-- Marts: small, ready-to-chart tables built from core.
DROP TABLE IF EXISTS mart.council_year, mart.council_month;

-- One row per council per ONS year: your figures beside the official ones.
CREATE TABLE mart.council_year AS
WITH sales AS (
    SELECT f.council_code,
           d.ons_year,
           count(*)                                              AS sales,
           percentile_cont(0.5) WITHIN GROUP (ORDER BY f.price)  AS median_price,
           avg(p.new_build::int)                                 AS new_build_share
    FROM core.fact_sale f
    JOIN core.dim_date d     ON d.date_key = f.date_key
    JOIN core.dim_property p ON p.property_key = f.property_key
    WHERE d.ons_year BETWEEN 2019 AND 2024   -- complete ONS years only
    GROUP BY 1, 2
)
SELECT s.council_code,
       c.council_name,
       s.ons_year,
       s.sales,
       s.median_price,
       s.new_build_share,
       e.median_earnings,
       s.median_price / nullif(e.median_earnings, 0)                          AS ratio,
       op.value                                                              AS ons_median_price,
       orat.value                                                            AS ons_ratio,
       (s.median_price - op.value) / nullif(op.value, 0) * 100               AS pct_diff,
       s.sales < 300                                                         AS low_volume
FROM sales s
JOIN core.dim_council c          ON c.council_code = s.council_code
LEFT JOIN core.fact_earnings e   ON e.council_code = s.council_code AND e.year = s.ons_year
LEFT JOIN staging.ons_price op   ON op.la_code = s.council_code AND op.year = s.ons_year
LEFT JOIN staging.ons_ratio orat ON orat.la_code = s.council_code AND orat.year = s.ons_year;

ALTER TABLE mart.council_year ADD PRIMARY KEY (council_code, ons_year);

-- One row per council per calendar month, for trend lines.
CREATE TABLE mart.council_month AS
SELECT f.council_code,
       d.month_start,
       extract(year FROM d.month_start)::int                  AS year,
       count(*)                                               AS sales,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY f.price)   AS median_price
FROM core.fact_sale f
JOIN core.dim_date d ON d.date_key = f.date_key
GROUP BY 1, 2;

ALTER TABLE mart.council_month ADD PRIMARY KEY (council_code, month_start);