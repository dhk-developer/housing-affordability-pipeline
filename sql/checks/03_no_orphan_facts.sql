-- No fact row points at a missing dimension row.
-- The foreign keys already guarantee this; the check proves it.
SELECT f.transaction_id,
       d.date_key IS NULL     AS missing_date,
       c.council_code IS NULL AS missing_council,
       p.property_key IS NULL AS missing_property
FROM core.fact_sale f
LEFT JOIN core.dim_date d     ON d.date_key = f.date_key
LEFT JOIN core.dim_council c  ON c.council_code = f.council_code
LEFT JOIN core.dim_property p ON p.property_key = f.property_key
WHERE d.date_key IS NULL OR c.council_code IS NULL OR p.property_key IS NULL;