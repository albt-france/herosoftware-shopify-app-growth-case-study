-- 99_tests.sql - assertions. run_sql.py stops with an error if any 'passed' is false.
CREATE OR REPLACE TABLE out_tests AS
SELECT 'no duplicate merchant x app after cleaning' AS test,
       (SELECT COUNT(*) = COUNT(DISTINCT merchant_id || app) FROM stg_installs) AS passed
UNION ALL SELECT 'no retry duplicate left in stg_events',
       (SELECT COUNT(*) = 0 FROM (SELECT ts_utc - LAG(ts_utc) OVER (PARTITION BY merchant_id, app, event ORDER BY ts_utc) AS g
                                   FROM stg_events) WHERE g < INTERVAL 10 MINUTE)
UNION ALL SELECT '514 public reviews, unique ids', (SELECT COUNT(*) = 514 AND COUNT(DISTINCT review_id) = 514 FROM reviews_public)
UNION ALL SELECT 'reviews = sum of listing ratingCount', (SELECT (SELECT COUNT(*) FROM reviews_public) = SUM(rating_count) FROM listings)
UNION ALL SELECT 'avg stars per app within 0.05 of listing',
       (SELECT bool_and(abs(r.s - l.rating) <= 0.05) FROM (SELECT handle, AVG(stars) AS s FROM reviews_public GROUP BY ALL) r JOIN listings l USING (handle))
UNION ALL SELECT 'public review table has no shop name / text column',
       (SELECT COUNT(*) = 0 FROM (DESCRIBE reviews_public)
         WHERE regexp_matches(lower(column_name), '(shop|store|text|body|title|author|name)'))
UNION ALL SELECT 'no published country with fewer than 5 reviews', (SELECT MIN(reviews) >= 5 FROM out_reviews_country)
UNION ALL SELECT 'installs >= trials >= paying (every channel)',
       (SELECT bool_and(installs >= trials AND trials >= paying) FROM out_channel_scorecard)
UNION ALL SELECT 'funnel views >= installs (every app x surface)', (SELECT bool_and(listing_views >= installs) FROM out_funnel)
UNION ALL SELECT '24 experiments', (SELECT COUNT(*) = 24 FROM experiments)
UNION ALL SELECT 'clean installs never above raw installed events', (SELECT bool_and(raw_installed >= clean_installs) FROM out_dq_daily);
