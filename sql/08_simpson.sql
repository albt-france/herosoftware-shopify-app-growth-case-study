-- 08_simpson.sql (SIMULATED) - trial -> paid of APP_B and APP_D: overall, then by region and country
-- Trials started up to 2026-10-17 (14-day trial fully observed).
CREATE OR REPLACE TABLE out_simpson AS
WITH t AS (
    SELECT i.app, i.region, i.country, s.paid_start IS NOT NULL AS paid
    FROM subscriptions s JOIN stg_installs i USING (merchant_id, app)
    WHERE i.app IN ('APP_B', 'APP_D') AND s.trial_start <= DATE '2026-10-17'
)
SELECT 'overall' AS level, 'all' AS segment, app, COUNT(*) AS trials, ROUND(AVG(paid::INT), 3) AS trial_to_paid FROM t GROUP BY ALL
UNION ALL
SELECT 'region', region, app, COUNT(*), ROUND(AVG(paid::INT), 3) FROM t GROUP BY ALL
UNION ALL
SELECT 'country', country, app, COUNT(*), ROUND(AVG(paid::INT), 3) FROM t
WHERE country IN ('DE', 'AT', 'CH', 'FR', 'IT', 'ES', 'NL', 'US', 'GB') GROUP BY ALL
ORDER BY level DESC, segment, app;

CREATE OR REPLACE TABLE out_simpson_mix AS
SELECT app, ROUND(AVG(CASE WHEN region = 'non-DACH' THEN 1 ELSE 0 END), 3) AS non_dach_share_of_trials
FROM subscriptions s JOIN stg_installs i USING (merchant_id, app)
WHERE app IN ('APP_B', 'APP_D') AND s.trial_start <= DATE '2026-10-17' GROUP BY ALL ORDER BY 1;
