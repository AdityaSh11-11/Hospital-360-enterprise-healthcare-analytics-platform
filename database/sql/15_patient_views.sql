-- ============================================================
-- HOSPITAL 360
-- PHASE 5.3 — PATIENT ANALYTICS
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- 1. PATIENT DEMOGRAPHICS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_patient_demographics AS

WITH classified AS (

    SELECT
        patient_key,
        patient_id,
        gender,
        date_of_birth,

        EXTRACT(
            YEAR
            FROM AGE(
                CURRENT_DATE,
                date_of_birth
            )
        )::integer AS age,

        blood_group,
        city,
        state,
        insurance_status,
        chronic_condition,
        registration_date,
        is_active

    FROM warehouse.dim_patient
)

SELECT
    patient_key,
    patient_id,
    gender,
    date_of_birth,
    age,

    CASE
        WHEN age IS NULL THEN 'Unknown'
        WHEN age < 18 THEN '0-17'
        WHEN age <= 30 THEN '18-30'
        WHEN age <= 45 THEN '31-45'
        WHEN age <= 60 THEN '46-60'
        WHEN age <= 70 THEN '61-70'
        ELSE '71+'
    END AS age_band,

    CASE
        WHEN age IS NULL THEN 8
        WHEN age < 18 THEN 1
        WHEN age <= 30 THEN 2
        WHEN age <= 45 THEN 3
        WHEN age <= 60 THEN 4
        WHEN age <= 70 THEN 5
        ELSE 6
    END AS age_band_order,

    blood_group,
    city,
    state,
    insurance_status,
    chronic_condition,
    registration_date,
    is_active

FROM classified;


-- ============================================================
-- 2. AGE BAND ANALYSIS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_patient_age_analysis AS

SELECT
    age_band,
    age_band_order,

    COUNT(*) AS patients,

    COUNT(*) FILTER (
        WHERE is_active = TRUE
    ) AS active_patients,

    ROUND(
        AVG(age)::numeric,
        2
    ) AS average_age,

    ROUND(
        (
            100.0
            * COUNT(*)
            / NULLIF(
                SUM(COUNT(*)) OVER (),
                0
            )
        )::numeric,
        2
    ) AS patient_mix_pct

FROM analytics.vw_patient_demographics

GROUP BY
    age_band,
    age_band_order;


-- ============================================================
-- 3. GENDER ANALYSIS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_patient_gender_analysis AS

SELECT
    COALESCE(gender, 'Unknown') AS gender,

    COUNT(*) AS patients,

    COUNT(*) FILTER (
        WHERE is_active = TRUE
    ) AS active_patients,

    ROUND(
        (
            100.0
            * COUNT(*)
            / NULLIF(
                SUM(COUNT(*)) OVER (),
                0
            )
        )::numeric,
        2
    ) AS patient_mix_pct

FROM warehouse.dim_patient

GROUP BY
    COALESCE(gender, 'Unknown');


-- ============================================================
-- 4. INSURANCE STATUS ANALYSIS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_patient_insurance_analysis AS

SELECT
    COALESCE(
        insurance_status,
        'Unknown'
    ) AS insurance_status,

    COUNT(*) AS patients,

    COUNT(*) FILTER (
        WHERE is_active = TRUE
    ) AS active_patients,

    ROUND(
        (
            100.0
            * COUNT(*)
            / NULLIF(
                SUM(COUNT(*)) OVER (),
                0
            )
        )::numeric,
        2
    ) AS patient_mix_pct

FROM warehouse.dim_patient

GROUP BY
    COALESCE(
        insurance_status,
        'Unknown'
    );


-- ============================================================
-- 5. CHRONIC CONDITION ANALYSIS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_chronic_condition_analysis AS

WITH patient_admissions AS (

    SELECT
        patient_key,

        COUNT(*) AS admissions,

        COUNT(*) FILTER (
            WHERE emergency_flag = TRUE
        ) AS emergency_admissions,

        COUNT(*) FILTER (
            WHERE icu_flag = TRUE
        ) AS icu_admissions,

        COUNT(*) FILTER (
            WHERE readmission_flag = TRUE
        ) AS readmissions,

        ROUND(
            AVG(length_of_stay)::numeric,
            2
        ) AS average_length_of_stay

    FROM warehouse.fact_admission

    GROUP BY
        patient_key
)

SELECT
    COALESCE(
        p.chronic_condition,
        'Unknown'
    ) AS chronic_condition,

    COUNT(*) AS patients,

    COUNT(*) FILTER (
        WHERE p.is_active = TRUE
    ) AS active_patients,

    COALESCE(
        SUM(a.admissions),
        0
    ) AS admissions,

    COALESCE(
        SUM(a.emergency_admissions),
        0
    ) AS emergency_admissions,

    COALESCE(
        SUM(a.icu_admissions),
        0
    ) AS icu_admissions,

    COALESCE(
        SUM(a.readmissions),
        0
    ) AS readmissions,

    ROUND(
        AVG(a.average_length_of_stay)::numeric,
        2
    ) AS average_patient_alos

FROM warehouse.dim_patient p

LEFT JOIN patient_admissions a
    ON a.patient_key =
       p.patient_key

GROUP BY
    COALESCE(
        p.chronic_condition,
        'Unknown'
    );


-- ============================================================
-- 6. PATIENT GEOGRAPHY
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_patient_geography AS

SELECT
    COALESCE(state, 'Unknown') AS state,
    COALESCE(city, 'Unknown') AS city,

    COUNT(*) AS patients,

    COUNT(*) FILTER (
        WHERE is_active = TRUE
    ) AS active_patients,

    COUNT(*) FILTER (
        WHERE insurance_status IS NOT NULL
    ) AS patients_with_insurance_status,

    ROUND(
        (
            100.0
            * COUNT(*)
            / NULLIF(
                SUM(COUNT(*)) OVER (),
                0
            )
        )::numeric,
        2
    ) AS patient_mix_pct,

    DENSE_RANK() OVER (
        ORDER BY
            COUNT(*) DESC
    ) AS population_rank

FROM warehouse.dim_patient

GROUP BY
    COALESCE(state, 'Unknown'),
    COALESCE(city, 'Unknown');


-- ============================================================
-- 7. PATIENT UTILIZATION SEGMENTS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_patient_utilization_segments AS

WITH utilization AS (

    SELECT
        p.patient_key,
        p.patient_id,
        p.gender,
        p.date_of_birth,
        p.city,
        p.state,
        p.insurance_status,
        p.chronic_condition,

        COUNT(a.admission_key) AS lifetime_admissions,

        COALESCE(
            SUM(a.length_of_stay),
            0
        ) AS lifetime_inpatient_days,

        COUNT(a.admission_key) FILTER (
            WHERE a.emergency_flag = TRUE
        ) AS emergency_admissions,

        COUNT(a.admission_key) FILTER (
            WHERE a.icu_flag = TRUE
        ) AS icu_admissions,

        COUNT(a.admission_key) FILTER (
            WHERE a.readmission_flag = TRUE
        ) AS readmissions,

        MAX(
            a.admission_timestamp
        ) AS latest_admission_timestamp

    FROM warehouse.dim_patient p

    LEFT JOIN warehouse.fact_admission a
        ON a.patient_key =
           p.patient_key

    WHERE p.is_active = TRUE

    GROUP BY
        p.patient_key,
        p.patient_id,
        p.gender,
        p.date_of_birth,
        p.city,
        p.state,
        p.insurance_status,
        p.chronic_condition
)

SELECT
    *,

    CASE
        WHEN lifetime_admissions = 0
            THEN 'No Admission'

        WHEN lifetime_admissions = 1
            THEN 'Single Admission'

        WHEN lifetime_admissions BETWEEN 2 AND 3
            THEN '2-3 Admissions'

        WHEN lifetime_admissions BETWEEN 4 AND 5
            THEN '4-5 Admissions'

        ELSE '6+ Admissions'
    END AS utilization_segment,

    CASE
        WHEN lifetime_admissions = 0 THEN 1
        WHEN lifetime_admissions = 1 THEN 2
        WHEN lifetime_admissions BETWEEN 2 AND 3 THEN 3
        WHEN lifetime_admissions BETWEEN 4 AND 5 THEN 4
        ELSE 5
    END AS utilization_segment_order

FROM utilization;


-- ============================================================
-- 8. UTILIZATION SEGMENT SUMMARY
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_patient_utilization_segment_summary AS

SELECT
    utilization_segment,
    utilization_segment_order,

    COUNT(*) AS patients,

    SUM(lifetime_admissions) AS admissions,

    SUM(lifetime_inpatient_days) AS inpatient_days,

    SUM(emergency_admissions) AS emergency_admissions,

    SUM(icu_admissions) AS icu_admissions,

    SUM(readmissions) AS readmissions,

    ROUND(
        AVG(lifetime_admissions)::numeric,
        2
    ) AS average_admissions_per_patient,

    ROUND(
        (
            100.0
            * COUNT(*)
            / NULLIF(
                SUM(COUNT(*)) OVER (),
                0
            )
        )::numeric,
        2
    ) AS patient_mix_pct

FROM analytics.vw_patient_utilization_segments

GROUP BY
    utilization_segment,
    utilization_segment_order;


-- ============================================================
-- 9. HIGH UTILIZATION PATIENTS
-- Descriptive only — NOT a clinical risk score.
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_high_utilization_patients AS

SELECT
    u.patient_key,
    u.patient_id,
    u.gender,

    EXTRACT(
        YEAR
        FROM AGE(
            CURRENT_DATE,
            u.date_of_birth
        )
    )::integer AS age,

    u.city,
    u.state,
    u.insurance_status,
    u.chronic_condition,
    u.lifetime_admissions,
    u.lifetime_inpatient_days,
    u.emergency_admissions,
    u.icu_admissions,
    u.readmissions,
    u.latest_admission_timestamp,
    u.utilization_segment,

    DENSE_RANK() OVER (
        ORDER BY
            u.lifetime_admissions DESC,
            u.lifetime_inpatient_days DESC
    ) AS utilization_rank

FROM analytics.vw_patient_utilization_segments u

WHERE u.lifetime_admissions >= 4;


-- ============================================================
-- 10. MONTHLY PATIENT ADMISSION COHORT
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_patient_admission_cohort AS

WITH first_admission AS (

    SELECT
        patient_key,

        MIN(
            admission_timestamp::date
        ) AS first_admission_date

    FROM warehouse.fact_admission

    GROUP BY
        patient_key
),

cohorts AS (

    SELECT
        DATE_TRUNC(
            'month',
            first_admission_date
        )::date AS cohort_month,

        COUNT(*) AS first_time_admitted_patients

    FROM first_admission

    GROUP BY
        DATE_TRUNC(
            'month',
            first_admission_date
        )::date
)

SELECT
    cohort_month,
    first_time_admitted_patients,

    SUM(
        first_time_admitted_patients
    ) OVER (
        ORDER BY cohort_month
        ROWS BETWEEN
            UNBOUNDED PRECEDING
            AND CURRENT ROW
    ) AS cumulative_admitted_patients,

    LAG(
        first_time_admitted_patients
    ) OVER (
        ORDER BY cohort_month
    ) AS previous_month_first_time_patients,

    ROUND(
        (
            100.0
            * (
                first_time_admitted_patients
                - LAG(
                    first_time_admitted_patients
                ) OVER (
                    ORDER BY cohort_month
                )
            )
            / NULLIF(
                LAG(
                    first_time_admitted_patients
                ) OVER (
                    ORDER BY cohort_month
                ),
                0
            )
        )::numeric,
        2
    ) AS first_time_patient_mom_growth_pct

FROM cohorts;


-- ============================================================
-- DOCUMENTATION
-- ============================================================

COMMENT ON VIEW analytics.vw_patient_demographics IS
'Patient demographic semantic layer with derived age and age bands.';

COMMENT ON VIEW analytics.vw_patient_age_analysis IS
'Patient population summarized by age band.';

COMMENT ON VIEW analytics.vw_patient_gender_analysis IS
'Patient population summarized by recorded gender.';

COMMENT ON VIEW analytics.vw_patient_insurance_analysis IS
'Patient population summarized by insurance status.';

COMMENT ON VIEW analytics.vw_chronic_condition_analysis IS
'Patient and admission utilization summarized by chronic condition.';

COMMENT ON VIEW analytics.vw_patient_geography IS
'Patient population summarized by state and city.';

COMMENT ON VIEW analytics.vw_patient_utilization_segments IS
'Patient-level descriptive utilization segmentation based on admission frequency.';

COMMENT ON VIEW analytics.vw_patient_utilization_segment_summary IS
'Summary of descriptive patient utilization segments.';

COMMENT ON VIEW analytics.vw_high_utilization_patients IS
'Descriptive high-utilization patient view; not a clinical risk model.';

COMMENT ON VIEW analytics.vw_monthly_patient_admission_cohort IS
'Monthly cohort of patients based on their first recorded hospital admission.';