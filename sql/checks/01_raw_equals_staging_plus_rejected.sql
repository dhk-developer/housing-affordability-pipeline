-- Every raw row is either kept or rejected, for every file.
SELECT r.source_file, r.n AS raw_rows, coalesce(s.n, 0) + coalesce(x.n, 0) AS accounted
FROM (SELECT source_file, count(*) n FROM raw.price_paid GROUP BY 1) r
LEFT JOIN (SELECT source_file, count(*) n FROM staging.sales GROUP BY 1) s USING (source_file)
LEFT JOIN (SELECT source_file, count(*) n FROM staging.sales_rejected GROUP BY 1) x USING (source_file)
WHERE r.n <> coalesce(s.n, 0) + coalesce(x.n, 0);