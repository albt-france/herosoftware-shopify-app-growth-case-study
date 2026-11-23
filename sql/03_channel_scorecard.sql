-- 03_channel_scorecard.sql (SIMULATED) - cost per install, CAC per paying merchant, payback, MRR at 60 days
-- MRR in EUR = (mrr_usd + usage_usd) / ECB monthly USD per EUR of the paid-start month.
-- Cohort: installs 2025-11-01 .. 2026-08-31 (Berlin); spend over the same months.
-- The Meta test (CMP006, EXP06) and the LinkedIn BFCM push (CMP005, EXP02) are tests, read in their own read-outs.
CREATE OR REPLACE TABLE out_channel_scorecard AS
WITH spend AS (
    SELECT CASE WHEN campaign_id IN ('CMP001', 'CMP002') THEN 'google_ads_brand'
                WHEN campaign_id = 'CMP003' THEN 'google_ads_nonbrand'
                ELSE channel END AS channel,
           SUM(spend_eur) AS spend_eur, SUM(platform_reported_conversions) AS platform_conversions
    FROM marketing_spend
    WHERE date <= DATE '2026-08-31' AND campaign_id NOT IN ('CMP005', 'CMP006')
    GROUP BY ALL
), cohort AS (
    SELECT i.channel, i.merchant_id, i.app, i.date_berlin, i.uninstalled_48h, s.trial_start, s.paid_start, s.cancel_date,
           (COALESCE(s.mrr_usd, 0) + COALESCE(s.usage_usd, 0)) / COALESCE(f.usd_per_eur, 1.15) AS mrr_eur
    FROM stg_installs i
    LEFT JOIN subscriptions s USING (merchant_id, app)
    LEFT JOIN fx f ON f.month = strftime(COALESCE(s.paid_start, i.date_berlin), '%Y-%m')
    WHERE i.date_berlin <= DATE '2026-08-31'
), agg AS (
    SELECT channel, COUNT(*) AS installs,
           AVG(CASE WHEN uninstalled_48h THEN 1 ELSE 0 END) AS uninstall_48h_rate,
           COUNT(trial_start) AS trials, COUNT(paid_start) AS paying,
           SUM(CASE WHEN paid_start IS NOT NULL AND (cancel_date IS NULL OR cancel_date > date_berlin + INTERVAL 60 DAY)
                    THEN mrr_eur ELSE 0 END) AS mrr_eur_d60,
           COUNT(*) FILTER (WHERE paid_start IS NOT NULL AND (cancel_date IS NULL OR cancel_date > date_berlin + INTERVAL 60 DAY)) AS paying_d60
    FROM cohort GROUP BY ALL
)
SELECT a.channel, a.installs, ROUND(a.uninstall_48h_rate, 3) AS uninstall_48h_rate, a.trials, a.paying,
       ROUND(a.paying / NULLIF(a.trials, 0), 3) AS trial_to_paid,
       ROUND(COALESCE(s.spend_eur, 0), 0) AS spend_eur,
       COALESCE(s.platform_conversions, 0) AS platform_conversions,
       ROUND(s.spend_eur / NULLIF(a.installs, 0), 1) AS cost_per_install,
       ROUND(s.spend_eur / NULLIF(a.paying, 0), 0) AS cac_per_paying,
       ROUND(a.mrr_eur_d60 / NULLIF(a.paying_d60, 0), 1) AS mrr_per_paying_d60,
       ROUND((s.spend_eur / NULLIF(a.paying, 0)) / NULLIF(a.mrr_eur_d60 / NULLIF(a.paying_d60, 0), 0), 1) AS payback_months,
       a.paying_d60,
       ROUND(a.paying_d60 / a.installs, 3) AS paying_d60_per_install
FROM agg a LEFT JOIN spend s USING (channel)
ORDER BY spend_eur DESC, installs DESC;
