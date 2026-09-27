CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- 1. CFO FINANCIAL SCORECARD
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_cfo_financial_scorecard AS

WITH billing AS (
    SELECT
        COUNT(*) AS total_bills,
        COUNT(DISTINCT patient_key) AS billed_patients,

        SUM(gross_amount) AS gross_revenue,
        SUM(discount_amount) AS discount_amount,
        SUM(tax_amount) AS tax_amount,
        SUM(net_amount) AS net_revenue,

        SUM(insurance_amount) AS insurance_receivable,
        SUM(patient_amount) AS patient_responsibility,

        SUM(paid_amount) AS collected_amount,
        SUM(outstanding_amount) AS outstanding_amount,

        AVG(net_amount) AS average_bill

    FROM warehouse.fact_billing
),

claims AS (
    SELECT
        COUNT(*) AS total_claims,

        SUM(claim_amount) AS claim_amount,
        SUM(approved_amount) AS approved_amount,
        SUM(rejected_amount) AS rejected_amount,

        COUNT(*) FILTER (
            WHERE claim_status = 'Approved'
        ) AS approved_claims,

        COUNT(*) FILTER (
            WHERE claim_status = 'Partially Approved'
        ) AS partially_approved_claims,

        COUNT(*) FILTER (
            WHERE claim_status = 'Rejected'
        ) AS rejected_claims,

        COUNT(*) FILTER (
            WHERE claim_status = 'Pending'
        ) AS pending_claims

    FROM warehouse.fact_claim
)

SELECT
    b.total_bills,
    b.billed_patients,

    ROUND(
        b.gross_revenue::numeric,
        2
    ) AS gross_revenue,

    ROUND(
        b.discount_amount::numeric,
        2
    ) AS discount_amount,

    ROUND(
        (
            100.0
            * b.discount_amount
            / NULLIF(
                b.gross_revenue,
                0
            )
        )::numeric,
        2
    ) AS discount_rate_pct,

    ROUND(
        b.tax_amount::numeric,
        2
    ) AS tax_amount,

    ROUND(
        b.net_revenue::numeric,
        2
    ) AS net_revenue,

    ROUND(
        b.insurance_receivable::numeric,
        2
    ) AS insurance_receivable,

    ROUND(
        b.patient_responsibility::numeric,
        2
    ) AS patient_responsibility,

    ROUND(
        b.collected_amount::numeric,
        2
    ) AS collected_amount,

    ROUND(
        b.outstanding_amount::numeric,
        2
    ) AS outstanding_amount,

    ROUND(
        (
            100.0
            * b.collected_amount
            / NULLIF(
                b.net_revenue,
                0
            )
        )::numeric,
        2
    ) AS collection_efficiency_pct,

    ROUND(
        (
            100.0
            * b.outstanding_amount
            / NULLIF(
                b.net_revenue,
                0
            )
        )::numeric,
        2
    ) AS outstanding_rate_pct,

    ROUND(
        b.average_bill::numeric,
        2
    ) AS average_bill,

    c.total_claims,

    ROUND(
        c.claim_amount::numeric,
        2
    ) AS claim_amount,

    ROUND(
        c.approved_amount::numeric,
        2
    ) AS approved_amount,

    ROUND(
        c.rejected_amount::numeric,
        2
    ) AS rejected_amount,

    c.approved_claims,
    c.partially_approved_claims,
    c.rejected_claims,
    c.pending_claims,

    ROUND(
        (
            100.0
            * c.rejected_claims
            / NULLIF(
                c.total_claims,
                0
            )
        )::numeric,
        2
    ) AS claim_rejection_rate_pct,

    ROUND(
        (
            100.0
            * c.rejected_amount
            / NULLIF(
                c.claim_amount,
                0
            )
        )::numeric,
        2
    ) AS rejected_value_rate_pct

FROM billing b

CROSS JOIN claims c;


-- ============================================================
-- 2. MONTHLY CFO PERFORMANCE
--
-- Billing month is intentionally used for financial reporting.
-- This preserves the existing financial date semantics.
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_cfo_performance AS

WITH monthly AS (
    SELECT
        DATE_TRUNC(
            'month',
            d.full_date
        )::date AS month_start,

        COUNT(*) AS bills,

        COUNT(
            DISTINCT b.patient_key
        ) AS billed_patients,

        SUM(
            b.gross_amount
        ) AS gross_revenue,

        SUM(
            b.discount_amount
        ) AS discount_amount,

        SUM(
            b.net_amount
        ) AS net_revenue,

        SUM(
            b.insurance_amount
        ) AS insurance_receivable,

        SUM(
            b.patient_amount
        ) AS patient_responsibility,

        SUM(
            b.paid_amount
        ) AS collected_amount,

        SUM(
            b.outstanding_amount
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

metrics AS (
    SELECT
        *,

        100.0
        * discount_amount
        / NULLIF(
            gross_revenue,
            0
        ) AS discount_rate_pct,

        100.0
        * collected_amount
        / NULLIF(
            net_revenue,
            0
        ) AS collection_efficiency_pct,

        100.0
        * outstanding_amount
        / NULLIF(
            net_revenue,
            0
        ) AS outstanding_rate_pct

    FROM monthly
)

SELECT
    month_start,
    bills,
    billed_patients,

    ROUND(
        gross_revenue::numeric,
        2
    ) AS gross_revenue,

    ROUND(
        discount_amount::numeric,
        2
    ) AS discount_amount,

    ROUND(
        discount_rate_pct::numeric,
        2
    ) AS discount_rate_pct,

    ROUND(
        net_revenue::numeric,
        2
    ) AS net_revenue,

    ROUND(
        insurance_receivable::numeric,
        2
    ) AS insurance_receivable,

    ROUND(
        patient_responsibility::numeric,
        2
    ) AS patient_responsibility,

    ROUND(
        collected_amount::numeric,
        2
    ) AS collected_amount,

    ROUND(
        outstanding_amount::numeric,
        2
    ) AS outstanding_amount,

    ROUND(
        collection_efficiency_pct::numeric,
        2
    ) AS collection_efficiency_pct,

    ROUND(
        outstanding_rate_pct::numeric,
        2
    ) AS outstanding_rate_pct,

    ROUND(
        (
            100.0
            * (
                net_revenue
                - LAG(
                    net_revenue
                ) OVER (
                    ORDER BY month_start
                )
            )
            / NULLIF(
                LAG(
                    net_revenue
                ) OVER (
                    ORDER BY month_start
                ),
                0
            )
        )::numeric,
        2
    ) AS net_revenue_mom_growth_pct,

    ROUND(
        (
            100.0
            * (
                collected_amount
                - LAG(
                    collected_amount
                ) OVER (
                    ORDER BY month_start
                )
            )
            / NULLIF(
                LAG(
                    collected_amount
                ) OVER (
                    ORDER BY month_start
                ),
                0
            )
        )::numeric,
        2
    ) AS collection_mom_growth_pct,

    ROUND(
        (
            AVG(
                net_revenue
            ) OVER (
                ORDER BY month_start
                ROWS BETWEEN
                    2 PRECEDING
                    AND CURRENT ROW
            )
        )::numeric,
        2
    ) AS rolling_3_month_revenue,

    ROUND(
        (
            AVG(
                collected_amount
            ) OVER (
                ORDER BY month_start
                ROWS BETWEEN
                    2 PRECEDING
                    AND CURRENT ROW
            )
        )::numeric,
        2
    ) AS rolling_3_month_collection

FROM metrics

ORDER BY
    month_start;


-- ============================================================
-- 3. DEPARTMENT CFO PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_department_cfo_performance AS

WITH department_finance AS (
    SELECT
        dep.department_key,
        dep.department_id,
        dep.department_name,

        COUNT(*) AS bills,

        COUNT(
            DISTINCT b.patient_key
        ) AS billed_patients,

        SUM(
            b.gross_amount
        ) AS gross_revenue,

        SUM(
            b.discount_amount
        ) AS discount_amount,

        SUM(
            b.net_amount
        ) AS net_revenue,

        SUM(
            b.insurance_amount
        ) AS insurance_receivable,

        SUM(
            b.patient_amount
        ) AS patient_responsibility,

        SUM(
            b.paid_amount
        ) AS collected_amount,

        SUM(
            b.outstanding_amount
        ) AS outstanding_amount,

        AVG(
            b.net_amount
        ) AS average_bill

    FROM warehouse.fact_billing b

    INNER JOIN warehouse.fact_admission a
        ON a.admission_key =
           b.admission_key

    INNER JOIN warehouse.dim_department dep
        ON dep.department_key =
           a.department_key

    GROUP BY
        dep.department_key,
        dep.department_id,
        dep.department_name
),

hospital AS (
    SELECT
        SUM(
            net_revenue
        ) AS hospital_net_revenue,

        SUM(
            outstanding_amount
        ) AS hospital_outstanding

    FROM department_finance
)

SELECT
    d.department_key,
    d.department_id,
    d.department_name,
    d.bills,
    d.billed_patients,

    ROUND(
        d.gross_revenue::numeric,
        2
    ) AS gross_revenue,

    ROUND(
        d.discount_amount::numeric,
        2
    ) AS discount_amount,

    ROUND(
        (
            100.0
            * d.discount_amount
            / NULLIF(
                d.gross_revenue,
                0
            )
        )::numeric,
        2
    ) AS discount_rate_pct,

    ROUND(
        d.net_revenue::numeric,
        2
    ) AS net_revenue,

    ROUND(
        d.insurance_receivable::numeric,
        2
    ) AS insurance_receivable,

    ROUND(
        d.patient_responsibility::numeric,
        2
    ) AS patient_responsibility,

    ROUND(
        d.collected_amount::numeric,
        2
    ) AS collected_amount,

    ROUND(
        d.outstanding_amount::numeric,
        2
    ) AS outstanding_amount,

    ROUND(
        (
            100.0
            * d.collected_amount
            / NULLIF(
                d.net_revenue,
                0
            )
        )::numeric,
        2
    ) AS collection_efficiency_pct,

    ROUND(
        (
            100.0
            * d.outstanding_amount
            / NULLIF(
                d.net_revenue,
                0
            )
        )::numeric,
        2
    ) AS outstanding_rate_pct,

    ROUND(
        d.average_bill::numeric,
        2
    ) AS average_bill,

    ROUND(
        (
            100.0
            * d.net_revenue
            / NULLIF(
                h.hospital_net_revenue,
                0
            )
        )::numeric,
        2
    ) AS revenue_share_pct,

    ROUND(
        (
            100.0
            * d.outstanding_amount
            / NULLIF(
                h.hospital_outstanding,
                0
            )
        )::numeric,
        2
    ) AS outstanding_share_pct,

    DENSE_RANK() OVER (
        ORDER BY
            d.net_revenue DESC
    ) AS revenue_rank,

    DENSE_RANK() OVER (
        ORDER BY
            d.outstanding_amount DESC
    ) AS outstanding_rank

FROM department_finance d

CROSS JOIN hospital h

ORDER BY
    revenue_rank,
    d.department_name;


-- ============================================================
-- 4. PAYER MIX
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_cfo_payer_mix AS

WITH payer AS (
    SELECT
        CASE
            WHEN p.insurance_status = 'Insured'
                THEN 'Insured'
            ELSE 'Self Pay'
        END AS payer_group,

        COUNT(*) AS bills,

        COUNT(
            DISTINCT b.patient_key
        ) AS billed_patients,

        SUM(
            b.net_amount
        ) AS net_revenue,

        SUM(
            b.insurance_amount
        ) AS insurance_amount,

        SUM(
            b.patient_amount
        ) AS patient_amount,

        SUM(
            b.paid_amount
        ) AS collected_amount,

        SUM(
            b.outstanding_amount
        ) AS outstanding_amount

    FROM warehouse.fact_billing b

    INNER JOIN warehouse.dim_patient p
        ON p.patient_key =
           b.patient_key

    GROUP BY
        CASE
            WHEN p.insurance_status = 'Insured'
                THEN 'Insured'
            ELSE 'Self Pay'
        END
),

totals AS (
    SELECT
        SUM(
            net_revenue
        ) AS total_net_revenue

    FROM payer
)

SELECT
    p.payer_group,
    p.bills,
    p.billed_patients,

    ROUND(
        p.net_revenue::numeric,
        2
    ) AS net_revenue,

    ROUND(
        (
            100.0
            * p.net_revenue
            / NULLIF(
                t.total_net_revenue,
                0
            )
        )::numeric,
        2
    ) AS revenue_mix_pct,

    ROUND(
        p.insurance_amount::numeric,
        2
    ) AS insurance_amount,

    ROUND(
        p.patient_amount::numeric,
        2
    ) AS patient_amount,

    ROUND(
        p.collected_amount::numeric,
        2
    ) AS collected_amount,

    ROUND(
        p.outstanding_amount::numeric,
        2
    ) AS outstanding_amount,

    ROUND(
        (
            100.0
            * p.collected_amount
            / NULLIF(
                p.net_revenue,
                0
            )
        )::numeric,
        2
    ) AS collection_efficiency_pct,

    ROUND(
        (
            100.0
            * p.outstanding_amount
            / NULLIF(
                p.net_revenue,
                0
            )
        )::numeric,
        2
    ) AS outstanding_rate_pct

FROM payer p

CROSS JOIN totals t

ORDER BY
    p.net_revenue DESC;


-- ============================================================
-- 5. PAYMENT METHOD MIX
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_cfo_payment_method_mix AS

WITH payment AS (
    SELECT
        COALESCE(
            payment_method,
            'Unknown'
        ) AS payment_method,

        COUNT(*) AS bills,

        SUM(
            net_amount
        ) AS net_revenue,

        SUM(
            paid_amount
        ) AS collected_amount,

        SUM(
            outstanding_amount
        ) AS outstanding_amount

    FROM warehouse.fact_billing

    GROUP BY
        COALESCE(
            payment_method,
            'Unknown'
        )
),

totals AS (
    SELECT
        SUM(
            collected_amount
        ) AS total_collected

    FROM payment
)

SELECT
    p.payment_method,
    p.bills,

    ROUND(
        p.net_revenue::numeric,
        2
    ) AS net_revenue,

    ROUND(
        p.collected_amount::numeric,
        2
    ) AS collected_amount,

    ROUND(
        p.outstanding_amount::numeric,
        2
    ) AS outstanding_amount,

    ROUND(
        (
            100.0
            * p.collected_amount
            / NULLIF(
                t.total_collected,
                0
            )
        )::numeric,
        2
    ) AS collection_mix_pct,

    ROUND(
        (
            100.0
            * p.collected_amount
            / NULLIF(
                p.net_revenue,
                0
            )
        )::numeric,
        2
    ) AS collection_efficiency_pct

FROM payment p

CROSS JOIN totals t

ORDER BY
    p.collected_amount DESC;


-- ============================================================
-- 6. RECEIVABLE EXPOSURE
--
-- This is exposure segmentation, not true AR ageing because
-- the current fact table does not contain payment due dates.
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_cfo_receivable_exposure AS

WITH exposure AS (
    SELECT
        CASE
            WHEN outstanding_amount = 0
                THEN 'No Outstanding'

            WHEN outstanding_amount < 10000
                THEN 'Below 10K'

            WHEN outstanding_amount < 25000
                THEN '10K-25K'

            WHEN outstanding_amount < 50000
                THEN '25K-50K'

            ELSE '50K+'
        END AS exposure_band,

        CASE
            WHEN outstanding_amount = 0
                THEN 1

            WHEN outstanding_amount < 10000
                THEN 2

            WHEN outstanding_amount < 25000
                THEN 3

            WHEN outstanding_amount < 50000
                THEN 4

            ELSE 5
        END AS exposure_order,

        COUNT(*) AS bills,

        COUNT(
            DISTINCT patient_key
        ) AS patients,

        SUM(
            net_amount
        ) AS net_revenue,

        SUM(
            paid_amount
        ) AS collected_amount,

        SUM(
            outstanding_amount
        ) AS outstanding_amount,

        AVG(
            outstanding_amount
        ) AS average_outstanding

    FROM warehouse.fact_billing

    GROUP BY
        exposure_band,
        exposure_order
),

totals AS (
    SELECT
        SUM(
            outstanding_amount
        ) AS total_outstanding

    FROM exposure
)

SELECT
    e.exposure_band,
    e.exposure_order,
    e.bills,
    e.patients,

    ROUND(
        e.net_revenue::numeric,
        2
    ) AS net_revenue,

    ROUND(
        e.collected_amount::numeric,
        2
    ) AS collected_amount,

    ROUND(
        e.outstanding_amount::numeric,
        2
    ) AS outstanding_amount,

    ROUND(
        e.average_outstanding::numeric,
        2
    ) AS average_outstanding,

    ROUND(
        (
            100.0
            * e.outstanding_amount
            / NULLIF(
                t.total_outstanding,
                0
            )
        )::numeric,
        2
    ) AS outstanding_share_pct

FROM exposure e

CROSS JOIN totals t

ORDER BY
    e.exposure_order;


-- ============================================================
-- 7. CLAIM FINANCIAL EXPOSURE BY INSURER
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_cfo_insurer_exposure AS

WITH insurer AS (
    SELECT
        i.insurer_key,
        i.insurer_id,
        i.insurer_name,

        COUNT(*) AS total_claims,

        SUM(
            c.claim_amount
        ) AS claim_amount,

        SUM(
            c.approved_amount
        ) AS approved_amount,

        SUM(
            c.rejected_amount
        ) AS rejected_amount,

        COUNT(*) FILTER (
            WHERE c.claim_status = 'Rejected'
        ) AS rejected_claims,

        COUNT(*) FILTER (
            WHERE c.claim_status = 'Pending'
        ) AS pending_claims,

        AVG(
            c.processing_days
        ) AS average_processing_days

    FROM warehouse.fact_claim c

    INNER JOIN warehouse.dim_insurer i
        ON i.insurer_key =
           c.insurer_key

    GROUP BY
        i.insurer_key,
        i.insurer_id,
        i.insurer_name
),

totals AS (
    SELECT
        SUM(
            claim_amount
        ) AS total_claim_amount,

        SUM(
            rejected_amount
        ) AS total_rejected_amount

    FROM insurer
)

SELECT
    i.insurer_key,
    i.insurer_id,
    i.insurer_name,
    i.total_claims,

    ROUND(
        i.claim_amount::numeric,
        2
    ) AS claim_amount,

    ROUND(
        i.approved_amount::numeric,
        2
    ) AS approved_amount,

    ROUND(
        i.rejected_amount::numeric,
        2
    ) AS rejected_amount,

    i.rejected_claims,
    i.pending_claims,

    ROUND(
        (
            100.0
            * i.rejected_claims
            / NULLIF(
                i.total_claims,
                0
            )
        )::numeric,
        2
    ) AS claim_rejection_rate_pct,

    ROUND(
        (
            100.0
            * i.rejected_amount
            / NULLIF(
                i.claim_amount,
                0
            )
        )::numeric,
        2
    ) AS rejected_value_rate_pct,

    ROUND(
        i.average_processing_days::numeric,
        2
    ) AS average_processing_days,

    ROUND(
        (
            100.0
            * i.claim_amount
            / NULLIF(
                t.total_claim_amount,
                0
            )
        )::numeric,
        2
    ) AS claim_value_share_pct,

    ROUND(
        (
            100.0
            * i.rejected_amount
            / NULLIF(
                t.total_rejected_amount,
                0
            )
        )::numeric,
        2
    ) AS rejected_value_share_pct,

    DENSE_RANK() OVER (
        ORDER BY
            i.rejected_amount DESC
    ) AS rejected_value_rank

FROM insurer i

CROSS JOIN totals t

ORDER BY
    rejected_value_rank,
    i.insurer_name;