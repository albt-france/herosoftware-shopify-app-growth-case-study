-- 07_bfcm_false_signal.sql (SIMULATED) - a LinkedIn content push promoting APP_A, launched on 2025-11-24 (Black Friday week)
-- naive: APP_A installs per day in launch week (2025-11-24..12-01, 8 days) vs the 2 weeks before (2025-11-10..11-23)
-- DiD: the same change for the apps NOT promoted (APP_B + APP_C), same days and same countries -> same Black Friday wave
CREATE OR REPLACE TABLE out_bfcm AS
SELECT grp,
       COUNT(*) FILTER (WHERE date_berlin BETWEEN DATE '2025-11-10' AND DATE '2025-11-23') AS before_14d,
       COUNT(*) FILTER (WHERE date_berlin BETWEEN DATE '2025-11-24' AND DATE '2025-12-01') AS launch_week_8d,
       ROUND((launch_week_8d / 8.0) / (before_14d / 14.0) - 1, 3) AS change_per_day
FROM (SELECT *, 'APP_A (promoted on LinkedIn)' AS grp FROM stg_installs WHERE app = 'APP_A'
      UNION ALL SELECT *, 'APP_B + APP_C (not promoted)' FROM stg_installs WHERE app IN ('APP_B', 'APP_C')
      UNION ALL SELECT *, 'social channel, all apps' FROM stg_installs WHERE channel = 'social')
GROUP BY ALL ORDER BY grp;

CREATE OR REPLACE TABLE out_bfcm_did AS
WITH s AS (SELECT * FROM out_bfcm WHERE grp LIKE 'APP_A%'), o AS (SELECT * FROM out_bfcm WHERE grp LIKE 'APP_B%')
SELECT s.change_per_day AS naive_lift, o.change_per_day AS not_promoted_change,
       ROUND((s.launch_week_8d / s.before_14d) / (o.launch_week_8d / o.before_14d) - 1, 3) AS did_lift,
       ROUND(exp(ln((s.launch_week_8d / s.before_14d) / (o.launch_week_8d / o.before_14d)) - 1.96 * sqrt(1.0 / s.before_14d + 1.0 / s.launch_week_8d + 1.0 / o.before_14d + 1.0 / o.launch_week_8d)) - 1, 3) AS did_ci_low,
       ROUND(exp(ln((s.launch_week_8d / s.before_14d) / (o.launch_week_8d / o.before_14d)) + 1.96 * sqrt(1.0 / s.before_14d + 1.0 / s.launch_week_8d + 1.0 / o.before_14d + 1.0 / o.launch_week_8d)) - 1, 3) AS did_ci_high
FROM s, o;

-- Black Friday week vs the 2 previous weeks, all apps, by region: the seasonal wave is everywhere
CREATE OR REPLACE TABLE out_bfcm_week AS
SELECT ROUND((COUNT(*) FILTER (WHERE date_berlin BETWEEN DATE '2025-11-24' AND DATE '2025-12-01') / 8.0)
           / (COUNT(*) FILTER (WHERE date_berlin BETWEEN DATE '2025-11-10' AND DATE '2025-11-23') / 14.0) - 1, 3) AS bfcm_week_lift,
       ROUND((COUNT(*) FILTER (WHERE region = 'DACH' AND date_berlin BETWEEN DATE '2025-11-24' AND DATE '2025-12-01') / 8.0)
           / (COUNT(*) FILTER (WHERE region = 'DACH' AND date_berlin BETWEEN DATE '2025-11-10' AND DATE '2025-11-23') / 14.0) - 1, 3) AS bfcm_week_lift_dach,
       ROUND((COUNT(*) FILTER (WHERE region = 'non-DACH' AND date_berlin BETWEEN DATE '2025-11-24' AND DATE '2025-12-01') / 8.0)
           / (COUNT(*) FILTER (WHERE region = 'non-DACH' AND date_berlin BETWEEN DATE '2025-11-10' AND DATE '2025-11-23') / 14.0) - 1, 3) AS bfcm_week_lift_non_dach
FROM stg_installs;

CREATE OR REPLACE TABLE out_daily_installs AS
SELECT date_berlin AS date, app, region, COUNT(*) AS installs FROM stg_installs GROUP BY ALL ORDER BY 1, 2, 3;
