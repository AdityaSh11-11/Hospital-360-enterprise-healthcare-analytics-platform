-- ============================================================
-- HOSPITAL 360
-- PHASE 5.1 — CORE ANALYTICS SEMANTIC LAYER
-- ============================================================
--
-- Source of truth:
-- Actual Hospital 360 PostgreSQL warehouse schema.
--
-- IMPORTANT GRAIN RULE:
-- Admissions, billing, claims, labs and medications have
-- different grains.
--
-- Never join multiple one-to-many fact tables before
-- aggregation. Each fact is aggregated independently first.
-- ============================================================


CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- 1. EXECUTIVE KPI VIEW
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_executive_kpis AS

WITH patient_metrics AS (

    SELECT
        COUNT(*) AS total_patients

    FROM warehouse.dim_patient

    WHERE is_active = TRUE
),

admission_metrics AS (

    SELECT
        COUNT(*) AS total_admissions,

        COUNT(
            DISTINCT patient_key
        ) AS admitted_patients,

        ROUND(
            AVG(length_of_stay)::numeric,
            2
        ) AS average_length_of_stay,

        COUNT(*) FILTER (
            WHERE icu_flag = TRUE
        ) AS icu_admissions,

        COUNT(*) FILTER (
            WHERE emergency_flag = TRUE
        ) AS emergency_admissions,

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
        ) AS readmission_rate_pct

    FROM warehouse.fact_admission
),

billing_metrics AS (

    SELECT
        ROUND(
            COALESCE(
                SUM(gross_amount),
                0
            )::numeric,
            2
        ) AS gross_revenue,

        ROUND(
            COALESCE(
                SUM(discount_amount),
                0
            )::numeric,
            2
        ) AS total_discount,

        ROUND(
            COALESCE(
                SUM(net_amount),
                0
            )::numeric,
            2
        ) AS net_revenue,

        ROUND(
            COALESCE(
                SUM(paid_amount),
                0
            )::numeric,
            2
        ) AS collected_amount,

        ROUND(
            COALESCE(
                SUM(outstanding_amount),
                0
            )::numeric,
            2
        ) AS outstanding_amount,

        ROUND(
            (
                100.0
                * COALESCE(
                    SUM(paid_amount),
                    0
                )
                / NULLIF(
                    SUM(net_amount),
                    0
                )
            )::numeric,
            2
        ) AS collection_efficiency_pct,

        ROUND(
            (
                100.0
                * COALESCE(
                    SUM(discount_amount),
                    0
                )
                / NULLIF(
                    SUM(gross_amount),
                    0
                )
            )::numeric,
            2
        ) AS discount_rate_pct

    FROM warehouse.fact_billing
),

claim_metrics AS (

    SELECT
        COUNT(*) AS total_claims,

        COUNT(*) FILTER (
            WHERE LOWER(claim_status) = 'approved'
        ) AS approved_claims,

        COUNT(*) FILTER (
            WHERE LOWER(claim_status) = 'partially approved'
        ) AS partially_approved_claims,

        COUNT(*) FILTER (
            WHERE LOWER(claim_status) = 'rejected'
        ) AS rejected_claims,

        COUNT(*) FILTER (
            WHERE LOWER(claim_status) = 'pending'
        ) AS pending_claims,

        ROUND(
            (
                100.0
                * COUNT(*) FILTER (
                    WHERE LOWER(claim_status) = 'rejected'
                )
                / NULLIF(
                    COUNT(*),
                    0
                )
            )::numeric,
            2
        ) AS claim_rejection_rate_pct,

        ROUND(
            AVG(processing_days)::numeric,
            2
        ) AS average_claim_processing_days

    FROM warehouse.fact_claim
)

SELECT
    p.total_patients,

    a.total_admissions,

    a.admitted_patients,

    a.average_length_of_stay,

    a.icu_admissions,

    a.emergency_admissions,

    a.readmissions,

    a.readmission_rate_pct,

    b.gross_revenue,

    b.total_discount,

    b.discount_rate_pct,

    b.net_revenue,

    b.collected_amount,

    b.outstanding_amount,

    b.collection_efficiency_pct,

    c.total_claims,

    c.approved_claims,

    c.partially_approved_claims,

    c.rejected_claims,

    c.pending_claims,

    c.claim_rejection_rate_pct,

    c.average_claim_processing_days

FROM patient_metrics p

CROSS JOIN admission_metrics a

CROSS JOIN billing_metrics b

CROSS JOIN claim_metrics c;


-- ============================================================
-- 2. MONTHLY HOSPITAL PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_hospital_performance AS

WITH admission_monthly AS (

    SELECT
        DATE_TRUNC(
            'month',
            d.full_date
        )::date AS month_start,

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

    INNER JOIN warehouse.dim_date d
        ON d.date_key =
           a.admission_date_key

    GROUP BY
        DATE_TRUNC(
            'month',
            d.full_date
        )::date
),

billing_monthly AS (

    SELECT
        DATE_TRUNC(
            'month',
            d.full_date
        )::date AS month_start,

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

    FROM warehouse.fact_billing b

    INNER JOIN warehouse.dim_date d
        ON d.date_key =
           b.billing_date_key

    GROUP BY
        DATE_TRUNC(
            'month',
            d.full_date
        )::date
),

months AS (

    SELECT month_start
    FROM admission_monthly

    UNION

    SELECT month_start
    FROM billing_monthly
),

combined AS (

    SELECT
        m.month_start,

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
            b.gross_revenue,
            0
        ) AS gross_revenue,

        COALESCE(
            b.discount_amount,
            0
        ) AS discount_amount,

        COALESCE(
            b.net_revenue,
            0
        ) AS net_revenue,

        COALESCE(
            b.collected_amount,
            0
        ) AS collected_amount,

        COALESCE(
            b.outstanding_amount,
            0
        ) AS outstanding_amount

    FROM months m

    LEFT JOIN admission_monthly a
        ON a.month_start =
           m.month_start

    LEFT JOIN billing_monthly b
        ON b.month_start =
           m.month_start
),

with_previous AS (

    SELECT
        *,

        LAG(net_revenue) OVER (
            ORDER BY month_start
        ) AS previous_month_revenue

    FROM combined
)

SELECT
    month_start,

    admissions,

    unique_patients,

    average_length_of_stay,

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

    discount_amount,

    ROUND(
        (
            100.0
            * discount_amount
            / NULLIF(
                gross_revenue,
                0
            )
        )::numeric,
        2
    ) AS discount_rate_pct,

    net_revenue,

    collected_amount,

    outstanding_amount,

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

    previous_month_revenue,

    ROUND(
        (
            100.0
            * (
                net_revenue
                - previous_month_revenue
            )
            / NULLIF(
                previous_month_revenue,
                0
            )
        )::numeric,
        2
    ) AS revenue_mom_growth_pct

FROM with_previous;


-- ============================================================
-- 3. DEPARTMENT PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_department_performance AS

WITH admission_department AS (

    SELECT
        department_key,

        COUNT(*) AS admissions,

        COUNT(
            DISTINCT patient_key
        ) AS unique_patients,

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
        ) AS readmissions

    FROM warehouse.fact_admission

    GROUP BY
        department_key
),

billing_department AS (

    SELECT
        a.department_key,

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

    FROM warehouse.fact_billing b

    INNER JOIN warehouse.fact_admission a
        ON a.admission_key =
           b.admission_key

    GROUP BY
        a.department_key
),

combined AS (

    SELECT
        d.department_key,

        d.department_id,

        d.department_name,

        d.department_type,

        d.floor_number,

        d.bed_capacity,

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
            b.gross_revenue,
            0
        ) AS gross_revenue,

        COALESCE(
            b.discount_amount,
            0
        ) AS discount_amount,

        COALESCE(
            b.net_revenue,
            0
        ) AS net_revenue,

        COALESCE(
            b.collected_amount,
            0
        ) AS collected_amount,

        COALESCE(
            b.outstanding_amount,
            0
        ) AS outstanding_amount

    FROM warehouse.dim_department d

    LEFT JOIN admission_department a
        ON a.department_key =
           d.department_key

    LEFT JOIN billing_department b
        ON b.department_key =
           d.department_key
)

SELECT
    department_key,

    department_id,

    department_name,

    department_type,

    floor_number,

    bed_capacity,

    admissions,

    unique_patients,

    average_length_of_stay,

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

    discount_amount,

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
    ) AS collection_efficiency_pct,

    DENSE_RANK() OVER (
        ORDER BY
            net_revenue DESC
    ) AS revenue_rank

FROM combined;


-- ============================================================
-- 4. DOCTOR PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_doctor_performance AS

WITH doctor_admissions AS (

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

doctor_billing AS (

    SELECT
        a.doctor_key,

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
        a.doctor_key
),

combined AS (

    SELECT
        d.doctor_key,

        d.doctor_id,

        d.doctor_name,

        d.gender,

        d.specialization,

        d.department_key,

        dep.department_name,

        d.qualification,

        d.experience_years,

        d.consultation_fee,

        d.joining_date,

        d.employment_status,

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
            b.gross_revenue,
            0
        ) AS gross_revenue,

        COALESCE(
            b.net_revenue,
            0
        ) AS net_revenue,

        COALESCE(
            b.collected_amount,
            0
        ) AS collected_amount,

        COALESCE(
            b.outstanding_amount,
            0
        ) AS outstanding_amount

    FROM warehouse.dim_doctor d

    LEFT JOIN warehouse.dim_department dep
        ON dep.department_key =
           d.department_key

    LEFT JOIN doctor_admissions a
        ON a.doctor_key =
           d.doctor_key

    LEFT JOIN doctor_billing b
        ON b.doctor_key =
           d.doctor_key
)

SELECT
    doctor_key,

    doctor_id,

    doctor_name,

    gender,

    specialization,

    department_key,

    department_name,

    qualification,

    experience_years,

    consultation_fee,

    joining_date,

    employment_status,

    admissions,

    unique_patients,

    average_length_of_stay,

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

    DENSE_RANK() OVER (
        ORDER BY
            net_revenue DESC
    ) AS hospital_revenue_rank,

    DENSE_RANK() OVER (
        PARTITION BY
            department_key

        ORDER BY
            net_revenue DESC
    ) AS department_revenue_rank

FROM combined;


-- ============================================================
-- 5. CLAIM / INSURER PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_claim_performance AS

SELECT
    i.insurer_key,

    i.insurer_id,

    i.insurer_name,

    i.insurer_type,

    i.active_flag,

    COUNT(
        c.claim_key
    ) AS total_claims,

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

    COUNT(
        c.claim_key
    ) FILTER (
        WHERE
            LOWER(c.claim_status)
            = 'approved'
    ) AS approved_claims,

    COUNT(
        c.claim_key
    ) FILTER (
        WHERE
            LOWER(c.claim_status)
            = 'partially approved'
    ) AS partially_approved_claims,

    COUNT(
        c.claim_key
    ) FILTER (
        WHERE
            LOWER(c.claim_status)
            = 'rejected'
    ) AS rejected_claims,

    COUNT(
        c.claim_key
    ) FILTER (
        WHERE
            LOWER(c.claim_status)
            = 'pending'
    ) AS pending_claims,

    ROUND(
        (
            100.0
            * COUNT(
                c.claim_key
            ) FILTER (
                WHERE
                    LOWER(c.claim_status)
                    = 'rejected'
            )
            / NULLIF(
                COUNT(c.claim_key),
                0
            )
        )::numeric,
        2
    ) AS rejection_rate_pct,

    ROUND(
        AVG(c.processing_days)::numeric,
        2
    ) AS average_processing_days,

    ROUND(
        (
            COALESCE(
                SUM(c.approved_amount),
                0
            )
            / NULLIF(
                COUNT(c.claim_key),
                0
            )
        )::numeric,
        2
    ) AS average_approved_amount

FROM warehouse.dim_insurer i

LEFT JOIN warehouse.fact_claim c
    ON c.insurer_key =
       i.insurer_key

GROUP BY
    i.insurer_key,
    i.insurer_id,
    i.insurer_name,
    i.insurer_type,
    i.active_flag;


-- ============================================================
-- 6. DAILY OPERATIONS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_daily_operations AS

WITH daily_admissions AS (

    SELECT
        d.full_date AS activity_date,

        COUNT(*) AS admissions,

        COUNT(
            DISTINCT a.patient_key
        ) AS unique_patients,

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
            AVG(a.length_of_stay)::numeric,
            2
        ) AS average_length_of_stay

    FROM warehouse.fact_admission a

    INNER JOIN warehouse.dim_date d
        ON d.date_key =
           a.admission_date_key

    GROUP BY
        d.full_date
),

daily_billing AS (

    SELECT
        d.full_date AS activity_date,

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

    INNER JOIN warehouse.dim_date d
        ON d.date_key =
           b.billing_date_key

    GROUP BY
        d.full_date
),

activity_dates AS (

    SELECT activity_date
    FROM daily_admissions

    UNION

    SELECT activity_date
    FROM daily_billing
)

SELECT
    x.activity_date,

    EXTRACT(
        YEAR
        FROM x.activity_date
    )::integer AS year,

    EXTRACT(
        QUARTER
        FROM x.activity_date
    )::integer AS quarter,

    EXTRACT(
        MONTH
        FROM x.activity_date
    )::integer AS month,

    TO_CHAR(
        x.activity_date,
        'Mon'
    ) AS month_name,

    TO_CHAR(
        x.activity_date,
        'Dy'
    ) AS day_name,

    COALESCE(
        a.admissions,
        0
    ) AS admissions,

    COALESCE(
        a.unique_patients,
        0
    ) AS unique_patients,

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
        a.average_length_of_stay,
        0
    ) AS average_length_of_stay,

    COALESCE(
        b.gross_revenue,
        0
    ) AS gross_revenue,

    COALESCE(
        b.net_revenue,
        0
    ) AS net_revenue,

    COALESCE(
        b.collected_amount,
        0
    ) AS collected_amount,

    COALESCE(
        b.outstanding_amount,
        0
    ) AS outstanding_amount

FROM activity_dates x

LEFT JOIN daily_admissions a
    ON a.activity_date =
       x.activity_date

LEFT JOIN daily_billing b
    ON b.activity_date =
       x.activity_date;


-- ============================================================
-- 7. PATIENT UTILIZATION
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_patient_utilization AS

WITH patient_admissions AS (

    SELECT
        patient_key,

        COUNT(*) AS lifetime_admissions,

        MIN(
            admission_timestamp
        ) AS first_admission_timestamp,

        MAX(
            admission_timestamp
        ) AS latest_admission_timestamp,

        SUM(
            length_of_stay
        ) AS total_length_of_stay_days,

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
        ) AS readmissions

    FROM warehouse.fact_admission

    GROUP BY
        patient_key
),

patient_finance AS (

    SELECT
        patient_key,

        ROUND(
            SUM(gross_amount)::numeric,
            2
        ) AS lifetime_gross_revenue,

        ROUND(
            SUM(net_amount)::numeric,
            2
        ) AS lifetime_net_revenue,

        ROUND(
            SUM(paid_amount)::numeric,
            2
        ) AS lifetime_paid_amount,

        ROUND(
            SUM(outstanding_amount)::numeric,
            2
        ) AS lifetime_outstanding_amount

    FROM warehouse.fact_billing

    GROUP BY
        patient_key
)

SELECT
    p.patient_key,

    p.patient_id,

    p.first_name,

    p.last_name,

    p.gender,

    p.date_of_birth,

    EXTRACT(
        YEAR
        FROM AGE(
            CURRENT_DATE,
            p.date_of_birth
        )
    )::integer AS current_age,

    p.blood_group,

    p.city,

    p.state,

    p.insurance_status,

    p.chronic_condition,

    p.registration_date,

    p.is_active,

    COALESCE(
        a.lifetime_admissions,
        0
    ) AS lifetime_admissions,

    a.first_admission_timestamp,

    a.latest_admission_timestamp,

    COALESCE(
        a.total_length_of_stay_days,
        0
    ) AS total_length_of_stay_days,

    COALESCE(
        a.average_length_of_stay,
        0
    ) AS average_length_of_stay,

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
        f.lifetime_gross_revenue,
        0
    ) AS lifetime_gross_revenue,

    COALESCE(
        f.lifetime_net_revenue,
        0
    ) AS lifetime_net_revenue,

    COALESCE(
        f.lifetime_paid_amount,
        0
    ) AS lifetime_paid_amount,

    COALESCE(
        f.lifetime_outstanding_amount,
        0
    ) AS lifetime_outstanding_amount

FROM warehouse.dim_patient p

LEFT JOIN patient_admissions a
    ON a.patient_key =
       p.patient_key

LEFT JOIN patient_finance f
    ON f.patient_key =
       p.patient_key

WHERE p.is_active = TRUE;


-- ============================================================
-- 8. MONTHLY DEPARTMENT PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_department_performance AS

WITH admission_monthly AS (

    SELECT
        DATE_TRUNC(
            'month',
            d.full_date
        )::date AS month_start,

        a.department_key,

        COUNT(*) AS admissions,

        COUNT(
            DISTINCT a.patient_key
        ) AS unique_patients,

        ROUND(
            AVG(a.length_of_stay)::numeric,
            2
        ) AS average_length_of_stay,

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
        )::date,

        a.department_key
),

billing_monthly AS (

    SELECT
        DATE_TRUNC(
            'month',
            d.full_date
        )::date AS month_start,

        a.department_key,

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

    INNER JOIN warehouse.dim_date d
        ON d.date_key =
           b.billing_date_key

    GROUP BY
        DATE_TRUNC(
            'month',
            d.full_date
        )::date,

        a.department_key
),

metric_keys AS (

    SELECT
        month_start,
        department_key

    FROM admission_monthly

    UNION

    SELECT
        month_start,
        department_key

    FROM billing_monthly
),

combined AS (

    SELECT
        k.month_start,

        k.department_key,

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
            a.readmissions,
            0
        ) AS readmissions,

        COALESCE(
            b.gross_revenue,
            0
        ) AS gross_revenue,

        COALESCE(
            b.net_revenue,
            0
        ) AS net_revenue,

        COALESCE(
            b.collected_amount,
            0
        ) AS collected_amount,

        COALESCE(
            b.outstanding_amount,
            0
        ) AS outstanding_amount

    FROM metric_keys k

    LEFT JOIN admission_monthly a
        ON a.month_start =
           k.month_start

       AND a.department_key =
           k.department_key

    LEFT JOIN billing_monthly b
        ON b.month_start =
           k.month_start

       AND b.department_key =
           k.department_key
),

with_previous AS (

    SELECT
        c.*,

        LAG(
            c.net_revenue
        ) OVER (
            PARTITION BY
                c.department_key

            ORDER BY
                c.month_start
        ) AS previous_month_revenue

    FROM combined c
)

SELECT
    c.month_start,

    d.department_key,

    d.department_id,

    d.department_name,

    c.admissions,

    c.unique_patients,

    c.average_length_of_stay,

    c.readmissions,

    ROUND(
        (
            100.0
            * c.readmissions
            / NULLIF(
                c.admissions,
                0
            )
        )::numeric,
        2
    ) AS readmission_rate_pct,

    c.gross_revenue,

    c.net_revenue,

    c.collected_amount,

    c.outstanding_amount,

    ROUND(
        (
            c.net_revenue
            / NULLIF(
                c.admissions,
                0
            )
        )::numeric,
        2
    ) AS revenue_per_admission,

    c.previous_month_revenue,

    ROUND(
        (
            100.0
            * (
                c.net_revenue
                - c.previous_month_revenue
            )
            / NULLIF(
                c.previous_month_revenue,
                0
            )
        )::numeric,
        2
    ) AS revenue_mom_growth_pct,

    DENSE_RANK() OVER (
        PARTITION BY
            c.month_start

        ORDER BY
            c.net_revenue DESC
    ) AS monthly_revenue_rank

FROM with_previous c

INNER JOIN warehouse.dim_department d
    ON d.department_key =
       c.department_key;


-- ============================================================
-- VIEW DOCUMENTATION
-- ============================================================

COMMENT ON VIEW analytics.vw_executive_kpis IS
'Enterprise-level Hospital 360 executive KPI summary.';


COMMENT ON VIEW analytics.vw_monthly_hospital_performance IS
'Monthly hospital operations and financial trends including month-over-month revenue growth.';


COMMENT ON VIEW analytics.vw_department_performance IS
'Department-level operational and financial performance.';


COMMENT ON VIEW analytics.vw_doctor_performance IS
'Doctor-level admissions, utilization, financial performance and revenue rankings.';


COMMENT ON VIEW analytics.vw_claim_performance IS
'Insurance claim performance summarized by insurer.';


COMMENT ON VIEW analytics.vw_daily_operations IS
'Daily operational and financial activity using warehouse date dimensions.';


COMMENT ON VIEW analytics.vw_patient_utilization IS
'Patient-level lifetime hospital utilization and financial metrics.';


COMMENT ON VIEW analytics.vw_monthly_department_performance IS
'Monthly department operations, financial performance, growth and ranking metrics.';