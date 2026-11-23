-- 04_cohort_retention.sql (SIMULATED) - monthly install cohorts: share still installed and share paying,
-- by month since install (a month = 30 days). Only fully observed cells are kept.
CREATE OR REPLACE TABLE out_cohort_retention AS
WITH base AS (
    SELECT i.merchant_id, i.app, date_trunc('month', i.date_berlin) AS cohort, i.date_berlin,
           CAST(i.uninstall_ts_utc AS DATE) AS uninstall_date, s.paid_start, s.cancel_date
    FROM stg_installs i LEFT JOIN subscriptions s USING (merchant_id, app)
), grid AS (
    SELECT b.*, k.m AS months_since, b.date_berlin + to_days(CAST(30 * k.m + 30 AS INTEGER)) AS check_date
    FROM base b CROSS JOIN range(0, 12) AS k(m)
)
SELECT strftime(cohort, '%Y-%m') AS cohort, months_since, COUNT(*) AS cohort_installs,
       ROUND(AVG(CASE WHEN uninstall_date IS NULL OR uninstall_date > check_date THEN 1 ELSE 0 END), 3) AS still_installed,
       ROUND(AVG(CASE WHEN paid_start IS NOT NULL AND paid_start <= check_date
                       AND (cancel_date IS NULL OR cancel_date > check_date) THEN 1 ELSE 0 END), 3) AS paying_share
FROM grid
GROUP BY ALL
HAVING MAX(check_date) <= DATE '2026-10-31'
ORDER BY cohort, months_since;
