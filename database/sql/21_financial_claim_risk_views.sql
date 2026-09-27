CREATE SCHEMA IF NOT EXISTS analytics;


-- =====================================================================
-- HOSPITAL 360
-- PHASE 8.2 — FINANCIAL & CLAIMS RISK INTELLIGENCE
--
-- These are transparent analytical exposure indicators.
-- They are NOT credit scores, fraud determinations, or actuarial models.
-- =====================================================================


-- =====================================================================
-- 1. BILL-LEVEL FINANCIAL RISK
--
-- Score:
-- Outstanding > 0                  +15
-- Outstanding >= 10,000            +10
-- Outstanding >= 25,000            +10
-- Outstanding >= 50,000            +15
-- Net amount >= 100,000            +10
-- Payment status not fully paid     +15
-- Claim rejected                    +20
-- Claim pending                     +10
--
-- Maximum possible score = 95
--
-- Bands:
-- 0–24   Low
-- 25–49  Medium
-- 50+    High
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_bill_financial_risk AS

WITH claim_by_bill AS (
    SELECT
        billing_key,

        COUNT(*) AS claim_count,

        ROUND(
            SUM(claim_amount)::numeric,
            2
        ) AS claim_amount,

        ROUND(
            SUM(approved_amount)::numeric,
            2
        ) AS approved_amount,

        ROUND(
            SUM(rejected_amount)::numeric,
            2
        ) AS rejected_amount,

        BOOL_OR(
            claim_status = 'Rejected'
        ) AS rejected_claim_flag,

        BOOL_OR(
            claim_status = 'Pending'
        ) AS pending_claim_flag,

        STRING_AGG(
            DISTINCT claim_status,
            ', '
            ORDER BY claim_status
        ) AS claim_statuses

    FROM warehouse.fact_claim

    GROUP BY
        billing_key
),

base AS (
    SELECT
        b.billing_key,
        b.bill_id,

        b.admission_key,
        a.admission_id,

        b.patient_key,
        p.patient_id,
        p.first_name,
        p.last_name,

        a.department_key,
        dep.department_id,
        dep.department_name,

        a.doctor_key,
        doc.doctor_id,
        doc.doctor_name,

        b.billing_date_key,
        dt.full_date AS billing_date,

        b.gross_amount,
        b.discount_amount,
        b.insurance_amount,
        b.patient_amount,
        b.tax_amount,
        b.net_amount,
        b.paid_amount,
        b.outstanding_amount,

        b.payment_status,
        b.payment_method,

        COALESCE(
            c.claim_count,
            0
        ) AS claim_count,

        COALESCE(
            c.claim_amount,
            0
        ) AS claim_amount,

        COALESCE(
            c.approved_amount,
            0
        ) AS approved_amount,

        COALESCE(
            c.rejected_amount,
            0
        ) AS rejected_amount,

        COALESCE(
            c.rejected_claim_flag,
            FALSE
        ) AS rejected_claim_flag,

        COALESCE(
            c.pending_claim_flag,
            FALSE
        ) AS pending_claim_flag,

        c.claim_statuses

    FROM warehouse.fact_billing b

    INNER JOIN warehouse.fact_admission a
        ON a.admission_key = b.admission_key

    INNER JOIN warehouse.dim_patient p
        ON p.patient_key = b.patient_key

    INNER JOIN warehouse.dim_department dep
        ON dep.department_key = a.department_key

    INNER JOIN warehouse.dim_doctor doc
        ON doc.doctor_key = a.doctor_key

    INNER JOIN warehouse.dim_date dt
        ON dt.date_key = b.billing_date_key

    LEFT JOIN claim_by_bill c
        ON c.billing_key = b.billing_key
),

components AS (
    SELECT
        *,

        CASE
            WHEN outstanding_amount > 0
            THEN 15
            ELSE 0
        END AS outstanding_present_points,

        CASE
            WHEN outstanding_amount >= 10000
            THEN 10
            ELSE 0
        END AS outstanding_10k_points,

        CASE
            WHEN outstanding_amount >= 25000
            THEN 10
            ELSE 0
        END AS outstanding_25k_points,

        CASE
            WHEN outstanding_amount >= 50000
            THEN 15
            ELSE 0
        END AS outstanding_50k_points,

        CASE
            WHEN net_amount >= 100000
            THEN 10
            ELSE 0
        END AS high_bill_points,

        CASE
            WHEN LOWER(
                COALESCE(
                    payment_status,
                    ''
                )
            ) NOT IN (
                'paid',
                'fully paid',
                'completed'
            )
            THEN 15
            ELSE 0
        END AS payment_status_points,

        CASE
            WHEN rejected_claim_flag
            THEN 20
            ELSE 0
        END AS rejected_claim_points,

        CASE
            WHEN pending_claim_flag
            THEN 10
            ELSE 0
        END AS pending_claim_points

    FROM base
),

scored AS (
    SELECT
        *,

        (
            outstanding_present_points
            + outstanding_10k_points
            + outstanding_25k_points
            + outstanding_50k_points
            + high_bill_points
            + payment_status_points
            + rejected_claim_points
            + pending_claim_points
        )::integer AS financial_risk_score

    FROM components
)

SELECT
    *,

    CASE
        WHEN financial_risk_score >= 50
            THEN 'High'

        WHEN financial_risk_score >= 25
            THEN 'Medium'

        ELSE 'Low'
    END AS financial_risk_band,

    CONCAT_WS(
        '; ',

        CASE
            WHEN outstanding_present_points > 0
            THEN 'Outstanding balance'
        END,

        CASE
            WHEN outstanding_10k_points > 0
            THEN 'Outstanding >= 10K'
        END,

        CASE
            WHEN outstanding_25k_points > 0
            THEN 'Outstanding >= 25K'
        END,

        CASE
            WHEN outstanding_50k_points > 0
            THEN 'Outstanding >= 50K'
        END,

        CASE
            WHEN high_bill_points > 0
            THEN 'Net bill >= 100K'
        END,

        CASE
            WHEN payment_status_points > 0
            THEN 'Payment not fully paid'
        END,

        CASE
            WHEN rejected_claim_points > 0
            THEN 'Rejected claim'
        END,

        CASE
            WHEN pending_claim_points > 0
            THEN 'Pending claim'
        END

    ) AS financial_risk_reasons

FROM scored;


-- =====================================================================
-- 2. FINANCIAL RISK BAND SUMMARY
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_financial_risk_band_summary AS

SELECT
    financial_risk_band,

    COUNT(*) AS bills,

    COUNT(
        DISTINCT patient_key
    ) AS patients,

    ROUND(
        AVG(financial_risk_score)::numeric,
        2
    ) AS average_financial_risk_score,

    MIN(financial_risk_score)
        AS minimum_financial_risk_score,

    MAX(financial_risk_score)
        AS maximum_financial_risk_score,

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
        100.0
        * COUNT(*)
        / NULLIF(
            SUM(COUNT(*)) OVER (),
            0
        ),
        2
    ) AS bill_share_pct,

    ROUND(
        100.0
        * SUM(outstanding_amount)
        / NULLIF(
            SUM(
                SUM(outstanding_amount)
            ) OVER (),
            0
        ),
        2
    ) AS outstanding_share_pct

FROM analytics.vw_bill_financial_risk

GROUP BY
    financial_risk_band;


-- =====================================================================
-- 3. DEPARTMENT FINANCIAL RISK
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_department_financial_risk AS

WITH metrics AS (
    SELECT
        department_key,
        department_id,
        department_name,

        COUNT(*) AS bills,

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
            AVG(financial_risk_score)::numeric,
            2
        ) AS average_financial_risk_score,

        COUNT(*) FILTER (
            WHERE financial_risk_band = 'High'
        ) AS high_risk_bills,

        COUNT(*) FILTER (
            WHERE financial_risk_band = 'Medium'
        ) AS medium_risk_bills,

        COUNT(*) FILTER (
            WHERE financial_risk_band = 'Low'
        ) AS low_risk_bills,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE financial_risk_band = 'High'
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS high_risk_bill_rate_pct,

        ROUND(
            100.0
            * SUM(outstanding_amount)
            / NULLIF(
                SUM(net_amount),
                0
            ),
            2
        ) AS outstanding_rate_pct

    FROM analytics.vw_bill_financial_risk

    GROUP BY
        department_key,
        department_id,
        department_name
)

SELECT
    *,

    ROUND(
        100.0
        * outstanding_amount
        / NULLIF(
            SUM(outstanding_amount)
            OVER (),
            0
        ),
        2
    ) AS outstanding_share_pct,

    DENSE_RANK() OVER (
        ORDER BY
            outstanding_amount DESC,
            department_name
    ) AS outstanding_rank,

    DENSE_RANK() OVER (
        ORDER BY
            high_risk_bill_rate_pct DESC,
            average_financial_risk_score DESC,
            department_name
    ) AS financial_risk_rank

FROM metrics;


-- =====================================================================
-- 4. CLAIM-LEVEL RISK
--
-- This is exposure prioritization, not a prediction that a claim
-- will be rejected.
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_claim_risk AS

WITH base AS (
    SELECT
        c.claim_key,
        c.claim_id,

        c.billing_key,
        b.bill_id,

        c.patient_key,
        p.patient_id,

        c.insurer_key,
        i.insurer_id,
        i.insurer_name,

        a.department_key,
        dep.department_id,
        dep.department_name,

        c.claim_amount,
        c.approved_amount,
        c.rejected_amount,

        c.claim_status,
        c.rejection_reason,
        c.processing_days,

        submission.full_date
            AS submission_date,

        settlement.full_date
            AS settlement_date,

        CASE
            WHEN c.claim_status = 'Rejected'
            THEN 30
            ELSE 0
        END AS rejected_status_points,

        CASE
            WHEN c.claim_status = 'Pending'
            THEN 20
            ELSE 0
        END AS pending_status_points,

        CASE
            WHEN c.claim_status = 'Partially Approved'
            THEN 10
            ELSE 0
        END AS partial_approval_points,

        CASE
            WHEN c.rejected_amount >= 25000
            THEN 15
            ELSE 0
        END AS rejected_value_points,

        CASE
            WHEN c.claim_amount >= 100000
            THEN 10
            ELSE 0
        END AS high_claim_value_points,

        CASE
            WHEN COALESCE(
                c.processing_days,
                0
            ) > 30
            THEN 10
            ELSE 0
        END AS long_processing_points

    FROM warehouse.fact_claim c

    INNER JOIN warehouse.fact_billing b
        ON b.billing_key = c.billing_key

    INNER JOIN warehouse.fact_admission a
        ON a.admission_key = b.admission_key

    INNER JOIN warehouse.dim_patient p
        ON p.patient_key = c.patient_key

    INNER JOIN warehouse.dim_insurer i
        ON i.insurer_key = c.insurer_key

    INNER JOIN warehouse.dim_department dep
        ON dep.department_key = a.department_key

    INNER JOIN warehouse.dim_date submission
        ON submission.date_key
         = c.submission_date_key

    LEFT JOIN warehouse.dim_date settlement
        ON settlement.date_key
         = c.settlement_date_key
),

scored AS (
    SELECT
        *,

        (
            rejected_status_points
            + pending_status_points
            + partial_approval_points
            + rejected_value_points
            + high_claim_value_points
            + long_processing_points
        )::integer AS claim_risk_score

    FROM base
)

SELECT
    *,

    CASE
        WHEN claim_risk_score >= 40
            THEN 'High'

        WHEN claim_risk_score >= 20
            THEN 'Medium'

        ELSE 'Low'
    END AS claim_risk_band,

    CONCAT_WS(
        '; ',

        CASE
            WHEN rejected_status_points > 0
            THEN 'Rejected claim'
        END,

        CASE
            WHEN pending_status_points > 0
            THEN 'Pending claim'
        END,

        CASE
            WHEN partial_approval_points > 0
            THEN 'Partially approved'
        END,

        CASE
            WHEN rejected_value_points > 0
            THEN 'Rejected value >= 25K'
        END,

        CASE
            WHEN high_claim_value_points > 0
            THEN 'Claim value >= 100K'
        END,

        CASE
            WHEN long_processing_points > 0
            THEN 'Processing > 30 days'
        END

    ) AS claim_risk_reasons

FROM scored;


-- =====================================================================
-- 5. INSURER CLAIM RISK
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_insurer_claim_risk AS

WITH metrics AS (
    SELECT
        insurer_key,
        insurer_id,
        insurer_name,

        COUNT(*) AS total_claims,

        ROUND(
            SUM(claim_amount)::numeric,
            2
        ) AS claim_amount,

        ROUND(
            SUM(approved_amount)::numeric,
            2
        ) AS approved_amount,

        ROUND(
            SUM(rejected_amount)::numeric,
            2
        ) AS rejected_amount,

        COUNT(*) FILTER (
            WHERE claim_status = 'Rejected'
        ) AS rejected_claims,

        COUNT(*) FILTER (
            WHERE claim_status = 'Pending'
        ) AS pending_claims,

        COUNT(*) FILTER (
            WHERE claim_status = 'Partially Approved'
        ) AS partially_approved_claims,

        COUNT(*) FILTER (
            WHERE claim_risk_band = 'High'
        ) AS high_risk_claims,

        ROUND(
            AVG(claim_risk_score)::numeric,
            2
        ) AS average_claim_risk_score,

        ROUND(
            AVG(processing_days)::numeric,
            2
        ) AS average_processing_days,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE claim_status = 'Rejected'
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS claim_rejection_rate_pct,

        ROUND(
            100.0
            * SUM(rejected_amount)
            / NULLIF(
                SUM(claim_amount),
                0
            ),
            2
        ) AS rejected_value_rate_pct,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE claim_risk_band = 'High'
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS high_risk_claim_rate_pct

    FROM analytics.vw_claim_risk

    GROUP BY
        insurer_key,
        insurer_id,
        insurer_name
)

SELECT
    *,

    ROUND(
        100.0
        * rejected_amount
        / NULLIF(
            SUM(rejected_amount)
            OVER (),
            0
        ),
        2
    ) AS rejected_value_share_pct,

    DENSE_RANK() OVER (
        ORDER BY
            rejected_amount DESC,
            insurer_name
    ) AS rejected_value_rank,

    DENSE_RANK() OVER (
        ORDER BY
            high_risk_claim_rate_pct DESC,
            average_claim_risk_score DESC,
            insurer_name
    ) AS claim_risk_rank

FROM metrics;


-- =====================================================================
-- 6. MONTHLY FINANCIAL RISK TREND
-- Billing-month semantics.
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_financial_risk AS

WITH metrics AS (
    SELECT
        DATE_TRUNC(
            'month',
            billing_date
        )::date AS month_start,

        COUNT(*) AS bills,

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
            AVG(financial_risk_score)::numeric,
            2
        ) AS average_financial_risk_score,

        COUNT(*) FILTER (
            WHERE financial_risk_band = 'High'
        ) AS high_risk_bills,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE financial_risk_band = 'High'
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS high_risk_bill_rate_pct,

        ROUND(
            100.0
            * SUM(outstanding_amount)
            / NULLIF(
                SUM(net_amount),
                0
            ),
            2
        ) AS outstanding_rate_pct

    FROM analytics.vw_bill_financial_risk

    GROUP BY
        DATE_TRUNC(
            'month',
            billing_date
        )::date
)

SELECT
    *,

    ROUND(
        (
            high_risk_bill_rate_pct
            - LAG(
                high_risk_bill_rate_pct
            ) OVER (
                ORDER BY month_start
            )
        )::numeric,
        2
    ) AS high_risk_bill_rate_mom_change_pp,

    ROUND(
        (
            outstanding_rate_pct
            - LAG(
                outstanding_rate_pct
            ) OVER (
                ORDER BY month_start
            )
        )::numeric,
        2
    ) AS outstanding_rate_mom_change_pp

FROM metrics;


-- =====================================================================
-- 7. MONTHLY CLAIM RISK TREND
-- Submission-month semantics.
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_claim_risk AS

WITH metrics AS (
    SELECT
        DATE_TRUNC(
            'month',
            submission_date
        )::date AS month_start,

        COUNT(*) AS total_claims,

        ROUND(
            SUM(claim_amount)::numeric,
            2
        ) AS claim_amount,

        ROUND(
            SUM(rejected_amount)::numeric,
            2
        ) AS rejected_amount,

        COUNT(*) FILTER (
            WHERE claim_risk_band = 'High'
        ) AS high_risk_claims,

        ROUND(
            AVG(claim_risk_score)::numeric,
            2
        ) AS average_claim_risk_score,

        ROUND(
            100.0
            * COUNT(*) FILTER (
                WHERE claim_risk_band = 'High'
            )
            / NULLIF(
                COUNT(*),
                0
            ),
            2
        ) AS high_risk_claim_rate_pct,

        ROUND(
            100.0
            * SUM(rejected_amount)
            / NULLIF(
                SUM(claim_amount),
                0
            ),
            2
        ) AS rejected_value_rate_pct

    FROM analytics.vw_claim_risk

    GROUP BY
        DATE_TRUNC(
            'month',
            submission_date
        )::date
)

SELECT
    *,

    ROUND(
        (
            high_risk_claim_rate_pct
            - LAG(
                high_risk_claim_rate_pct
            ) OVER (
                ORDER BY month_start
            )
        )::numeric,
        2
    ) AS high_risk_claim_rate_mom_change_pp,

    ROUND(
        (
            rejected_value_rate_pct
            - LAG(
                rejected_value_rate_pct
            ) OVER (
                ORDER BY month_start
            )
        )::numeric,
        2
    ) AS rejected_value_rate_mom_change_pp

FROM metrics;


-- =====================================================================
-- 8. FINANCIAL RISK FACTOR PREVALENCE
-- =====================================================================

CREATE OR REPLACE VIEW analytics.vw_financial_risk_factor_prevalence AS

WITH total AS (
    SELECT
        COUNT(*) AS total_bills

    FROM analytics.vw_bill_financial_risk
),

factors AS (
    SELECT
        'Outstanding balance'::varchar
            AS risk_factor,

        COUNT(*) FILTER (
            WHERE outstanding_present_points > 0
        ) AS triggered_bills

    FROM analytics.vw_bill_financial_risk

    UNION ALL

    SELECT
        'Outstanding >= 10K',

        COUNT(*) FILTER (
            WHERE outstanding_10k_points > 0
        )

    FROM analytics.vw_bill_financial_risk

    UNION ALL

    SELECT
        'Outstanding >= 25K',

        COUNT(*) FILTER (
            WHERE outstanding_25k_points > 0
        )

    FROM analytics.vw_bill_financial_risk

    UNION ALL

    SELECT
        'Outstanding >= 50K',

        COUNT(*) FILTER (
            WHERE outstanding_50k_points > 0
        )

    FROM analytics.vw_bill_financial_risk

    UNION ALL

    SELECT
        'Net bill >= 100K',

        COUNT(*) FILTER (
            WHERE high_bill_points > 0
        )

    FROM analytics.vw_bill_financial_risk

    UNION ALL

    SELECT
        'Payment not fully paid',

        COUNT(*) FILTER (
            WHERE payment_status_points > 0
        )

    FROM analytics.vw_bill_financial_risk

    UNION ALL

    SELECT
        'Rejected claim',

        COUNT(*) FILTER (
            WHERE rejected_claim_points > 0
        )

    FROM analytics.vw_bill_financial_risk

    UNION ALL

    SELECT
        'Pending claim',

        COUNT(*) FILTER (
            WHERE pending_claim_points > 0
        )

    FROM analytics.vw_bill_financial_risk
)

SELECT
    f.risk_factor,
    f.triggered_bills,
    t.total_bills,

    ROUND(
        100.0
        * f.triggered_bills
        / NULLIF(
            t.total_bills,
            0
        ),
        2
    ) AS prevalence_pct

FROM factors f

CROSS JOIN total t;