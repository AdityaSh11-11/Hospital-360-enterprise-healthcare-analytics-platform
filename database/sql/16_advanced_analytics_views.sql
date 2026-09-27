-- ============================================================
-- HOSPITAL 360
-- PHASE 5.4 — ADVANCED ANALYTICS SEMANTIC LAYER
-- ============================================================
--
-- Purpose:
--   Diagnosis analytics
--   Service-line analytics
--   Monthly diagnosis trends
--   Hospital trend comparison
--   Department trend comparison
--   Doctor/department benchmarking
--
-- IMPORTANT:
--   These views are descriptive / analytical.
--   They are NOT clinical decision-support models.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- 1. DIAGNOSIS PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_diagnosis_performance AS

WITH admission_metrics AS (

    SELECT
        diagnosis_key,

        COUNT(*) AS admissions,

        COUNT(
            DISTINCT patient_key
        ) AS patients,

        ROUND(
            AVG(length_of_stay)::numeric,
            2
        ) AS average_length_of_stay,

        SUM(
            length_of_stay
        ) AS total_inpatient_days,

        COUNT(*) FILTER (
            WHERE emergency_flag = TRUE
        ) AS emergency_admissions,

        COUNT(*) FILTER (
            WHERE icu_flag = TRUE
        ) AS icu_admissions,

        COUNT(*) FILTER (
            WHERE readmission_flag = TRUE
        ) AS readmissions

    FROM warehouse.fact_admission

    GROUP BY
        diagnosis_key
),

finance_metrics AS (

    SELECT
        a.diagnosis_key,

        ROUND(
            SUM(b.gross_amount)::numeric,
            2
        ) AS gross_revenue,

        ROUND(
            SUM(b.net_amount)::numeric,
            2
        ) AS net_revenue,

        ROUND(
            SUM(b.paid_amount)::numeric,
            2
        ) AS collected_amount,

        ROUND(
            SUM(b.outstanding_amount)::numeric,
            2
        ) AS outstanding_amount

    FROM warehouse.fact_billing b

    INNER JOIN warehouse.fact_admission a
        ON a.admission_key =
           b.admission_key

    GROUP BY
        a.diagnosis_key
),

combined AS (

    SELECT
        d.diagnosis_key,
        d.diagnosis_code,
        d.diagnosis_name,
        d.diagnosis_category,
        d.chronic_flag,

        COALESCE(
            a.admissions,
            0
        ) AS admissions,

        COALESCE(
            a.patients,
            0
        ) AS patients,

        COALESCE(
            a.average_length_of_stay,
            0
        ) AS average_length_of_stay,

        COALESCE(
            a.total_inpatient_days,
            0
        ) AS total_inpatient_days,

        COALESCE(
            a.emergency_admissions,
            0
        ) AS emergency_admissions,

        COALESCE(
            a.icu_admissions,
            0
        ) AS icu_admissions,

        COALESCE(
            a.readmissions,
            0
        ) AS readmissions,

        COALESCE(
            f.gross_revenue,
            0
        ) AS gross_revenue,

        COALESCE(
            f.net_revenue,
            0
        ) AS net_revenue,

        COALESCE(
            f.collected_amount,
            0
        ) AS collected_amount,

        COALESCE(
            f.outstanding_amount,
            0
        ) AS outstanding_amount

    FROM warehouse.dim_diagnosis d

    LEFT JOIN admission_metrics a
        ON a.diagnosis_key =
           d.diagnosis_key

    LEFT JOIN finance_metrics f
        ON f.diagnosis_key =
           d.diagnosis_key
),

metrics AS (

    SELECT
        diagnosis_key,
        diagnosis_code,
        diagnosis_name,
        diagnosis_category,
        chronic_flag,

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
                / NULLIF(
                    admissions,
                    0
                )
            )::numeric,
            2
        ) AS readmission_rate_pct,

        gross_revenue,
        net_revenue,
        collected_amount,
        outstanding_amount,

        ROUND(
            (
                net_revenue
                / NULLIF(
                    admissions,
                    0
                )
            )::numeric,
            2
        ) AS revenue_per_admission,

        ROUND(
            (
                100.0
                * collected_amount
                / NULLIF(
                    net_revenue,
                    0
                )
            )::numeric,
            2
        ) AS collection_efficiency_pct

    FROM combined
)

SELECT
    diagnosis_key,
    diagnosis_code,
    diagnosis_name,
    diagnosis_category,
    chronic_flag,

    admissions,
    patients,
    average_length_of_stay,
    total_inpatient_days,
    emergency_admissions,
    icu_admissions,
    readmissions,
    readmission_rate_pct,

    gross_revenue,
    net_revenue,
    collected_amount,
    outstanding_amount,
    revenue_per_admission,
    collection_efficiency_pct,

    DENSE_RANK() OVER (
        ORDER BY
            admissions DESC
    ) AS admission_volume_rank,

    DENSE_RANK() OVER (
        ORDER BY
            net_revenue DESC
    ) AS revenue_rank,

    DENSE_RANK() OVER (
        ORDER BY
            readmission_rate_pct DESC NULLS LAST
    ) AS readmission_rate_rank

FROM metrics;


-- ============================================================
-- 2. DIAGNOSIS CATEGORY / SERVICE-LINE PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_diagnosis_category_performance AS

WITH category_metrics AS (

    SELECT
        COALESCE(
            diagnosis_category,
            'Unknown'
        ) AS diagnosis_category,

        COUNT(*) AS diagnosis_count,

        SUM(admissions) AS admissions,

        SUM(patients) AS diagnosis_patient_occurrences,

        ROUND(
            (
                SUM(
                    average_length_of_stay
                    * admissions
                )
                / NULLIF(
                    SUM(admissions),
                    0
                )
            )::numeric,
            2
        ) AS weighted_average_length_of_stay,

        SUM(
            total_inpatient_days
        ) AS total_inpatient_days,

        SUM(
            emergency_admissions
        ) AS emergency_admissions,

        SUM(
            icu_admissions
        ) AS icu_admissions,

        SUM(
            readmissions
        ) AS readmissions,

        ROUND(
            (
                100.0
                * SUM(readmissions)
                / NULLIF(
                    SUM(admissions),
                    0
                )
            )::numeric,
            2
        ) AS readmission_rate_pct,

        ROUND(
            SUM(gross_revenue)::numeric,
            2
        ) AS gross_revenue,

        ROUND(
            SUM(net_revenue)::numeric,
            2
        ) AS net_revenue,

        ROUND(
            SUM(collected_amount)::numeric,
            2
        ) AS collected_amount,

        ROUND(
            SUM(outstanding_amount)::numeric,
            2
        ) AS outstanding_amount,

        ROUND(
            (
                SUM(net_revenue)
                / NULLIF(
                    SUM(admissions),
                    0
                )
            )::numeric,
            2
        ) AS revenue_per_admission

    FROM analytics.vw_diagnosis_performance

    GROUP BY
        COALESCE(
            diagnosis_category,
            'Unknown'
        )
)

SELECT
    diagnosis_category,
    diagnosis_count,
    admissions,
    diagnosis_patient_occurrences,
    weighted_average_length_of_stay,
    total_inpatient_days,
    emergency_admissions,
    icu_admissions,
    readmissions,
    readmission_rate_pct,
    gross_revenue,
    net_revenue,
    collected_amount,
    outstanding_amount,
    revenue_per_admission,

    DENSE_RANK() OVER (
        ORDER BY
            admissions DESC
    ) AS admission_volume_rank,

    DENSE_RANK() OVER (
        ORDER BY
            net_revenue DESC
    ) AS revenue_rank

FROM category_metrics;


-- ============================================================
-- 3. MONTHLY DIAGNOSIS TREND
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_diagnosis_trend AS

WITH monthly AS (

    SELECT
        DATE_TRUNC(
            'month',
            dt.full_date
        )::date AS month_start,

        a.diagnosis_key,

        COUNT(*) AS admissions,

        COUNT(
            DISTINCT a.patient_key
        ) AS patients,

        ROUND(
            AVG(a.length_of_stay)::numeric,
            2
        ) AS average_length_of_stay,

        COUNT(*) FILTER (
            WHERE a.readmission_flag = TRUE
        ) AS readmissions

    FROM warehouse.fact_admission a

    INNER JOIN warehouse.dim_date dt
        ON dt.date_key =
           a.admission_date_key

    GROUP BY
        DATE_TRUNC(
            'month',
            dt.full_date
        )::date,
        a.diagnosis_key
),

windowed AS (

    SELECT
        *,

        LAG(admissions) OVER (
            PARTITION BY diagnosis_key
            ORDER BY month_start
        ) AS previous_month_admissions,

        AVG(admissions) OVER (
            PARTITION BY diagnosis_key
            ORDER BY month_start
            ROWS BETWEEN
                2 PRECEDING
                AND CURRENT ROW
        ) AS rolling_3_month_admissions

    FROM monthly
)

SELECT
    w.month_start,

    d.diagnosis_key,
    d.diagnosis_code,
    d.diagnosis_name,
    d.diagnosis_category,
    d.chronic_flag,

    w.admissions,
    w.patients,
    w.average_length_of_stay,
    w.readmissions,

    ROUND(
        (
            100.0
            * w.readmissions
            / NULLIF(
                w.admissions,
                0
            )
        )::numeric,
        2
    ) AS readmission_rate_pct,

    w.previous_month_admissions,

    ROUND(
        (
            100.0
            * (
                w.admissions
                - w.previous_month_admissions
            )
            / NULLIF(
                w.previous_month_admissions,
                0
            )
        )::numeric,
        2
    ) AS admission_mom_growth_pct,

    ROUND(
        w.rolling_3_month_admissions::numeric,
        2
    ) AS rolling_3_month_admissions,

    DENSE_RANK() OVER (
        PARTITION BY w.month_start
        ORDER BY
            w.admissions DESC
    ) AS monthly_diagnosis_rank

FROM windowed w

INNER JOIN warehouse.dim_diagnosis d
    ON d.diagnosis_key =
       w.diagnosis_key;


-- ============================================================
-- 4. HOSPITAL MONTHLY COMPARISON
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_hospital_monthly_comparison AS

WITH monthly AS (

    SELECT
        month_start,
        admissions,
        unique_patients,
        average_length_of_stay,
        emergency_admissions,
        icu_admissions,
        readmissions,
        readmission_rate_pct,
        gross_revenue,
        net_revenue,
        collected_amount,
        outstanding_amount,
        collection_efficiency_pct

    FROM analytics.vw_monthly_hospital_performance

    WHERE admissions > 0
),

comparison AS (

    SELECT
        *,

        LAG(admissions) OVER (
            ORDER BY month_start
        ) AS previous_month_admissions,

        LAG(net_revenue) OVER (
            ORDER BY month_start
        ) AS previous_month_net_revenue,

        LAG(readmission_rate_pct) OVER (
            ORDER BY month_start
        ) AS previous_month_readmission_rate,

        LAG(
            collection_efficiency_pct
        ) OVER (
            ORDER BY month_start
        ) AS previous_month_collection_efficiency,

        AVG(admissions) OVER (
            ORDER BY month_start
            ROWS BETWEEN
                2 PRECEDING
                AND CURRENT ROW
        ) AS rolling_3_month_admissions,

        AVG(net_revenue) OVER (
            ORDER BY month_start
            ROWS BETWEEN
                2 PRECEDING
                AND CURRENT ROW
        ) AS rolling_3_month_revenue

    FROM monthly
)

SELECT
    month_start,

    admissions,
    unique_patients,
    average_length_of_stay,
    emergency_admissions,
    icu_admissions,
    readmissions,
    readmission_rate_pct,

    gross_revenue,
    net_revenue,
    collected_amount,
    outstanding_amount,
    collection_efficiency_pct,

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

    previous_month_net_revenue,

    ROUND(
        (
            100.0
            * (
                net_revenue
                - previous_month_net_revenue
            )
            / NULLIF(
                previous_month_net_revenue,
                0
            )
        )::numeric,
        2
    ) AS revenue_mom_growth_pct,

    previous_month_readmission_rate,

    ROUND(
        (
            readmission_rate_pct
            - previous_month_readmission_rate
        )::numeric,
        2
    ) AS readmission_rate_change_pp,

    previous_month_collection_efficiency,

    ROUND(
        (
            collection_efficiency_pct
            - previous_month_collection_efficiency
        )::numeric,
        2
    ) AS collection_efficiency_change_pp,

    ROUND(
        rolling_3_month_admissions::numeric,
        2
    ) AS rolling_3_month_admissions,

    ROUND(
        rolling_3_month_revenue::numeric,
        2
    ) AS rolling_3_month_revenue

FROM comparison;


-- ============================================================
-- 5. DEPARTMENT MONTHLY BENCHMARK
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_department_monthly_benchmark AS

WITH base AS (

    SELECT
        month_start,
        department_key,
        department_id,
        department_name,
        admissions,
        unique_patients,
        average_length_of_stay,
        readmissions,
        readmission_rate_pct,
        net_revenue,
        collected_amount,
        outstanding_amount,
        revenue_per_admission

    FROM analytics.vw_monthly_department_performance
),

benchmarked AS (

    SELECT
        *,

        AVG(admissions) OVER (
            PARTITION BY month_start
        ) AS hospital_department_avg_admissions,

        AVG(
            average_length_of_stay
        ) OVER (
            PARTITION BY month_start
        ) AS hospital_department_avg_alos,

        AVG(
            readmission_rate_pct
        ) OVER (
            PARTITION BY month_start
        ) AS hospital_department_avg_readmission_rate,

        AVG(net_revenue) OVER (
            PARTITION BY month_start
        ) AS hospital_department_avg_revenue,

        AVG(
            revenue_per_admission
        ) OVER (
            PARTITION BY month_start
        ) AS hospital_department_avg_revenue_per_admission,

        DENSE_RANK() OVER (
            PARTITION BY month_start
            ORDER BY admissions DESC
        ) AS admission_volume_rank,

        DENSE_RANK() OVER (
            PARTITION BY month_start
            ORDER BY net_revenue DESC
        ) AS revenue_rank

    FROM base
)

SELECT
    month_start,
    department_key,
    department_id,
    department_name,

    admissions,
    unique_patients,
    average_length_of_stay,
    readmissions,
    readmission_rate_pct,

    net_revenue,
    collected_amount,
    outstanding_amount,
    revenue_per_admission,

    ROUND(
        hospital_department_avg_admissions::numeric,
        2
    ) AS hospital_department_avg_admissions,

    ROUND(
        (
            admissions
            - hospital_department_avg_admissions
        )::numeric,
        2
    ) AS admissions_vs_department_avg,

    ROUND(
        hospital_department_avg_alos::numeric,
        2
    ) AS hospital_department_avg_alos,

    ROUND(
        (
            average_length_of_stay
            - hospital_department_avg_alos
        )::numeric,
        2
    ) AS alos_vs_department_avg,

    ROUND(
        hospital_department_avg_readmission_rate::numeric,
        2
    ) AS hospital_department_avg_readmission_rate,

    ROUND(
        (
            readmission_rate_pct
            - hospital_department_avg_readmission_rate
        )::numeric,
        2
    ) AS readmission_rate_vs_department_avg_pp,

    ROUND(
        hospital_department_avg_revenue::numeric,
        2
    ) AS hospital_department_avg_revenue,

    ROUND(
        (
            net_revenue
            - hospital_department_avg_revenue
        )::numeric,
        2
    ) AS revenue_vs_department_avg,

    ROUND(
        hospital_department_avg_revenue_per_admission::numeric,
        2
    ) AS hospital_department_avg_revenue_per_admission,

    ROUND(
        (
            revenue_per_admission
            - hospital_department_avg_revenue_per_admission
        )::numeric,
        2
    ) AS revenue_per_admission_vs_avg,

    admission_volume_rank,
    revenue_rank

FROM benchmarked;


-- ============================================================
-- 6. DOCTOR DEPARTMENT BENCHMARK
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_doctor_department_benchmark AS

WITH base AS (

    SELECT
        doctor_key,
        doctor_id,
        doctor_name,
        specialization,
        department_key,
        department_name,
        admissions,
        unique_patients,
        average_length_of_stay,
        readmissions,
        readmission_rate_pct,
        net_revenue,
        collected_amount,
        outstanding_amount,
        revenue_per_admission

    FROM analytics.vw_doctor_performance
),

benchmarked AS (

    SELECT
        *,

        AVG(admissions) OVER (
            PARTITION BY department_key
        ) AS department_avg_admissions,

        AVG(
            average_length_of_stay
        ) OVER (
            PARTITION BY department_key
        ) AS department_avg_alos,

        AVG(
            readmission_rate_pct
        ) OVER (
            PARTITION BY department_key
        ) AS department_avg_readmission_rate,

        AVG(net_revenue) OVER (
            PARTITION BY department_key
        ) AS department_avg_revenue,

        AVG(
            revenue_per_admission
        ) OVER (
            PARTITION BY department_key
        ) AS department_avg_revenue_per_admission,

        DENSE_RANK() OVER (
            PARTITION BY department_key
            ORDER BY admissions DESC
        ) AS department_admission_rank,

        DENSE_RANK() OVER (
            PARTITION BY department_key
            ORDER BY net_revenue DESC
        ) AS department_revenue_rank

    FROM base
)

SELECT
    doctor_key,
    doctor_id,
    doctor_name,
    specialization,
    department_key,
    department_name,

    admissions,
    unique_patients,
    average_length_of_stay,
    readmissions,
    readmission_rate_pct,

    net_revenue,
    collected_amount,
    outstanding_amount,
    revenue_per_admission,

    ROUND(
        department_avg_admissions::numeric,
        2
    ) AS department_avg_admissions,

    ROUND(
        (
            admissions
            - department_avg_admissions
        )::numeric,
        2
    ) AS admissions_vs_department_avg,

    ROUND(
        department_avg_alos::numeric,
        2
    ) AS department_avg_alos,

    ROUND(
        (
            average_length_of_stay
            - department_avg_alos
        )::numeric,
        2
    ) AS alos_vs_department_avg,

    ROUND(
        department_avg_readmission_rate::numeric,
        2
    ) AS department_avg_readmission_rate,

    ROUND(
        (
            readmission_rate_pct
            - department_avg_readmission_rate
        )::numeric,
        2
    ) AS readmission_rate_vs_department_avg_pp,

    ROUND(
        department_avg_revenue::numeric,
        2
    ) AS department_avg_revenue,

    ROUND(
        (
            net_revenue
            - department_avg_revenue
        )::numeric,
        2
    ) AS revenue_vs_department_avg,

    ROUND(
        department_avg_revenue_per_admission::numeric,
        2
    ) AS department_avg_revenue_per_admission,

    ROUND(
        (
            revenue_per_admission
            - department_avg_revenue_per_admission
        )::numeric,
        2
    ) AS revenue_per_admission_vs_avg,

    department_admission_rank,
    department_revenue_rank

FROM benchmarked;


-- ============================================================
-- DOCUMENTATION
-- ============================================================

COMMENT ON VIEW analytics.vw_diagnosis_performance IS
'Diagnosis-level operational and financial performance.';

COMMENT ON VIEW analytics.vw_diagnosis_category_performance IS
'Diagnosis-category service-line performance summary.';

COMMENT ON VIEW analytics.vw_monthly_diagnosis_trend IS
'Monthly diagnosis volume, readmission and rolling trend analysis.';

COMMENT ON VIEW analytics.vw_hospital_monthly_comparison IS
'Operational-month hospital KPI comparison with month-over-month and rolling metrics. Financial-only months with zero admissions are excluded from this operational comparison view.';

COMMENT ON VIEW analytics.vw_department_monthly_benchmark IS
'Monthly department performance compared with hospital department averages.';

COMMENT ON VIEW analytics.vw_doctor_department_benchmark IS
'Doctor performance compared with peers in the same department.';