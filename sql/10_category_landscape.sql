-- 10_category_landscape.sql (PUBLIC DATA) - category pages, default order, logged-out view, observed once on the
-- collection date. The order can be personalised and change daily: it is NOT Shopify's ranking algorithm.
CREATE OR REPLACE TABLE out_category_summary AS
WITH r AS (SELECT *, RANK() OVER (PARTITION BY category ORDER BY total_reviews DESC) AS review_rank FROM categories)
SELECT category, MAX(primary_of) AS herosoftware_app, COUNT(*) AS apps_listed, MAX(n_apps_stated) AS apps_stated,
       MAX(position) FILTER (WHERE is_herosoftware) AS hero_position,
       MAX(review_rank) FILTER (WHERE is_herosoftware) AS hero_review_rank,
       MAX(total_reviews) FILTER (WHERE is_herosoftware) AS hero_reviews,
       COUNT(*) FILTER (WHERE total_reviews >= 50) AS apps_50_plus_reviews,
       MEDIAN(total_reviews) AS median_reviews,
       ROUND(AVG(CASE WHEN free_plan THEN 1 ELSE 0 END) FILTER (WHERE position <= 30), 3) AS free_plan_top30,
       ROUND(AVG(CASE WHEN free_plan THEN 1 ELSE 0 END) FILTER (WHERE position > 30), 3) AS free_plan_rest,
       SUM(CASE WHEN is_ad THEN 1 ELSE 0 END) AS ad_cards,
       MAX(collected) AS collected
FROM r GROUP BY ALL ORDER BY apps_listed DESC;

CREATE OR REPLACE TABLE out_category_top AS
SELECT category, position, handle, name, rating, total_reviews, price_label, free_plan, is_herosoftware
FROM categories
WHERE position <= 5 OR is_herosoftware
ORDER BY category, position;

CREATE OR REPLACE TABLE out_category_scatter AS
SELECT category, position, total_reviews, free_plan, is_herosoftware, handle FROM categories WHERE position <= 60;

CREATE OR REPLACE TABLE out_wayback AS SELECT * FROM wayback ORDER BY handle, snapshot;
CREATE OR REPLACE TABLE out_eurostat AS SELECT * FROM eurostat ORDER BY pct_enterprises_selling_online_b2c DESC NULLS LAST;
