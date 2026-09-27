CREATE SCHEMA IF NOT EXISTS analytics;


-- =====================================================================
-- HOSPITAL 360
-- PHASE 8.1 — PATIENT RISK INTELLIGENCE
--
-- IMPORTANT:
-- This is a transparent analytical/demo prioritization model.
-- It is NOT a validated clinical risk score and must not be used
-- for diagnosis, treatment, or real-world clinical decision-making.
-- =====================================================================


-- =====================================================================
-- 1. ADMISSION-LEVEL RISK
-- One row per admission.
--
-- Billing is pre-aggregated to admission grain before joining so the
-- admission fact grain remains protected.
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_admission_risk AS

WITH billing_by_admission AS (
    SELECT
        admission_key,

        ROUND(
            COALESCE(
                SUM(outstanding_amount),
                0
            )::numeric,
            2
        ) AS outstanding_amount

    FROM warehouse.fact_billing

    GROUP BY
        admission_key
),

risk_base AS (
    SELECT
        a.admission_key,
        a.admission_id,

        a.patient_key,
        p.patient_id,
        p.first_name,
        p.last_name,
        p.gender,
        p.date_of_birth,
        p.chronic_condition,

        a.doctor_key,
        d.doctor_id,
        d.doctor_name,

        a.department_key,
        dep.department_id,
        dep.department_name,

        a.diagnosis_key,
        dx.diagnosis_code,
        dx.diagnosis_name,
        dx.diagnosis_category,

        a.admission_date_key,
        a.discharge_date_key,

        a.admission_timestamp,
        a.discharge_timestamp,

        a.admission_type,
        a.room_type,
        a.length_of_stay,

        a.icu_flag,
        a.readmission_flag,
        a.emergency_flag,
        a.outcome,

        EXTRACT(
            YEAR
            FROM AGE(
                a.admission_timestamp::date,
                p.date_of_birth
            )
        )::integer AS age_at_admission,

        COALESCE(
            b.outstanding_amount,
            0
        ) AS outstanding_amount

    FROM warehouse.fact_admission a

    INNER JOIN warehouse.dim_patient p
        ON p.patient_key = a.patient_key

    INNER JOIN warehouse.dim_doctor d
        ON d.doctor_key = a.doctor_key

    INNER JOIN warehouse.dim_department dep
        ON dep.department_key = a.department_key

    INNER JOIN warehouse.dim_diagnosis dx
        ON dx.diagnosis_key = a.diagnosis_key

    LEFT JOIN billing_by_admission b
        ON b.admission_key = a.admission_key
),

risk_components AS (
    SELECT
        *,

        CASE
            WHEN readmission_flag
            THEN 25
            ELSE 0
        END AS readmission_risk_points,

        CASE
            WHEN age_at_admission > 70
            THEN 15
            ELSE 0
        END AS age_risk_points,

        CASE
            WHEN chronic_condition IS NOT NULL
             AND BTRIM(chronic_condition) <> ''
             AND LOWER(
                    BTRIM(chronic_condition)
                 ) NOT IN (
                    'none',
                    'no',
                    'n/a',
                    'na'
                 )
            THEN 15
            ELSE 0
        END AS chronic_condition_risk_points,

        CASE
            WHEN icu_flag
            THEN 20
            ELSE 0
        END AS icu_risk_points,

        CASE
            WHEN length_of_stay > 10
            THEN 10
            ELSE 0
        END AS long_stay_risk_points,

        CASE
            WHEN outstanding_amount > 0
            THEN 5
            ELSE 0
        END AS outstanding_risk_points,

        CASE
            WHEN emergency_flag
            THEN 10
            ELSE 0
        END AS emergency_risk_points

    FROM risk_base
),

scored AS (
    SELECT
        *,

        (
            readmission_risk_points
            + age_risk_points
            + chronic_condition_risk_points
            + icu_risk_points
            + long_stay_risk_points
            + outstanding_risk_points
            + emergency_risk_points
        )::integer AS risk_score

    FROM risk_components
)

SELECT
    *,

    CASE
        WHEN risk_score >= 60
            THEN 'High'

        WHEN risk_score >= 30
            THEN 'Medium'

        ELSE 'Low'
    END AS risk_band,

    CONCAT_WS(
        '; ',

        CASE
            WHEN readmission_risk_points > 0
            THEN 'Readmission'
        END,

        CASE
            WHEN age_risk_points > 0
            THEN 'Age > 70'
        END,

        CASE
            WHEN chronic_condition_risk_points > 0
            THEN 'Chronic condition'
        END,

        CASE
            WHEN icu_risk_points > 0
            THEN 'ICU admission'
        END,

        CASE
            WHEN long_stay_risk_points > 0
            THEN 'LOS > 10 days'
        END,

        CASE
            WHEN outstanding_risk_points > 0
            THEN 'Outstanding balance'
        END,

        CASE
            WHEN emergency_risk_points > 0
            THEN 'Emergency admission'
        END

    ) AS risk_reasons

FROM scored;


-- =====================================================================
-- 2. PATIENT-LEVEL RISK
--
-- Patient risk represents the highest observed admission risk score.
-- Latest admission risk is retained separately.
-- This avoids summing risk points across repeated admissions.
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_patient_risk AS

WITH ranked AS (
    SELECT
        r.*,

        ROW_NUMBER() OVER (
            PARTITION BY r.patient_key

            ORDER BY
                r.admission_timestamp DESC,
                r.admission_key DESC
        ) AS latest_row_number

    FROM analytics.vw_admission_risk r
),

patient_summary AS (
    SELECT
        patient_key,

        MAX(patient_id) AS patient_id,
        MAX(first_name) AS first_name,
        MAX(last_name) AS last_name,
        MAX(gender) AS gender,
        MAX(date_of_birth) AS date_of_birth,

        MAX(age_at_admission) AS maximum_observed_age,

        COUNT(*) AS lifetime_admissions,

        SUM(
            CASE
                WHEN readmission_flag
                THEN 1
                ELSE 0
            END
        ) AS readmission_admissions,

        SUM(
            CASE
                WHEN emergency_flag
                THEN 1
                ELSE 0
            END
        ) AS emergency_admissions,

        SUM(
            CASE
                WHEN icu_flag
                THEN 1
                ELSE 0
            END
        ) AS icu_admissions,

        MAX(length_of_stay) AS maximum_length_of_stay,

        ROUND(
            AVG(length_of_stay)::numeric,
            2
        ) AS average_length_of_stay,

        ROUND(
            SUM(outstanding_amount)::numeric,
            2
        ) AS lifetime_recorded_outstanding,

        MAX(risk_score) AS maximum_risk_score,

        COUNT(*) FILTER (
            WHERE risk_band = 'High'
        ) AS high_risk_admissions,

        COUNT(*) FILTER (
            WHERE risk_band = 'Medium'
        ) AS medium_risk_admissions,

        COUNT(*) FILTER (
            WHERE risk_band = 'Low'
        ) AS low_risk_admissions,

        MAX(admission_timestamp)
            AS latest_admission_timestamp

    FROM ranked

    GROUP BY
        patient_key
),

latest AS (
    SELECT
        patient_key,

        admission_id
            AS latest_admission_id,

        doctor_id
            AS latest_doctor_id,

        doctor_name
            AS latest_doctor_name,

        department_id
            AS latest_department_id,

        department_name
            AS latest_department_name,

        diagnosis_code
            AS latest_diagnosis_code,

        diagnosis_name
            AS latest_diagnosis_name,

        chronic_condition
            AS latest_chronic_condition,

        risk_score
            AS latest_risk_score,

        risk_band
            AS latest_risk_band,

        risk_reasons
            AS latest_risk_reasons

    FROM ranked

    WHERE latest_row_number = 1
)

SELECT
    p.*,

    CASE
        WHEN p.maximum_risk_score >= 60
            THEN 'High'

        WHEN p.maximum_risk_score >= 30
            THEN 'Medium'

        ELSE 'Low'
    END AS maximum_risk_band,

    l.latest_admission_id,
    l.latest_doctor_id,
    l.latest_doctor_name,
    l.latest_department_id,
    l.latest_department_name,
    l.latest_diagnosis_code,
    l.latest_diagnosis_name,
    l.latest_chronic_condition,
    l.latest_risk_score,
    l.latest_risk_band,
    l.latest_risk_reasons

FROM patient_summary p

INNER JOIN latest l
    ON l.patient_key = p.patient_key;


-- =====================================================================
-- 3. RISK BAND SUMMARY
-- Admission-level population.
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_risk_band_summary AS

SELECT
    risk_band,

    COUNT(*) AS admissions,

    COUNT(
        DISTINCT patient_key
    ) AS patients,

    ROUND(
        AVG(risk_score)::numeric,
        2
    ) AS average_risk_score,

    MIN(risk_score)
        AS minimum_risk_score,

    MAX(risk_score)
        AS maximum_risk_score,

    ROUND(
        100.0
        * COUNT(*)
        / NULLIF(
            SUM(COUNT(*)) OVER (),
            0
        ),
        2
    ) AS admission_share_pct,

    ROUND(
        AVG(length_of_stay)::numeric,
        2
    ) AS average_length_of_stay,

    ROUND(
        SUM(outstanding_amount)::numeric,
        2
    ) AS outstanding_amount

FROM analytics.vw_admission_risk

GROUP BY
    risk_band;


-- =====================================================================
-- 4. DEPARTMENT RISK
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_department_risk AS

WITH metrics AS (
    SELECT
        department_key,
        department_id,
        department_name,

        COUNT(*) AS admissions,

        COUNT(
            DISTINCT patient_key
        ) AS patients,

        ROUND(
            AVG(risk_score)::numeric,
            2
        ) AS average_risk_score,

        COUNT(*) FILTER (
            WHERE risk_band = 'High'
        ) AS high_risk_admissions,

        COUNT(*) FILTER (
            WHERE risk_band = 'Medium'
        ) AS medium_risk_admissions,

        COUNT(*) FILTER (
            WHERE risk_band = 'Low'
        ) AS low_risk_admissions,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE risk_band = 'High'
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS high_risk_admission_rate_pct,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE readmission_flag
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS readmission_rate_pct,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE emergency_flag
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS emergency_rate_pct,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE icu_flag
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS icu_rate_pct,

        ROUND(
            AVG(length_of_stay)::numeric,
            2
        ) AS average_length_of_stay,

        ROUND(
            SUM(outstanding_amount)::numeric,
            2
        ) AS outstanding_amount

    FROM analytics.vw_admission_risk

    GROUP BY
        department_key,
        department_id,
        department_name
)

SELECT
    *,

    DENSE_RANK() OVER (
        ORDER BY
            high_risk_admission_rate_pct DESC,
            average_risk_score DESC,
            department_name
    ) AS high_risk_rate_rank

FROM metrics;


-- =====================================================================
-- 5. DOCTOR RISK
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_doctor_risk AS

WITH metrics AS (
    SELECT
        doctor_key,
        doctor_id,
        doctor_name,

        department_key,
        department_id,
        department_name,

        COUNT(*) AS admissions,

        COUNT(
            DISTINCT patient_key
        ) AS patients,

        ROUND(
            AVG(risk_score)::numeric,
            2
        ) AS average_risk_score,

        COUNT(*) FILTER (
            WHERE risk_band = 'High'
        ) AS high_risk_admissions,

        COUNT(*) FILTER (
            WHERE risk_band = 'Medium'
        ) AS medium_risk_admissions,

        COUNT(*) FILTER (
            WHERE risk_band = 'Low'
        ) AS low_risk_admissions,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE risk_band = 'High'
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS high_risk_admission_rate_pct,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE readmission_flag
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS readmission_rate_pct,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE emergency_flag
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS emergency_rate_pct,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE icu_flag
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS icu_rate_pct,

        ROUND(
            AVG(length_of_stay)::numeric,
            2
        ) AS average_length_of_stay,

        ROUND(
            SUM(outstanding_amount)::numeric,
            2
        ) AS outstanding_amount

    FROM analytics.vw_admission_risk

    GROUP BY
        doctor_key,
        doctor_id,
        doctor_name,
        department_key,
        department_id,
        department_name
)

SELECT
    *,

    DENSE_RANK() OVER (
        PARTITION BY department_key

        ORDER BY
            high_risk_admission_rate_pct DESC,
            average_risk_score DESC,
            doctor_name
    ) AS department_risk_rank,

    DENSE_RANK() OVER (
        ORDER BY
            high_risk_admission_rate_pct DESC,
            average_risk_score DESC,
            doctor_name
    ) AS hospital_risk_rank

FROM metrics;


-- =====================================================================
-- 6. MONTHLY RISK TREND
-- Admission-month semantics.
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_risk_trend AS

WITH metrics AS (
    SELECT
        DATE_TRUNC(
            'month',
            admission_timestamp
        )::date AS month_start,

        COUNT(*) AS admissions,

        COUNT(
            DISTINCT patient_key
        ) AS patients,

        ROUND(
            AVG(risk_score)::numeric,
            2
        ) AS average_risk_score,

        COUNT(*) FILTER (
            WHERE risk_band = 'High'
        ) AS high_risk_admissions,

        COUNT(*) FILTER (
            WHERE risk_band = 'Medium'
        ) AS medium_risk_admissions,

        COUNT(*) FILTER (
            WHERE risk_band = 'Low'
        ) AS low_risk_admissions,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE risk_band = 'High'
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS high_risk_admission_rate_pct,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE readmission_flag
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS readmission_rate_pct,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE emergency_flag
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS emergency_rate_pct,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE icu_flag
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS icu_rate_pct

    FROM analytics.vw_admission_risk

    GROUP BY
        DATE_TRUNC(
            'month',
            admission_timestamp
        )::date
)

SELECT
    *,

    ROUND(
        (
            high_risk_admission_rate_pct
            - LAG(
                high_risk_admission_rate_pct
            ) OVER (
                ORDER BY month_start
            )
        )::numeric,
        2
    ) AS high_risk_rate_mom_change_pp,

    ROUND(
        (
            average_risk_score
            - LAG(
                average_risk_score
            ) OVER (
                ORDER BY month_start
            )
        )::numeric,
        2
    ) AS average_risk_score_mom_change

FROM metrics;


-- =====================================================================
-- 7. RISK FACTOR PREVALENCE
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_risk_factor_prevalence AS

WITH total AS (
    SELECT
        COUNT(*) AS total_admissions

    FROM analytics.vw_admission_risk
),

factors AS (
    SELECT
        'Readmission'::varchar
            AS risk_factor,

        COUNT(*) FILTER (
            WHERE readmission_risk_points > 0
        ) AS triggered_admissions

    FROM analytics.vw_admission_risk

    UNION ALL

    SELECT
        'Age > 70',
        COUNT(*) FILTER (
            WHERE age_risk_points > 0
        )

    FROM analytics.vw_admission_risk

    UNION ALL

    SELECT
        'Chronic condition',
        COUNT(*) FILTER (
            WHERE chronic_condition_risk_points > 0
        )

    FROM analytics.vw_admission_risk

    UNION ALL

    SELECT
        'ICU admission',
        COUNT(*) FILTER (
            WHERE icu_risk_points > 0
        )

    FROM analytics.vw_admission_risk

    UNION ALL

    SELECT
        'LOS > 10 days',
        COUNT(*) FILTER (
            WHERE long_stay_risk_points > 0
        )

    FROM analytics.vw_admission_risk

    UNION ALL

    SELECT
        'Outstanding balance',
        COUNT(*) FILTER (
            WHERE outstanding_risk_points > 0
        )

    FROM analytics.vw_admission_risk

    UNION ALL

    SELECT
        'Emergency admission',
        COUNT(*) FILTER (
            WHERE emergency_risk_points > 0
        )

    FROM analytics.vw_admission_risk
)

SELECT
    f.risk_factor,
    f.triggered_admissions,
    t.total_admissions,

    ROUND(
        100.0
        * f.triggered_admissions
        / NULLIF(
            t.total_admissions,
            0
        ),
        2
    ) AS prevalence_pct

FROM factors f

CROSS JOIN total t;