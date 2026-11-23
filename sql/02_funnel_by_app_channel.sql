-- 02_funnel_by_app_channel.sql (SIMULATED) - listing views -> install -> trial -> paid -> paying at day 60
-- Cohort: installs up to 2026-08-31 (Berlin) so that every install has 60 days of history.
CREATE OR REPLACE TABLE out_funnel AS
WITH views AS (
    SELECT app, surface, SUM(listing_views) AS listing_views
    FROM listing_traffic WHERE date <= DATE '2026-08-31' GROUP BY ALL
), inst AS (
    SELECT i.app, i.source AS surface,
           COUNT(*) AS installs,
           COUNT(*) FILTER (WHERE NOT i.uninstalled_48h) AS installs_kept_48h,
           COUNT(s.trial_start) AS trials,
           COUNT(s.paid_start) AS paid,
           COUNT(*) FILTER (WHERE s.paid_start IS NOT NULL
                              AND (s.cancel_date IS NULL OR s.cancel_date > i.date_berlin + INTERVAL 60 DAY)) AS paying_d60
    FROM stg_installs i LEFT JOIN subscriptions s USING (merchant_id, app)
    WHERE i.date_berlin <= DATE '2026-08-31'
    GROUP BY ALL
)
SELECT v.app, v.surface, v.listing_views, COALESCE(installs, 0) AS installs, COALESCE(installs_kept_48h, 0) AS installs_kept_48h,
       COALESCE(trials, 0) AS trials, COALESCE(paid, 0) AS paid, COALESCE(paying_d60, 0) AS paying_d60,
       ROUND(installs / NULLIF(v.listing_views, 0), 4) AS view_to_install,
       ROUND(paid / NULLIF(trials, 0), 4) AS trial_to_paid
FROM views v LEFT JOIN inst i USING (app, surface)
ORDER BY app, listing_views DESC;

CREATE OR REPLACE TABLE out_funnel_total AS
SELECT 'listing views' AS step, 1 AS k, SUM(listing_views) AS n FROM out_funnel
UNION ALL SELECT 'installs', 2, SUM(installs) FROM out_funnel
UNION ALL SELECT 'kept 48h', 3, SUM(installs_kept_48h) FROM out_funnel
UNION ALL SELECT 'trials', 4, SUM(trials) FROM out_funnel
UNION ALL SELECT 'paying', 5, SUM(paid) FROM out_funnel
UNION ALL SELECT 'paying at day 60', 6, SUM(paying_d60) FROM out_funnel
ORDER BY k;
