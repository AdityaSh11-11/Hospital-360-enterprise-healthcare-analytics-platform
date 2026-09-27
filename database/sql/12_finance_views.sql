-- ============================================================
-- HOSPITAL 360
-- PHASE 5.2 — FINANCE ANALYTICS VIEWS
-- ============================================================
--
-- Financial reporting date:
-- fact_billing.billing_date_key -> dim_date.date_key
--
-- Grain protection:
-- Billing is aggregated independently before combining with
-- other analytical datasets.
-- ============================================================


CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- 1. FINANCE SUMMARY
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_finance_summary AS

SELECT
    COUNT(*) AS total_bills,

    COUNT(
        DISTINCT patient_key
    ) AS billed_patients,

    ROUND(
        SUM(gross_amount)::numeric,
        2
    ) AS gross_revenue,

    ROUND(
        SUM(discount_amount)::numeric,
        2
    ) AS total_discount,

    ROUND(
        SUM(tax_amount)::numeric,
        2
    ) AS total_tax,

    ROUND(
        SUM(net_amount)::numeric,
        2
    ) AS net_revenue,

    ROUND(
        SUM(insurance_amount)::numeric,
        2
    ) AS insurance_receivable,

    ROUND(
        SUM(patient_amount)::numeric,
        2
    ) AS patient_responsibility,

    ROUND(
        SUM(paid_amount)::numeric,
        2
    ) AS collected_amount,

    ROUND(
        SUM(outstanding_amount)::numeric,
        2
    ) AS outstanding_amount,

    ROUND(
        AVG(net_amount)::numeric,
        2
    ) AS average_bill_value,

    ROUND(
        (
            100.0
            * SUM(discount_amount)
            / NULLIF(
                SUM(gross_amount),
                0
            )
        )::numeric,
        2
    ) AS discount_rate_pct,

    ROUND(
        (
            100.0
            * SUM(paid_amount)
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
            * SUM(outstanding_amount)
            / NULLIF(
                SUM(net_amount),
                0
            )
        )::numeric,
        2
    ) AS outstanding_rate_pct

FROM warehouse.fact_billing;


-- ============================================================
-- 2. MONTHLY FINANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_finance AS

WITH monthly AS (

    SELECT
        DATE_TRUNC(
            'month',
            d.full_date
        )::date AS month_start,

        COUNT(*) AS total_bills,

        COUNT(
            DISTINCT b.patient_key
        ) AS billed_patients,

        ROUND(
            SUM(b.gross_amount)::numeric,
            2
        ) AS gross_revenue,

        ROUND(
            SUM(b.discount_amount)::numeric,
            2
        ) AS discount_amount,

        ROUND(
            SUM(b.tax_amount)::numeric,
            2
        ) AS tax_amount,

        ROUND(
            SUM(b.net_amount)::numeric,
            2
        ) AS net_revenue,

        ROUND(
            SUM(b.insurance_amount)::numeric,
            2
        ) AS insurance_amount,

        ROUND(
            SUM(b.patient_amount)::numeric,
            2
        ) AS patient_amount,

        ROUND(
            SUM(b.paid_amount)::numeric,
            2
        ) AS collected_amount,

        ROUND(
            SUM(b.outstanding_amount)::numeric,
            2
        ) AS outstanding_amount,

        ROUND(
            AVG(b.net_amount)::numeric,
            2
        ) AS average_bill_value

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

windowed AS (

    SELECT
        *,

        LAG(net_revenue) OVER (
            ORDER BY month_start
        ) AS previous_month_revenue,

        LAG(collected_amount) OVER (
            ORDER BY month_start
        ) AS previous_month_collections,

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

    total_bills,

    billed_patients,

    gross_revenue,

    discount_amount,

    tax_amount,

    net_revenue,

    insurance_amount,

    patient_amount,

    collected_amount,

    outstanding_amount,

    average_bill_value,

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
    ) AS outstanding_rate_pct,

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
    ) AS revenue_mom_growth_pct,

    previous_month_collections,

    ROUND(
        (
            100.0
            * (
                collected_amount
                - previous_month_collections
            )
            / NULLIF(
                previous_month_collections,
                0
            )
        )::numeric,
        2
    ) AS collection_mom_growth_pct,

    ROUND(
        rolling_3_month_revenue::numeric,
        2
    ) AS rolling_3_month_revenue

FROM windowed;


-- ============================================================
-- 3. PAYMENT STATUS ANALYSIS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_payment_status_analysis AS

SELECT
    payment_status,

    COUNT(*) AS total_bills,

    COUNT(
        DISTINCT patient_key
    ) AS patients,

    ROUND(
        SUM(net_amount)::numeric,
        2
    ) AS net_revenue,

    ROUND(
        SUM(paid_amount)::numeric,
        2
    ) AS collected_amount,

    ROUND(
        SUM(outstanding_amount)::numeric,
        2
    ) AS outstanding_amount,

    ROUND(
        AVG(net_amount)::numeric,
        2
    ) AS average_bill_value,

    ROUND(
        (
            100.0
            * SUM(paid_amount)
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
            * SUM(outstanding_amount)
            / NULLIF(
                SUM(net_amount),
                0
            )
        )::numeric,
        2
    ) AS outstanding_rate_pct

FROM warehouse.fact_billing

GROUP BY
    payment_status;


-- ============================================================
-- 4. PAYMENT METHOD ANALYSIS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_payment_method_analysis AS

SELECT
    payment_method,

    COUNT(*) AS total_bills,

    COUNT(
        DISTINCT patient_key
    ) AS patients,

    ROUND(
        SUM(net_amount)::numeric,
        2
    ) AS net_revenue,

    ROUND(
        SUM(paid_amount)::numeric,
        2
    ) AS collected_amount,

    ROUND(
        SUM(outstanding_amount)::numeric,
        2
    ) AS outstanding_amount,

    ROUND(
        AVG(net_amount)::numeric,
        2
    ) AS average_bill_value,

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
    ) AS bill_mix_pct,

    ROUND(
        (
            100.0
            * SUM(net_amount)
            / NULLIF(
                SUM(SUM(net_amount)) OVER (),
                0
            )
        )::numeric,
        2
    ) AS revenue_mix_pct

FROM warehouse.fact_billing

GROUP BY
    payment_method;


-- ============================================================
-- 5. DEPARTMENT FINANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_department_finance AS

WITH finance AS (

    SELECT
        a.department_key,

        COUNT(*) AS total_bills,

        COUNT(
            DISTINCT b.patient_key
        ) AS billed_patients,

        ROUND(
            SUM(b.room_charge)::numeric,
            2
        ) AS room_revenue,

        ROUND(
            SUM(b.doctor_charge)::numeric,
            2
        ) AS doctor_revenue,

        ROUND(
            SUM(b.procedure_charge)::numeric,
            2
        ) AS procedure_revenue,

        ROUND(
            SUM(b.medication_charge)::numeric,
            2
        ) AS medication_revenue,

        ROUND(
            SUM(b.lab_charge)::numeric,
            2
        ) AS lab_revenue,

        ROUND(
            SUM(b.other_charge)::numeric,
            2
        ) AS other_revenue,

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
        ) AS outstanding_amount,

        ROUND(
            AVG(b.net_amount)::numeric,
            2
        ) AS average_bill_value

    FROM warehouse.fact_billing b

    INNER JOIN warehouse.fact_admission a
        ON a.admission_key =
           b.admission_key

    GROUP BY
        a.department_key
)

SELECT
    d.department_key,

    d.department_id,

    d.department_name,

    d.department_type,

    f.total_bills,

    f.billed_patients,

    f.room_revenue,

    f.doctor_revenue,

    f.procedure_revenue,

    f.medication_revenue,

    f.lab_revenue,

    f.other_revenue,

    f.gross_revenue,

    f.discount_amount,

    f.net_revenue,

    f.collected_amount,

    f.outstanding_amount,

    f.average_bill_value,

    ROUND(
        (
            100.0
            * f.collected_amount
            / NULLIF(
                f.net_revenue,
                0
            )
        )::numeric,
        2
    ) AS collection_efficiency_pct,

    DENSE_RANK() OVER (
        ORDER BY
            f.net_revenue DESC
    ) AS revenue_rank,

    DENSE_RANK() OVER (
        ORDER BY
            f.outstanding_amount DESC
    ) AS outstanding_rank

FROM finance f

INNER JOIN warehouse.dim_department d
    ON d.department_key =
       f.department_key;


-- ============================================================
-- 6. MONTHLY DEPARTMENT FINANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_department_finance AS

WITH monthly AS (

    SELECT
        DATE_TRUNC(
            'month',
            d.full_date
        )::date AS month_start,

        a.department_key,

        COUNT(*) AS total_bills,

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

windowed AS (

    SELECT
        *,

        LAG(net_revenue) OVER (
            PARTITION BY
                department_key
            ORDER BY
                month_start
        ) AS previous_month_revenue

    FROM monthly
)

SELECT
    w.month_start,

    dep.department_key,

    dep.department_id,

    dep.department_name,

    w.total_bills,

    w.gross_revenue,

    w.discount_amount,

    w.net_revenue,

    w.collected_amount,

    w.outstanding_amount,

    ROUND(
        (
            100.0
            * w.collected_amount
            / NULLIF(
                w.net_revenue,
                0
            )
        )::numeric,
        2
    ) AS collection_efficiency_pct,

    w.previous_month_revenue,

    ROUND(
        (
            100.0
            * (
                w.net_revenue
                - w.previous_month_revenue
            )
            / NULLIF(
                w.previous_month_revenue,
                0
            )
        )::numeric,
        2
    ) AS revenue_mom_growth_pct,

    DENSE_RANK() OVER (
        PARTITION BY
            w.month_start
        ORDER BY
            w.net_revenue DESC
    ) AS monthly_revenue_rank

FROM windowed w

INNER JOIN warehouse.dim_department dep
    ON dep.department_key =
       w.department_key;


-- ============================================================
-- DOCUMENTATION
-- ============================================================

COMMENT ON VIEW analytics.vw_finance_summary IS
'Enterprise financial KPI summary derived from billing facts.';

COMMENT ON VIEW analytics.vw_monthly_finance IS
'Monthly revenue, collections, receivables and growth trends.';

COMMENT ON VIEW analytics.vw_payment_status_analysis IS
'Financial performance grouped by billing payment status.';

COMMENT ON VIEW analytics.vw_payment_method_analysis IS
'Billing and revenue mix grouped by payment method.';

COMMENT ON VIEW analytics.vw_department_finance IS
'Department financial performance and charge-component analysis.';

COMMENT ON VIEW analytics.vw_monthly_department_finance IS
'Monthly department financial performance and revenue growth.';