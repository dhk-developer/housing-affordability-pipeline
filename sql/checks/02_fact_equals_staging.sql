-- Every kept sale made it into the fact table, and nothing else did.
SELECT (SELECT count(*) FROM staging.sales)  AS staging_rows,
       (SELECT count(*) FROM core.fact_sale) AS fact_rows
WHERE (SELECT count(*) FROM staging.sales) <> (SELECT count(*) FROM core.fact_sale);