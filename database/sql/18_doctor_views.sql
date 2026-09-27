-- ============================================================
-- HOSPITAL 360
-- PHASE 5.5 — DOCTOR ANALYTICS LAYER
-- ============================================================
--
-- Existing doctor views retained:
--   analytics.vw_doctor_performance
--   analytics.vw_doctor_workload
--   analytics.vw_doctor_department_benchmark
--
-- This file adds:
--   1. Doctor analytics summary
--   2. Doctor financial contribution
--   3. Monthly doctor performance
--   4. Doctor claim performance
--   5. Doctor patient-utilization profile
--
-- IMPORTANT:
--   All metrics are descriptive / business analytics.
--   They are NOT clinical quality scores.
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- 1. DOCTOR ANALYTICS SUMMARY
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_doctor_analytics_summary AS

WITH admission_metrics AS (

    SELECT
        doctor_key,

        COUNT(*) AS admissions,

        COUNT(
            DISTINCT patient_key
        ) AS unique_patients,

        ROUND(
            AVG(length_of_stay)::numeric,
            2
        ) AS average_length_of_stay,

        COALESCE(
            SUM(length_of_stay),
            0
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
        doctor_key
),

finance_metrics AS (

    SELECT
        a.doctor_key,

        COUNT(b.billing_key) AS bills,

        ROUND(
            SUM(b.gross_amount)::numeric,
            2
        ) AS gross_revenue,

        ROUND(
            SUM(b.discount_amount)::numeric,
            2
        ) AS discount_amount,

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

    FROM warehouse.fact_admission a

    INNER JOIN warehouse.fact_billing b
        ON b.admission_key =
           a.admission_key

    GROUP BY
        a.doctor_key
),

base AS (

    SELECT
        d.doctor_key,
        d.doctor_id,
        d.doctor_name,
        d.gender,
        d.specialization,
        d.qualification,
        d.experience_years,
        d.consultation_fee,
        d.joining_date,
        d.employment_status,

        dep.department_key,
        dep.department_id,
        dep.department_name,

        COALESCE(
            a.admissions,
            0
        ) AS admissions,

        COALESCE(
            a.unique_patients,
            0
        ) AS unique_patients,

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
            f.bills,
            0
        ) AS bills,

        COALESCE(
            f.gross_revenue,
            0
        ) AS gross_revenue,

        COALESCE(
            f.discount_amount,
            0
        ) AS discount_amount,

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

    FROM warehouse.dim_doctor d

    LEFT JOIN warehouse.dim_department dep
        ON dep.department_key =
           d.department_key

    LEFT JOIN admission_metrics a
        ON a.doctor_key =
           d.doctor_key

    LEFT JOIN finance_metrics f
        ON f.doctor_key =
           d.doctor_key
),

metrics AS (

    SELECT
        *,

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
                net_revenue
                / NULLIF(
                    unique_patients,
                    0
                )
            )::numeric,
            2
        ) AS revenue_per_patient,

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
        ) AS collection_efficiency_pct,

        ROUND(
            (
                100.0
                * outstanding_amount
                / NULLIF(
                    net_revenue,
                    0
                )
            )::numeric,
            2
        ) AS outstanding_rate_pct

    FROM base
)

SELECT
    *,

    ROUND(
        (
            100.0
            * net_revenue
            / NULLIF(
                SUM(net_revenue) OVER (),
                0
            )
        )::numeric,
        2
    ) AS hospital_revenue_contribution_pct,

    ROUND(
        (
            100.0
            * admissions
            / NULLIF(
                SUM(admissions) OVER (),
                0
            )
        )::numeric,
        2
    ) AS hospital_admission_contribution_pct,

    DENSE_RANK() OVER (
        ORDER BY
            admissions DESC
    ) AS hospital_admission_rank,

    DENSE_RANK() OVER (
        ORDER BY
            net_revenue DESC
    ) AS hospital_revenue_rank,

    DENSE_RANK() OVER (
        PARTITION BY department_key
        ORDER BY
            admissions DESC
    ) AS department_admission_rank,

    DENSE_RANK() OVER (
        PARTITION BY department_key
        ORDER BY
            net_revenue DESC
    ) AS department_revenue_rank

FROM metrics;


-- ============================================================
-- 2. DOCTOR FINANCIAL CONTRIBUTION
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_doctor_financial_contribution AS

SELECT
    doctor_key,
    doctor_id,
    doctor_name,
    specialization,

    department_key,
    department_id,
    department_name,

    admissions,
    unique_patients,
    bills,

    gross_revenue,
    discount_amount,
    net_revenue,
    collected_amount,
    outstanding_amount,

    revenue_per_admission,
    revenue_per_patient,
    collection_efficiency_pct,
    outstanding_rate_pct,

    hospital_revenue_contribution_pct,
    hospital_revenue_rank,
    department_revenue_rank,

    ROUND(
        (
            100.0
            * net_revenue
            / NULLIF(
                SUM(net_revenue) OVER (
                    PARTITION BY department_key
                ),
                0
            )
        )::numeric,
        2
    ) AS department_revenue_contribution_pct

FROM analytics.vw_doctor_analytics_summary;


-- ============================================================
-- 3. MONTHLY DOCTOR PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_doctor_performance AS

WITH operational AS (

    SELECT
        DATE_TRUNC(
            'month',
            dt.full_date
        )::date AS month_start,

        a.doctor_key,

        COUNT(*) AS admissions,

        COUNT(
            DISTINCT a.patient_key
        ) AS unique_patients,

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
        a.doctor_key
),

financial AS (

    SELECT
        DATE_TRUNC(
            'month',
            dt.full_date
        )::date AS month_start,

        a.doctor_key,

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

    INNER JOIN warehouse.dim_date dt
        ON dt.date_key =
           b.billing_date_key

    GROUP BY
        DATE_TRUNC(
            'month',
            dt.full_date
        )::date,
        a.doctor_key
),

month_doctor AS (

    SELECT
        COALESCE(
            o.month_start,
            f.month_start
        ) AS month_start,

        COALESCE(
            o.doctor_key,
            f.doctor_key
        ) AS doctor_key,

        COALESCE(
            o.admissions,
            0
        ) AS admissions,

        COALESCE(
            o.unique_patients,
            0
        ) AS unique_patients,

        COALESCE(
            o.average_length_of_stay,
            0
        ) AS average_length_of_stay,

        COALESCE(
            o.emergency_admissions,
            0
        ) AS emergency_admissions,

        COALESCE(
            o.icu_admissions,
            0
        ) AS icu_admissions,

        COALESCE(
            o.readmissions,
            0
        ) AS readmissions,

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

    FROM operational o

    FULL OUTER JOIN financial f
        ON f.month_start =
           o.month_start
       AND f.doctor_key =
           o.doctor_key
),

metrics AS (

    SELECT
        md.month_start,

        d.doctor_key,
        d.doctor_id,
        d.doctor_name,
        d.specialization,

        dep.department_key,
        dep.department_id,
        dep.department_name,

        md.admissions,
        md.unique_patients,
        md.average_length_of_stay,
        md.emergency_admissions,
        md.icu_admissions,
        md.readmissions,

        ROUND(
            (
                100.0
                * md.readmissions
                / NULLIF(
                    md.admissions,
                    0
                )
            )::numeric,
            2
        ) AS readmission_rate_pct,

        md.net_revenue,
        md.collected_amount,
        md.outstanding_amount,

        ROUND(
            (
                md.net_revenue
                / NULLIF(
                    md.admissions,
                    0
                )
            )::numeric,
            2
        ) AS revenue_per_admission

    FROM month_doctor md

    INNER JOIN warehouse.dim_doctor d
        ON d.doctor_key =
           md.doctor_key

    LEFT JOIN warehouse.dim_department dep
        ON dep.department_key =
           d.department_key
),

windowed AS (

    SELECT
        *,

        LAG(admissions) OVER (
            PARTITION BY doctor_key
            ORDER BY month_start
        ) AS previous_month_admissions,

        LAG(net_revenue) OVER (
            PARTITION BY doctor_key
            ORDER BY month_start
        ) AS previous_month_net_revenue,

        AVG(admissions) OVER (
            PARTITION BY doctor_key
            ORDER BY month_start
            ROWS BETWEEN
                2 PRECEDING
                AND CURRENT ROW
        ) AS rolling_3_month_admissions,

        AVG(net_revenue) OVER (
            PARTITION BY doctor_key
            ORDER BY month_start
            ROWS BETWEEN
                2 PRECEDING
                AND CURRENT ROW
        ) AS rolling_3_month_revenue,

        DENSE_RANK() OVER (
            PARTITION BY month_start
            ORDER BY
                admissions DESC
        ) AS monthly_hospital_admission_rank,

        DENSE_RANK() OVER (
            PARTITION BY month_start
            ORDER BY
                net_revenue DESC
        ) AS monthly_hospital_revenue_rank,

        DENSE_RANK() OVER (
            PARTITION BY
                month_start,
                department_key
            ORDER BY
                admissions DESC
        ) AS monthly_department_admission_rank,

        DENSE_RANK() OVER (
            PARTITION BY
                month_start,
                department_key
            ORDER BY
                net_revenue DESC
        ) AS monthly_department_revenue_rank

    FROM metrics
)

SELECT
    month_start,

    doctor_key,
    doctor_id,
    doctor_name,
    specialization,

    department_key,
    department_id,
    department_name,

    admissions,
    unique_patients,
    average_length_of_stay,
    emergency_admissions,
    icu_admissions,
    readmissions,
    readmission_rate_pct,

    net_revenue,
    collected_amount,
    outstanding_amount,
    revenue_per_admission,

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

    ROUND(
        rolling_3_month_admissions::numeric,
        2
    ) AS rolling_3_month_admissions,

    ROUND(
        rolling_3_month_revenue::numeric,
        2
    ) AS rolling_3_month_revenue,

    monthly_hospital_admission_rank,
    monthly_hospital_revenue_rank,
    monthly_department_admission_rank,
    monthly_department_revenue_rank

FROM windowed;


-- ============================================================
-- 4. DOCTOR CLAIM PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_doctor_claim_performance AS

WITH doctor_claims AS (

    SELECT
        a.doctor_key,

        COUNT(c.claim_key) AS total_claims,

        ROUND(
            COALESCE(
                SUM(c.claim_amount),
                0
            )::numeric,
            2
        ) AS total_claim_amount,

        ROUND(
            COALESCE(
                SUM(c.approved_amount),
                0
            )::numeric,
            2
        ) AS approved_amount,

        ROUND(
            COALESCE(
                SUM(c.rejected_amount),
                0
            )::numeric,
            2
        ) AS rejected_amount,

        COUNT(c.claim_key) FILTER (
            WHERE LOWER(c.claim_status) = 'approved'
        ) AS approved_claims,

        COUNT(c.claim_key) FILTER (
            WHERE LOWER(c.claim_status)
                  = 'partially approved'
        ) AS partially_approved_claims,

        COUNT(c.claim_key) FILTER (
            WHERE LOWER(c.claim_status) = 'rejected'
        ) AS rejected_claims,

        COUNT(c.claim_key) FILTER (
            WHERE LOWER(c.claim_status) = 'pending'
        ) AS pending_claims,

        ROUND(
            AVG(c.processing_days)::numeric,
            2
        ) AS average_processing_days

    FROM warehouse.fact_admission a

    INNER JOIN warehouse.fact_billing b
        ON b.admission_key =
           a.admission_key

    INNER JOIN warehouse.fact_claim c
        ON c.billing_key =
           b.billing_key

    GROUP BY
        a.doctor_key
),

base AS (

    SELECT
        d.doctor_key,
        d.doctor_id,
        d.doctor_name,
        d.specialization,

        dep.department_key,
        dep.department_id,
        dep.department_name,

        COALESCE(
            c.total_claims,
            0
        ) AS total_claims,

        COALESCE(
            c.total_claim_amount,
            0
        ) AS total_claim_amount,

        COALESCE(
            c.approved_amount,
            0
        ) AS approved_amount,

        COALESCE(
            c.rejected_amount,
            0
        ) AS rejected_amount,

        COALESCE(
            c.approved_claims,
            0
        ) AS approved_claims,

        COALESCE(
            c.partially_approved_claims,
            0
        ) AS partially_approved_claims,

        COALESCE(
            c.rejected_claims,
            0
        ) AS rejected_claims,

        COALESCE(
            c.pending_claims,
            0
        ) AS pending_claims,

        c.average_processing_days

    FROM warehouse.dim_doctor d

    LEFT JOIN warehouse.dim_department dep
        ON dep.department_key =
           d.department_key

    LEFT JOIN doctor_claims c
        ON c.doctor_key =
           d.doctor_key
)

SELECT
    *,

    ROUND(
        (
            100.0
            * approved_claims
            / NULLIF(
                total_claims,
                0
            )
        )::numeric,
        2
    ) AS approval_rate_pct,

    ROUND(
        (
            100.0
            * rejected_claims
            / NULLIF(
                total_claims,
                0
            )
        )::numeric,
        2
    ) AS rejection_rate_pct,

    ROUND(
        (
            rejected_amount
            / NULLIF(
                rejected_claims,
                0
            )
        )::numeric,
        2
    ) AS average_rejected_amount,

    DENSE_RANK() OVER (
        ORDER BY
            total_claim_amount DESC
    ) AS claim_value_rank

FROM base;


-- ============================================================
-- 5. DOCTOR PATIENT UTILIZATION PROFILE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_doctor_patient_utilization AS

WITH patient_doctor AS (

    SELECT
        doctor_key,
        patient_key,

        COUNT(*) AS patient_admissions,

        COALESCE(
            SUM(length_of_stay),
            0
        ) AS patient_inpatient_days,

        COUNT(*) FILTER (
            WHERE emergency_flag = TRUE
        ) AS patient_emergency_admissions,

        COUNT(*) FILTER (
            WHERE icu_flag = TRUE
        ) AS patient_icu_admissions,

        COUNT(*) FILTER (
            WHERE readmission_flag = TRUE
        ) AS patient_readmissions

    FROM warehouse.fact_admission

    GROUP BY
        doctor_key,
        patient_key
),

doctor_profile AS (

    SELECT
        doctor_key,

        COUNT(*) AS unique_patients,

        COUNT(*) FILTER (
            WHERE patient_admissions = 1
        ) AS single_admission_patients,

        COUNT(*) FILTER (
            WHERE patient_admissions >= 2
        ) AS repeat_patients,

        COUNT(*) FILTER (
            WHERE patient_admissions >= 4
        ) AS high_utilization_patients,

        ROUND(
            AVG(patient_admissions)::numeric,
            2
        ) AS average_admissions_per_patient,

        ROUND(
            AVG(patient_inpatient_days)::numeric,
            2
        ) AS average_inpatient_days_per_patient,

        SUM(
            patient_emergency_admissions
        ) AS emergency_admissions,

        SUM(
            patient_icu_admissions
        ) AS icu_admissions,

        SUM(
            patient_readmissions
        ) AS readmissions

    FROM patient_doctor

    GROUP BY
        doctor_key
)

SELECT
    d.doctor_key,
    d.doctor_id,
    d.doctor_name,
    d.specialization,

    dep.department_key,
    dep.department_id,
    dep.department_name,

    COALESCE(
        p.unique_patients,
        0
    ) AS unique_patients,

    COALESCE(
        p.single_admission_patients,
        0
    ) AS single_admission_patients,

    COALESCE(
        p.repeat_patients,
        0
    ) AS repeat_patients,

    COALESCE(
        p.high_utilization_patients,
        0
    ) AS high_utilization_patients,

    COALESCE(
        p.average_admissions_per_patient,
        0
    ) AS average_admissions_per_patient,

    COALESCE(
        p.average_inpatient_days_per_patient,
        0
    ) AS average_inpatient_days_per_patient,

    COALESCE(
        p.emergency_admissions,
        0
    ) AS emergency_admissions,

    COALESCE(
        p.icu_admissions,
        0
    ) AS icu_admissions,

    COALESCE(
        p.readmissions,
        0
    ) AS readmissions,

    ROUND(
        (
            100.0
            * COALESCE(
                p.repeat_patients,
                0
            )
            / NULLIF(
                COALESCE(
                    p.unique_patients,
                    0
                ),
                0
            )
        )::numeric,
        2
    ) AS repeat_patient_rate_pct,

    ROUND(
        (
            100.0
            * COALESCE(
                p.high_utilization_patients,
                0
            )
            / NULLIF(
                COALESCE(
                    p.unique_patients,
                    0
                ),
                0
            )
        )::numeric,
        2
    ) AS high_utilization_patient_rate_pct

FROM warehouse.dim_doctor d

LEFT JOIN warehouse.dim_department dep
    ON dep.department_key =
       d.department_key

LEFT JOIN doctor_profile p
    ON p.doctor_key =
       d.doctor_key;


-- ============================================================
-- DOCUMENTATION
-- ============================================================

COMMENT ON VIEW analytics.vw_doctor_analytics_summary IS
'Unified doctor-level operational and financial analytics summary.';

COMMENT ON VIEW analytics.vw_doctor_financial_contribution IS
'Doctor financial contribution to hospital and department revenue.';

COMMENT ON VIEW analytics.vw_monthly_doctor_performance IS
'Monthly doctor operational and financial performance with MoM and rolling metrics.';

COMMENT ON VIEW analytics.vw_doctor_claim_performance IS
'Doctor-associated insurance claim volume, value and processing analytics.';

COMMENT ON VIEW analytics.vw_doctor_patient_utilization IS
'Doctor-level descriptive patient utilization and repeat-patient profile.';