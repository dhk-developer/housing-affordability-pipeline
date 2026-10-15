-- Staging for the three ONS tables: trimmed text, integer years, numeric values.
-- Markers such as [x] or : become NULL. Only council rows are kept
-- (E06 unitary, E07 district, E08 metropolitan, E09 London borough, W06 Welsh).
DROP TABLE IF EXISTS staging.ons_price, staging.ons_earnings, staging.ons_ratio;

CREATE TABLE staging.ons_price AS
SELECT trim(la_code) AS la_code,
       trim(la_name) AS la_name,
       year::int     AS year,
       CASE WHEN replace(value, ',', '') ~ '^[0-9]+(\.[0-9]+)?$'
            THEN replace(value, ',', '')::numeric END AS value
FROM raw.ons_median_price
WHERE trim(la_code) ~ '^(E0[6-9]|W06)';

CREATE TABLE staging.ons_earnings AS
SELECT trim(la_code) AS la_code,
       trim(la_name) AS la_name,
       year::int     AS year,
       CASE WHEN replace(value, ',', '') ~ '^[0-9]+(\.[0-9]+)?$'
            THEN replace(value, ',', '')::numeric END AS value
FROM raw.ons_median_earnings
WHERE trim(la_code) ~ '^(E0[6-9]|W06)';

CREATE TABLE staging.ons_ratio AS
SELECT trim(la_code) AS la_code,
       trim(la_name) AS la_name,
       year::int     AS year,
       CASE WHEN replace(value, ',', '') ~ '^[0-9]+(\.[0-9]+)?$'
            THEN replace(value, ',', '')::numeric END AS value
FROM raw.ons_ratio
WHERE trim(la_code) ~ '^(E0[6-9]|W06)';

ALTER TABLE staging.ons_price    ADD PRIMARY KEY (la_code, year);
ALTER TABLE staging.ons_earnings ADD PRIMARY KEY (la_code, year);
ALTER TABLE staging.ons_ratio    ADD PRIMARY KEY (la_code, year);