-- 01_staging.sql (SIMULATED) - clean install events before any count.
-- 1) webhook retries: same merchant/app/event less than 10 minutes after the previous one -> duplicate
-- 2) re-install within 24h of an uninstall -> not a new install (and that uninstall is not a churn)
-- 3) UTC -> Europe/Berlin for every reporting date
CREATE OR REPLACE TABLE stg_events AS
WITH ev AS (
    SELECT *, timezone('Europe/Berlin', ts_utc AT TIME ZONE 'UTC') AS ts_berlin
    FROM install_events
), lagged AS (
    SELECT *, LAG(ts_utc) OVER (PARTITION BY merchant_id, app, event ORDER BY ts_utc, event_id) AS prev_same_ts
    FROM ev
), flagged AS (
    SELECT *, COALESCE(ts_utc - prev_same_ts < INTERVAL 10 MINUTE, FALSE) AS is_retry_duplicate
    FROM lagged
), clean AS (
    SELECT *,
           LAG(event)   OVER w AS prev_event,
           LAG(ts_utc)  OVER w AS prev_ts,
           LEAD(event)  OVER w AS next_event,
           LEAD(ts_utc) OVER w AS next_ts
    FROM flagged WHERE NOT is_retry_duplicate
    WINDOW w AS (PARTITION BY merchant_id, app ORDER BY ts_utc, event_id)
)
SELECT event_id, merchant_id, app, ts_utc, ts_berlin, CAST(ts_berlin AS DATE) AS date_berlin,
       CAST(ts_utc AS DATE) AS date_utc, country, source, utm_source, utm_campaign, event,
       COALESCE(event = 'installed' AND prev_event = 'uninstalled' AND ts_utc - prev_ts < INTERVAL 24 HOUR, FALSE) AS is_quick_reinstall,
       COALESCE(event = 'uninstalled' AND next_event = 'installed' AND next_ts - ts_utc < INTERVAL 24 HOUR, FALSE) AS is_followed_by_reinstall
FROM clean;

-- one row per merchant x app: first real install, final uninstall (if any)
CREATE OR REPLACE TABLE stg_installs AS
WITH first_install AS (
    SELECT * FROM stg_events
    WHERE event = 'installed' AND NOT is_quick_reinstall
    QUALIFY ROW_NUMBER() OVER (PARTITION BY merchant_id, app ORDER BY ts_utc) = 1
), last_uninstall AS (
    SELECT merchant_id, app, MAX(ts_utc) AS uninstall_ts_utc
    FROM stg_events WHERE event = 'uninstalled' AND NOT is_followed_by_reinstall
    GROUP BY ALL
)
SELECT f.merchant_id, f.app, f.ts_utc, f.ts_berlin, f.date_berlin, f.date_utc, f.country, f.source,
       f.utm_source, f.utm_campaign, u.uninstall_ts_utc,
       COALESCE(u.uninstall_ts_utc - f.ts_utc < INTERVAL 48 HOUR, FALSE) AS uninstalled_48h,
       CASE WHEN f.country IN ('DE', 'AT', 'CH') THEN 'DACH' ELSE 'non-DACH' END AS region,
       CASE WHEN f.source = 'google_ads' AND f.utm_campaign IN ('CMP001', 'CMP002') THEN 'google_ads_brand'
            WHEN f.source = 'google_ads' THEN 'google_ads_nonbrand' ELSE f.source END AS channel
FROM first_install f LEFT JOIN last_uninstall u USING (merchant_id, app);

-- data-quality summary (feeds docs/data_issues_log.md and the Data quality tab)
CREATE OR REPLACE TABLE out_dq_summary AS
SELECT 1 AS k, 'raw installed events' AS item, COUNT(*) AS n FROM install_events WHERE event = 'installed'
UNION ALL SELECT 2, 'webhook retry duplicates removed', COUNT(*) FROM stg_events WHERE FALSE  -- placeholder row replaced below
UNION ALL SELECT 3, 'quick re-installs (<24h) not counted as new', COUNT(*) FROM stg_events WHERE is_quick_reinstall
UNION ALL SELECT 4, 'net installs (clean, one per merchant x app)', COUNT(*) FROM stg_installs
UNION ALL SELECT 5, 'installs in a different month in UTC vs Berlin', COUNT(*) FROM stg_installs
          WHERE date_trunc('month', date_utc) <> date_trunc('month', date_berlin);
UPDATE out_dq_summary SET n = (SELECT (SELECT COUNT(*) FROM install_events) - (SELECT COUNT(*) FROM stg_events)) WHERE k = 2;

CREATE OR REPLACE TABLE out_dq_daily AS
WITH raw AS (SELECT CAST(ts_utc AS DATE) AS d, COUNT(*) AS raw_installed FROM install_events WHERE event = 'installed' GROUP BY ALL),
     cln AS (SELECT date_utc AS d, COUNT(*) AS clean_installs FROM stg_installs GROUP BY ALL)
SELECT raw.d AS date_utc, raw_installed, COALESCE(clean_installs, 0) AS clean_installs
FROM raw LEFT JOIN cln USING (d)
WHERE raw.d BETWEEN DATE '2026-07-07' AND DATE '2026-07-22' ORDER BY 1;

CREATE OR REPLACE TABLE out_dq_month_shift AS
WITH b AS (SELECT strftime(date_berlin, '%Y-%m') AS month, COUNT(*) AS installs_berlin FROM stg_installs GROUP BY ALL),
     u AS (SELECT strftime(date_utc, '%Y-%m') AS month, COUNT(*) AS installs_utc FROM stg_installs GROUP BY ALL)
SELECT month, installs_berlin, COALESCE(installs_utc, 0) AS installs_utc, installs_berlin - COALESCE(installs_utc, 0) AS diff
FROM b LEFT JOIN u USING (month) ORDER BY 1;
