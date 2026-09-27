-- ============================================================
-- HOSPITAL 360
-- PHASE 5.2 — CLAIMS ANALYTICS VIEWS
-- ============================================================


CREATE SCHEMA IF NOT EXISTS analytics;


-- ============================================================
-- 1. CLAIMS SUMMARY
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_claims_summary AS

SELECT
    COUNT(*) AS total_claims,

    ROUND(
        SUM(claim_amount)::numeric,
        2
    ) AS total_claim_amount,

    ROUND(
        SUM(approved_amount)::numeric,
        2
    ) AS approved_amount,

    ROUND(
        SUM(rejected_amount)::numeric,
        2
    ) AS rejected_amount,

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
                WHERE LOWER(claim_status) = 'approved'
            )
            / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS approval_rate_pct,

    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE LOWER(claim_status) = 'rejected'
            )
            / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS rejection_rate_pct,

    ROUND(
        AVG(processing_days)::numeric,
        2
    ) AS average_processing_days,

    ROUND(
        AVG(claim_amount)::numeric,
        2
    ) AS average_claim_amount

FROM warehouse.fact_claim;


-- ============================================================
-- 2. MONTHLY CLAIM PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_claim_performance AS

WITH monthly AS (

    SELECT
        DATE_TRUNC(
            'month',
            d.full_date
        )::date AS month_start,

        COUNT(*) AS total_claims,

        ROUND(
            SUM(c.claim_amount)::numeric,
            2
        ) AS claim_amount,

        ROUND(
            SUM(c.approved_amount)::numeric,
            2
        ) AS approved_amount,

        ROUND(
            SUM(c.rejected_amount)::numeric,
            2
        ) AS rejected_amount,

        COUNT(*) FILTER (
            WHERE LOWER(c.claim_status) = 'approved'
        ) AS approved_claims,

        COUNT(*) FILTER (
            WHERE LOWER(c.claim_status) = 'partially approved'
        ) AS partially_approved_claims,

        COUNT(*) FILTER (
            WHERE LOWER(c.claim_status) = 'rejected'
        ) AS rejected_claims,

        COUNT(*) FILTER (
            WHERE LOWER(c.claim_status) = 'pending'
        ) AS pending_claims,

        ROUND(
            AVG(c.processing_days)::numeric,
            2
        ) AS average_processing_days

    FROM warehouse.fact_claim c

    INNER JOIN warehouse.dim_date d
        ON d.date_key =
           c.submission_date_key

    GROUP BY
        DATE_TRUNC(
            'month',
            d.full_date
        )::date
),

windowed AS (

    SELECT
        *,

        LAG(total_claims) OVER (
            ORDER BY month_start
        ) AS previous_month_claims,

        LAG(rejected_claims) OVER (
            ORDER BY month_start
        ) AS previous_month_rejected_claims

    FROM monthly
)

SELECT
    month_start,

    total_claims,

    claim_amount,

    approved_amount,

    rejected_amount,

    approved_claims,

    partially_approved_claims,

    rejected_claims,

    pending_claims,

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

    average_processing_days,

    previous_month_claims,

    previous_month_rejected_claims,

    ROUND(
        (
            100.0
            * (
                rejected_claims
                - previous_month_rejected_claims
            )
            / NULLIF(
                previous_month_rejected_claims,
                0
            )
        )::numeric,
        2
    ) AS rejected_claims_mom_growth_pct

FROM windowed;


-- ============================================================
-- 3. CLAIM STATUS ANALYSIS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_claim_status_analysis AS

SELECT
    claim_status,

    COUNT(*) AS total_claims,

    COUNT(
        DISTINCT patient_key
    ) AS patients,

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

    ROUND(
        AVG(claim_amount)::numeric,
        2
    ) AS average_claim_amount,

    ROUND(
        AVG(processing_days)::numeric,
        2
    ) AS average_processing_days,

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
    ) AS claim_mix_pct

FROM warehouse.fact_claim

GROUP BY
    claim_status;


-- ============================================================
-- 4. CLAIM REJECTION REASONS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_claim_rejection_reasons AS

SELECT
    COALESCE(
        NULLIF(
            TRIM(rejection_reason),
            ''
        ),
        'Unspecified'
    ) AS rejection_reason,

    COUNT(*) AS rejected_claims,

    ROUND(
        SUM(rejected_amount)::numeric,
        2
    ) AS rejected_amount,

    ROUND(
        AVG(rejected_amount)::numeric,
        2
    ) AS average_rejected_amount,

    ROUND(
        AVG(processing_days)::numeric,
        2
    ) AS average_processing_days,

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
    ) AS rejection_mix_pct,

    DENSE_RANK() OVER (
        ORDER BY
            COUNT(*) DESC
    ) AS frequency_rank,

    DENSE_RANK() OVER (
        ORDER BY
            SUM(rejected_amount) DESC
    ) AS rejected_amount_rank

FROM warehouse.fact_claim

WHERE LOWER(claim_status) = 'rejected'

GROUP BY
    COALESCE(
        NULLIF(
            TRIM(rejection_reason),
            ''
        ),
        'Unspecified'
    );


-- ============================================================
-- 5. INSURER CLAIM PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_insurer_claim_performance AS

SELECT
    i.insurer_key,

    i.insurer_id,

    i.insurer_name,

    i.insurer_type,

    i.active_flag,

    COUNT(
        c.claim_key
    ) AS total_claims,

    COUNT(
        DISTINCT c.patient_key
    ) AS patients,

    ROUND(
        COALESCE(
            SUM(c.claim_amount),
            0
        )::numeric,
        2
    ) AS claim_amount,

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
        WHERE LOWER(c.claim_status) = 'partially approved'
    ) AS partially_approved_claims,

    COUNT(c.claim_key) FILTER (
        WHERE LOWER(c.claim_status) = 'rejected'
    ) AS rejected_claims,

    COUNT(c.claim_key) FILTER (
        WHERE LOWER(c.claim_status) = 'pending'
    ) AS pending_claims,

    ROUND(
        (
            100.0
            * COUNT(c.claim_key) FILTER (
                WHERE LOWER(c.claim_status) = 'rejected'
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

    DENSE_RANK() OVER (
        ORDER BY
            COALESCE(
                SUM(c.claim_amount),
                0
            ) DESC
    ) AS claim_value_rank,

    DENSE_RANK() OVER (
        ORDER BY
            COALESCE(
                SUM(c.rejected_amount),
                0
            ) DESC
    ) AS rejected_value_rank

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
-- 6. MONTHLY INSURER CLAIM PERFORMANCE
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_monthly_insurer_claim_performance AS

SELECT
    DATE_TRUNC(
        'month',
        d.full_date
    )::date AS month_start,

    i.insurer_key,

    i.insurer_id,

    i.insurer_name,

    COUNT(*) AS total_claims,

    ROUND(
        SUM(c.claim_amount)::numeric,
        2
    ) AS claim_amount,

    ROUND(
        SUM(c.approved_amount)::numeric,
        2
    ) AS approved_amount,

    ROUND(
        SUM(c.rejected_amount)::numeric,
        2
    ) AS rejected_amount,

    COUNT(*) FILTER (
        WHERE LOWER(c.claim_status) = 'rejected'
    ) AS rejected_claims,

    ROUND(
        (
            100.0
            * COUNT(*) FILTER (
                WHERE LOWER(c.claim_status) = 'rejected'
            )
            / NULLIF(
                COUNT(*),
                0
            )
        )::numeric,
        2
    ) AS rejection_rate_pct,

    ROUND(
        AVG(c.processing_days)::numeric,
        2
    ) AS average_processing_days,

    DENSE_RANK() OVER (
        PARTITION BY
            DATE_TRUNC(
                'month',
                d.full_date
            )::date

        ORDER BY
            SUM(c.claim_amount) DESC
    ) AS monthly_claim_value_rank

FROM warehouse.fact_claim c

INNER JOIN warehouse.dim_insurer i
    ON i.insurer_key =
       c.insurer_key

INNER JOIN warehouse.dim_date d
    ON d.date_key =
       c.submission_date_key

GROUP BY
    DATE_TRUNC(
        'month',
        d.full_date
    )::date,

    i.insurer_key,
    i.insurer_id,
    i.insurer_name;


-- ============================================================
-- 7. CLAIM PROCESSING BANDS
-- ============================================================

CREATE OR REPLACE VIEW analytics.vw_claim_processing_bands AS

WITH classified AS (

    SELECT
        CASE

            WHEN processing_days IS NULL
                THEN 'Pending / Unknown'

            WHEN processing_days <= 3
                THEN '0-3 Days'

            WHEN processing_days <= 7
                THEN '4-7 Days'

            WHEN processing_days <= 14
                THEN '8-14 Days'

            WHEN processing_days <= 30
                THEN '15-30 Days'

            ELSE '31+ Days'

        END AS processing_band,

        CASE

            WHEN processing_days IS NULL
                THEN 6

            WHEN processing_days <= 3
                THEN 1

            WHEN processing_days <= 7
                THEN 2

            WHEN processing_days <= 14
                THEN 3

            WHEN processing_days <= 30
                THEN 4

            ELSE 5

        END AS band_order,

        claim_amount,

        approved_amount,

        rejected_amount

    FROM warehouse.fact_claim
)

SELECT
    processing_band,

    band_order,

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
    ) AS claim_mix_pct

FROM classified

GROUP BY
    processing_band,
    band_order;


-- ============================================================
-- DOCUMENTATION
-- ============================================================

COMMENT ON VIEW analytics.vw_claims_summary IS
'Enterprise insurance claims KPI summary.';

COMMENT ON VIEW analytics.vw_monthly_claim_performance IS
'Monthly claim volume, value, rejection and processing trends.';

COMMENT ON VIEW analytics.vw_claim_status_analysis IS
'Claims summarized by claim status.';

COMMENT ON VIEW analytics.vw_claim_rejection_reasons IS
'Rejected claims summarized and ranked by rejection reason.';

COMMENT ON VIEW analytics.vw_insurer_claim_performance IS
'Insurer-level claim value, rejection and processing performance.';

COMMENT ON VIEW analytics.vw_monthly_insurer_claim_performance IS
'Monthly insurer claim performance using claim submission date.';

COMMENT ON VIEW analytics.vw_claim_processing_bands IS
'Claim distribution across processing-time bands.';