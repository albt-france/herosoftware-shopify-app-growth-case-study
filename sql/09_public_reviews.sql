-- 09_public_reviews.sql (PUBLIC DATA) - public Shopify App Store reviews of the 4 HeroSoftware apps, as observed
-- on the Shopify App Store on the collection date. Columns kept: id, app, date, stars, country, tenure, reply date.
-- No shop name, no review text, no reply text. A review is an indirect signal, not an install.
-- 9 reviews only show an 'Edited <date>': they count in totals but not in the monthly rhythm.
CREATE OR REPLACE TABLE out_reviews_monthly AS
SELECT app, strftime(CAST(review_date AS DATE), '%Y-%m') AS month, COUNT(*) AS reviews
FROM reviews_public WHERE NOT date_is_edited GROUP BY ALL ORDER BY 2, 1;

-- countries with fewer than 5 reviews are grouped into 'Other'
CREATE OR REPLACE TABLE out_reviews_country AS
WITH c AS (SELECT country, COUNT(*) AS n FROM reviews_public GROUP BY ALL)
SELECT CASE WHEN n >= 5 THEN country ELSE 'Other' END AS country, SUM(n) AS reviews,
       ROUND(SUM(n) / (SELECT COUNT(*) FROM reviews_public), 3) AS share
FROM c GROUP BY ALL ORDER BY reviews DESC;

CREATE OR REPLACE TABLE out_reviews_by_app AS
SELECT app, COUNT(*) AS reviews, ROUND(AVG(stars), 3) AS avg_stars,
       ROUND(AVG(CASE WHEN stars = 5 THEN 1 ELSE 0 END), 3) AS share_5_star,
       ROUND(AVG(CASE WHEN country = 'Germany' THEN 1 ELSE 0 END), 3) AS share_germany,
       ROUND(AVG(CASE WHEN country IN ('Germany', 'Austria', 'Switzerland') THEN 1 ELSE 0 END), 3) AS share_dach,
       ROUND(AVG(CASE WHEN reply_date IS NOT NULL THEN 1 ELSE 0 END), 3) AS reply_rate,
       COUNT(*) FILTER (WHERE reply_date = DATE '2026-11-09') AS replies_on_2026_11_09,
       MAX(review_date) FILTER (WHERE NOT date_is_edited) AS last_review,
       COUNT(*) FILTER (WHERE review_date >= DATE '2026-03-01' AND NOT date_is_edited) AS reviews_since_2026_03,
       COUNT(*) FILTER (WHERE strftime(CAST(review_date AS DATE), '%Y-%m') IN ('2025-05', '2025-06') AND NOT date_is_edited) AS reviews_may_jun_2025,
       MAX(n_day) AS max_reviews_one_day
FROM (SELECT *, COUNT(*) OVER (PARTITION BY app, review_date) AS n_day FROM reviews_public)
GROUP BY ALL ORDER BY reviews DESC;

CREATE OR REPLACE TABLE out_reviews_tenure AS
SELECT CASE WHEN tenure_days < 1 THEN 'a) < 1 day' WHEN tenure_days < 7 THEN 'b) 1-6 days'
            WHEN tenure_days < 30 THEN 'c) 7-29 days' WHEN tenure_days < 90 THEN 'd) 1-2 months'
            WHEN tenure_days < 365 THEN 'e) 3-11 months' ELSE 'f) 1 year +' END AS tenure_bucket,
       COUNT(*) AS reviews, ROUND(COUNT(*) / (SELECT COUNT(*) FROM reviews_public), 3) AS share
FROM reviews_public GROUP BY ALL ORDER BY 1;

CREATE OR REPLACE TABLE out_reviews_totals AS
SELECT COUNT(*) AS reviews, COUNT(DISTINCT review_id) AS unique_ids,
       ROUND(AVG(CASE WHEN stars = 5 THEN 1 ELSE 0 END), 3) AS share_5_star,
       ROUND(AVG(CASE WHEN country = 'Germany' THEN 1 ELSE 0 END), 3) AS share_germany,
       ROUND(AVG(CASE WHEN country IN ('Germany', 'Austria', 'Switzerland') THEN 1 ELSE 0 END), 3) AS share_dach,
       ROUND(AVG(CASE WHEN tenure LIKE '% day%' THEN 1 ELSE 0 END), 3) AS share_tenure_in_days,
       ROUND(AVG(CASE WHEN tenure_days < 30 THEN 1 ELSE 0 END), 3) AS share_under_30_days,
       COUNT(*) FILTER (WHERE strftime(CAST(review_date AS DATE), '%Y-%m') IN ('2025-05', '2025-06') AND NOT date_is_edited) AS may_jun_2025,
       COUNT(*) FILTER (WHERE reply_date = DATE '2026-11-09') AS replies_2026_11_09,
       COUNT(*) FILTER (WHERE review_date >= DATE '2026-03-01' AND NOT date_is_edited) AS since_2026_03,
       MAX(collected) AS collected
FROM reviews_public;
