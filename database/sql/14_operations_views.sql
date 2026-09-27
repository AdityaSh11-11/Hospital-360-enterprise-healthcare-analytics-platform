-- ============================================================
-- HOSPITAL 360
-- PHASE 5.3 — OPERATIONS ANALYTICS
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- 1. OPERATIONS SUMMARY
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_operations_summary AS

SELECT
    COUNT(*) AS total_admissions,

    COUNT(DISTINCT patient_key) AS admitted_patients,

    ROUND(
        AVG(length_of_stay)::numeric,
        2
    ) AS average_length_of_stay,

    SUM(length_of_stay) AS total_inpatient_days,

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
        (
            100.0
            * COUNT(*) FILTER (
                WHERE emergency_flag = TRUE
            )
            / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS emergency_rate_pct,

    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE icu_flag = TRUE
            )
            / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS icu_rate_pct,

    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE readmission_flag = TRUE
            )
            / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS readmission_rate_pct

FROM warehouse.fact_admission;


-- ============================================================
-- 2. ADMISSION TYPE ANALYSIS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_admission_type_analysis AS

SELECT
    COALESCE(admission_type, 'Unknown') AS admission_type,

    COUNT(*) AS admissions,

    COUNT(DISTINCT patient_key) AS patients,

    ROUND(
        AVG(length_of_stay)::numeric,
        2
    ) AS average_length_of_stay,

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
        (
            100.0
            * COUNT(*) FILTER (
                WHERE readmission_flag = TRUE
            )
            / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS readmission_rate_pct,

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
    ) AS admission_mix_pct

FROM warehouse.fact_admission

GROUP BY
    COALESCE(admission_type, 'Unknown');


-- ============================================================
-- 3. ROOM TYPE ANALYSIS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_room_type_analysis AS

SELECT
    COALESCE(room_type, 'Unknown') AS room_type,

    COUNT(*) AS admissions,

    COUNT(DISTINCT patient_key) AS patients,

    ROUND(
        AVG(length_of_stay)::numeric,
        2
    ) AS average_length_of_stay,

    SUM(length_of_stay) AS total_inpatient_days,

    COUNT(*) FILTER (
        WHERE icu_flag = TRUE
    ) AS icu_admissions,

    COUNT(*) FILTER (
        WHERE readmission_flag = TRUE
    ) AS readmissions,

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
    ) AS admission_mix_pct

FROM warehouse.fact_admission

GROUP BY
    COALESCE(room_type, 'Unknown');


-- ============================================================
-- 4. LENGTH OF STAY BANDS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_length_of_stay_bands AS

WITH classified AS (

    SELECT
        CASE
            WHEN length_of_stay IS NULL
                THEN 'Unknown'

            WHEN length_of_stay <= 1
                THEN '0-1 Days'

            WHEN length_of_stay <= 3
                THEN '2-3 Days'

            WHEN length_of_stay <= 7
                THEN '4-7 Days'

            WHEN length_of_stay <= 14
                THEN '8-14 Days'

            ELSE '15+ Days'
        END AS los_band,

        CASE
            WHEN length_of_stay IS NULL THEN 6
            WHEN length_of_stay <= 1 THEN 1
            WHEN length_of_stay <= 3 THEN 2
            WHEN length_of_stay <= 7 THEN 3
            WHEN length_of_stay <= 14 THEN 4
            ELSE 5
        END AS band_order,

        patient_key,
        length_of_stay,
        emergency_flag,
        icu_flag,
        readmission_flag

    FROM warehouse.fact_admission
)

SELECT
    los_band,
    band_order,

    COUNT(*) AS admissions,

    COUNT(DISTINCT patient_key) AS patients,

    ROUND(
        AVG(length_of_stay)::numeric,
        2
    ) AS average_length_of_stay,

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
        (
            100.0
            * COUNT(*)
            / NULLIF(
                SUM(COUNT(*)) OVER (),
                0
            )
        )::numeric,
        2
    ) AS admission_mix_pct

FROM classified

GROUP BY
    los_band,
    band_order;


-- ============================================================
-- 5. OUTCOME ANALYSIS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_outcome_analysis AS

SELECT
    COALESCE(outcome, 'Unknown') AS outcome,

    COUNT(*) AS admissions,

    COUNT(DISTINCT patient_key) AS patients,

    ROUND(
        AVG(length_of_stay)::numeric,
        2
    ) AS average_length_of_stay,

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
        (
            100.0
            * COUNT(*)
            / NULLIF(
                SUM(COUNT(*)) OVER (),
                0
            )
        )::numeric,
        2
    ) AS outcome_mix_pct

FROM warehouse.fact_admission

GROUP BY
    COALESCE(outcome, 'Unknown');


-- ============================================================
-- 6. DEPARTMENT OPERATIONS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_department_operations AS

SELECT
    d.department_key,
    d.department_id,
    d.department_name,
    d.department_type,
    d.floor_number,
    d.bed_capacity,

    COUNT(a.admission_key) AS admissions,

    COUNT(
        DISTINCT a.patient_key
    ) AS patients,

    ROUND(
        AVG(a.length_of_stay)::numeric,
        2
    ) AS average_length_of_stay,

    COALESCE(
        SUM(a.length_of_stay),
        0
    ) AS total_inpatient_days,

    COUNT(a.admission_key) FILTER (
        WHERE a.emergency_flag = TRUE
    ) AS emergency_admissions,

    COUNT(a.admission_key) FILTER (
        WHERE a.icu_flag = TRUE
    ) AS icu_admissions,

    COUNT(a.admission_key) FILTER (
        WHERE a.readmission_flag = TRUE
    ) AS readmissions,

    ROUND(
        (
            100.0
            * COUNT(a.admission_key) FILTER (
                WHERE a.readmission_flag = TRUE
            )
            / NULLIF(
                COUNT(a.admission_key),
                0
            )
        )::numeric,
        2
    ) AS readmission_rate_pct,

    ROUND(
        (
            COUNT(a.admission_key)::numeric
            / NULLIF(d.bed_capacity, 0)
        ),
        2
    ) AS admissions_per_bed,

    ROUND(
        (
            COALESCE(
                SUM(a.length_of_stay),
                0
            )::numeric
            / NULLIF(d.bed_capacity, 0)
        ),
        2
    ) AS inpatient_days_per_bed,

    DENSE_RANK() OVER (
        ORDER BY
            COUNT(a.admission_key) DESC
    ) AS admission_volume_rank

FROM warehouse.dim_department d

LEFT JOIN warehouse.fact_admission a
    ON a.department_key =
       d.department_key

GROUP BY
    d.department_key,
    d.department_id,
    d.department_name,
    d.department_type,
    d.floor_number,
    d.bed_capacity;


-- ============================================================
-- 7. DOCTOR WORKLOAD
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_doctor_workload AS

SELECT
    d.doctor_key,
    d.doctor_id,
    d.doctor_name,
    d.specialization,
    d.department_key,
    dep.department_name,
    d.experience_years,
    d.employment_status,

    COUNT(a.admission_key) AS admissions,

    COUNT(
        DISTINCT a.patient_key
    ) AS patients,

    ROUND(
        AVG(a.length_of_stay)::numeric,
        2
    ) AS average_length_of_stay,

    COALESCE(
        SUM(a.length_of_stay),
        0
    ) AS total_inpatient_days,

    COUNT(a.admission_key) FILTER (
        WHERE a.emergency_flag = TRUE
    ) AS emergency_admissions,

    COUNT(a.admission_key) FILTER (
        WHERE a.icu_flag = TRUE
    ) AS icu_admissions,

    COUNT(a.admission_key) FILTER (
        WHERE a.readmission_flag = TRUE
    ) AS readmissions,

    ROUND(
        (
            100.0
            * COUNT(a.admission_key) FILTER (
                WHERE a.readmission_flag = TRUE
            )
            / NULLIF(
                COUNT(a.admission_key),
                0
            )
        )::numeric,
        2
    ) AS readmission_rate_pct,

    DENSE_RANK() OVER (
        ORDER BY
            COUNT(a.admission_key) DESC
    ) AS hospital_workload_rank,

    DENSE_RANK() OVER (
        PARTITION BY d.department_key
        ORDER BY
            COUNT(a.admission_key) DESC
    ) AS department_workload_rank

FROM warehouse.dim_doctor d

LEFT JOIN warehouse.dim_department dep
    ON dep.department_key =
       d.department_key

LEFT JOIN warehouse.fact_admission a
    ON a.doctor_key =
       d.doctor_key

GROUP BY
    d.doctor_key,
    d.doctor_id,
    d.doctor_name,
    d.specialization,
    d.department_key,
    dep.department_name,
    d.experience_years,
    d.employment_status;


-- ============================================================
-- 8. DAY OF WEEK OPERATIONS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_day_of_week_operations AS

SELECT
    EXTRACT(
        ISODOW
        FROM d.full_date
    )::integer AS day_number,

    d.day_name,

    COUNT(*) AS admissions,

    COUNT(
        DISTINCT a.patient_key
    ) AS patients,

    ROUND(
        AVG(a.length_of_stay)::numeric,
        2
    ) AS average_length_of_stay,

    COUNT(*) FILTER (
        WHERE a.emergency_flag = TRUE
    ) AS emergency_admissions,

    COUNT(*) FILTER (
        WHERE a.icu_flag = TRUE
    ) AS icu_admissions,

    COUNT(*) FILTER (
        WHERE a.readmission_flag = TRUE
    ) AS readmissions,

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
    ) AS admission_mix_pct

FROM warehouse.fact_admission a

INNER JOIN warehouse.dim_date d
    ON d.date_key =
       a.admission_date_key

GROUP BY
    EXTRACT(
        ISODOW
        FROM d.full_date
    )::integer,
    d.day_name;


-- ============================================================
-- 9. MONTHLY OPERATIONS TREND
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_operations_trend AS

WITH monthly AS (

    SELECT
        DATE_TRUNC(
            'month',
            d.full_date
        )::date AS month_start,

        COUNT(*) AS admissions,

        COUNT(
            DISTINCT a.patient_key
        ) AS patients,

        ROUND(
            AVG(a.length_of_stay)::numeric,
            2
        ) AS average_length_of_stay,

        SUM(
            a.length_of_stay
        ) AS total_inpatient_days,

        COUNT(*) FILTER (
            WHERE a.emergency_flag = TRUE
        ) AS emergency_admissions,

        COUNT(*) FILTER (
            WHERE a.icu_flag = TRUE
        ) AS icu_admissions,

        COUNT(*) FILTER (
            WHERE a.readmission_flag = TRUE
        ) AS readmissions

    FROM warehouse.fact_admission a

    INNER JOIN warehouse.dim_date d
        ON d.date_key =
           a.admission_date_key

    GROUP BY
        DATE_TRUNC(
            'month',
            d.full_date
        )::date
),

windowed AS (

    SELECT
        *,

        LAG(admissions) OVER (
            ORDER BY month_start
        ) AS previous_month_admissions,

        AVG(admissions) OVER (
            ORDER BY month_start
            ROWS BETWEEN
                2 PRECEDING
                AND CURRENT ROW
        ) AS rolling_3_month_admissions

    FROM monthly
)

SELECT
    month_start,
    admissions,
    patients,
    average_length_of_stay,
    total_inpatient_days,
    emergency_admissions,
    icu_admissions,
    readmissions,

    ROUND(
        (
            100.0
            * readmissions
            / NULLIF(admissions, 0)
        )::numeric,
        2
    ) AS readmission_rate_pct,

    previous_month_admissions,

    ROUND(
        (
            100.0
            * (
                admissions
                - previous_month_admissions
            )
            / NULLIF(
                previous_month_admissions,
                0
            )
        )::numeric,
        2
    ) AS admission_mom_growth_pct,

    ROUND(
        rolling_3_month_admissions::numeric,
        2
    ) AS rolling_3_month_admissions

FROM windowed;


-- ============================================================
-- DOCUMENTATION
-- ============================================================

COMMENT ON VIEW analytics.vw_operations_summary IS
'Enterprise operational KPI summary based on hospital admissions.';

COMMENT ON VIEW analytics.vw_admission_type_analysis IS
'Admission volume and utilization summarized by admission type.';

COMMENT ON VIEW analytics.vw_room_type_analysis IS
'Admission and inpatient-day utilization summarized by room type.';

COMMENT ON VIEW analytics.vw_length_of_stay_bands IS
'Admissions segmented into descriptive length-of-stay bands.';

COMMENT ON VIEW analytics.vw_outcome_analysis IS
'Admission utilization summarized by recorded outcome.';

COMMENT ON VIEW analytics.vw_department_operations IS
'Department workload, inpatient days and descriptive utilization metrics.';

COMMENT ON VIEW analytics.vw_doctor_workload IS
'Doctor admission workload and descriptive utilization metrics.';

COMMENT ON VIEW analytics.vw_day_of_week_operations IS
'Admission workload summarized by day of week.';

COMMENT ON VIEW analytics.vw_monthly_operations_trend IS
'Monthly operational trend with growth and rolling admission metrics.';