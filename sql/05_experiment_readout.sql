-- 05_experiment_readout.sql (SIMULATED) - standard read-outs read from the main tables
-- EXP03: French + Italian listing for APP_B. Treated FR+IT, controls ES+NL+PL (no translation).
-- pre = 2025-12-02..2026-03-01 (90 days, after BFCM), post = 2026-03-02..2026-06-30 (121 days).
-- 95% CI of the DiD ratio on the log scale: exp(ln r +/- 1.96 sqrt(sum 1/count)) (Poisson counts).
CREATE OR REPLACE TABLE out_exp03_did AS
WITH units AS (
    SELECT 'installs' AS metric, CASE WHEN country IN ('FR', 'IT') THEN 'treated' ELSE 'control' END AS grp,
           CASE WHEN date_berlin < DATE '2026-03-02' THEN 'pre' ELSE 'post' END AS period, COUNT(*) AS n
    FROM stg_installs
    WHERE app = 'APP_B' AND country IN ('FR', 'IT', 'ES', 'NL', 'PL') AND date_berlin BETWEEN DATE '2025-12-02' AND DATE '2026-06-30'
    GROUP BY ALL
    UNION ALL
    SELECT 'listing_views', CASE WHEN country IN ('FR', 'IT') THEN 'treated' ELSE 'control' END,
           CASE WHEN date < DATE '2026-03-02' THEN 'pre' ELSE 'post' END, SUM(listing_views)
    FROM listing_traffic
    WHERE app = 'APP_B' AND country IN ('FR', 'IT', 'ES', 'NL', 'PL') AND date BETWEEN DATE '2025-12-02' AND DATE '2026-06-30'
    GROUP BY ALL
), wide AS (
    SELECT metric,
           SUM(n) FILTER (WHERE grp = 'treated' AND period = 'pre')  AS t_pre,
           SUM(n) FILTER (WHERE grp = 'treated' AND period = 'post') AS t_post,
           SUM(n) FILTER (WHERE grp = 'control' AND period = 'pre')  AS c_pre,
           SUM(n) FILTER (WHERE grp = 'control' AND period = 'post') AS c_post
    FROM units GROUP BY ALL
)
SELECT metric, t_pre, t_post, c_pre, c_post,
       ROUND((t_post / 121.0) / (t_pre / 90.0) - 1, 3) AS naive_before_after,
       ROUND((c_post / 121.0) / (c_pre / 90.0) - 1, 3) AS control_change,
       ROUND((t_post / t_pre) / (c_post / c_pre) - 1, 3) AS did_lift,
       ROUND(exp(ln((t_post / t_pre) / (c_post / c_pre)) - 1.96 * sqrt(1.0 / t_pre + 1.0 / t_post + 1.0 / c_pre + 1.0 / c_post)) - 1, 3) AS did_ci_low,
       ROUND(exp(ln((t_post / t_pre) / (c_post / c_pre)) + 1.96 * sqrt(1.0 / t_pre + 1.0 / t_post + 1.0 / c_pre + 1.0 / c_post)) - 1, 3) AS did_ci_high
FROM wide ORDER BY metric;

-- weekly series for the chart (FR+IT vs ES+NL+PL, APP_B installs)
CREATE OR REPLACE TABLE out_exp03_weekly AS
SELECT date_trunc('week', date_berlin) AS week,
       COUNT(*) FILTER (WHERE country IN ('FR', 'IT')) AS treated_fr_it,
       COUNT(*) FILTER (WHERE country IN ('ES', 'NL', 'PL')) AS control_es_nl_pl
FROM stg_installs WHERE app = 'APP_B' GROUP BY ALL ORDER BY 1;

-- EXP04: App Store ads for APP_A (2026-04-06..05-31): quality of ad installs vs other installs in the same weeks
CREATE OR REPLACE TABLE out_exp04_quality AS
SELECT CASE WHEN i.channel = 'app_store_ads' THEN 'App Store ads' ELSE 'Organic + other' END AS cohort,
       COUNT(*) AS installs,
       ROUND(AVG(CASE WHEN i.uninstalled_48h THEN 1 ELSE 0 END), 3) AS uninstall_48h,
       COUNT(s.trial_start) AS trials, COUNT(s.paid_start) AS paying,
       ROUND(COUNT(s.paid_start) / NULLIF(COUNT(s.trial_start), 0), 3) AS trial_to_paid
FROM stg_installs i LEFT JOIN subscriptions s USING (merchant_id, app)
WHERE i.app = 'APP_A' AND i.date_berlin BETWEEN DATE '2026-04-06' AND DATE '2026-05-31'
GROUP BY ALL ORDER BY 1;

-- EXP01: review request at day 2 vs at the first value moment, randomised 2026-02-01..04-30
CREATE OR REPLACE TABLE out_exp01_reviews AS
SELECT r.arm, COUNT(*) AS prompted, SUM(CASE WHEN r.reviewed THEN 1 ELSE 0 END) AS reviews,
       ROUND(AVG(CASE WHEN r.reviewed THEN 1 ELSE 0 END), 4) AS review_rate, ROUND(AVG(r.stars), 2) AS avg_stars
FROM reviews_sim r JOIN stg_installs i USING (merchant_id, app)
WHERE i.date_berlin BETWEEN DATE '2026-02-01' AND DATE '2026-04-30' AND r.arm IN ('day_2', 'value_moment')
GROUP BY ALL ORDER BY 1;
