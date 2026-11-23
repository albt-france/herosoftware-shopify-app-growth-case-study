-- 06_attribution_vs_holdout.sql (SIMULATED) - Google Ads brand: claimed vs incremental conversions
-- Claimed: platform_reported_conversions of the brand campaigns over the 12 months.
-- Incremental share: 4-week geo holdout (EXP05): brand searches in geo cells with ads on (control) vs ads off.
-- incremental share = 1 - rate_off / rate_on ; 95% CI by the delta method on the log ratio.
CREATE OR REPLACE TABLE out_brand_holdout AS
WITH claimed AS (
    SELECT SUM(platform_reported_conversions) AS claimed, SUM(spend_eur) AS spend_eur
    FROM marketing_spend WHERE campaign_id IN ('CMP001', 'CMP002')
), cells AS (
    SELECT MAX(units) FILTER (WHERE arm = 'control') AS n_on, MAX(conversions) FILTER (WHERE arm = 'control') AS x_on,
           MAX(units) FILTER (WHERE arm = 'treatment') AS n_off, MAX(conversions) FILTER (WHERE arm = 'treatment') AS x_off
    FROM experiment_arms WHERE exp_id = 'EXP05'
), est AS (
    SELECT *, (x_off / n_off) / (x_on / n_on) AS ratio,
           sqrt(1.0 / x_off - 1.0 / n_off + 1.0 / x_on - 1.0 / n_on) AS se_log
    FROM cells
)
SELECT c.claimed, ROUND(c.spend_eur, 0) AS spend_eur, e.n_on, e.x_on, e.n_off, e.x_off,
       ROUND(1 - e.ratio, 3) AS incremental_share,
       ROUND(1 - exp(ln(e.ratio) + 1.96 * e.se_log), 3) AS incr_ci_low,
       ROUND(1 - exp(ln(e.ratio) - 1.96 * e.se_log), 3) AS incr_ci_high,
       ROUND(c.claimed * (1 - e.ratio), 0) AS incremental_conversions,
       ROUND(c.spend_eur / c.claimed, 1) AS cost_per_claimed,
       ROUND(c.spend_eur / (c.claimed * (1 - e.ratio)), 1) AS cost_per_incremental
FROM claimed c, est e;
