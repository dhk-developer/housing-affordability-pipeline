-- Independent reconciliation: in each year, at least 95% of councils
-- have a median price within 2% of the ONS median.
SELECT ons_year,
       count(*)                                   AS councils,
       count(*) FILTER (WHERE abs(pct_diff) <= 2) AS within_2_pct,
       round(100.0 * count(*) FILTER (WHERE abs(pct_diff) <= 2) / count(*), 1) AS pass_rate
FROM mart.council_year
WHERE pct_diff IS NOT NULL
GROUP BY ons_year
HAVING count(*) FILTER (WHERE abs(pct_diff) <= 2) < 0.95 * count(*);