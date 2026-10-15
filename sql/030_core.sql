-- Core: a star schema. fact_sale in the middle, dimensions around it.
-- Facts are dropped before the dimensions they point at.
DROP TABLE IF EXISTS core.fact_sale, core.fact_earnings, core.dim_property, core.dim_date, core.dim_council;

-- One row per day.
CREATE TABLE core.dim_date AS
SELECT to_char(d, 'YYYYMMDD')::int                            AS date_key,
       d::date                                                AS date,
       extract(year FROM d)::int                              AS year,
       extract(quarter FROM d)::int                           AS quarter,
       extract(month FROM d)::int                             AS month,
       date_trunc('month', d)::date                           AS month_start,
       extract(year FROM d + interval '3 months')::int        AS ons_year
FROM generate_series('2018-01-01'::date, '2024-12-31'::date, interval '1 day') AS d;
ALTER TABLE core.dim_date ADD PRIMARY KEY (date_key);

-- One row per council, today's boundaries.
CREATE TABLE core.dim_council AS
SELECT DISTINCT la_code AS council_code, la_name AS council_name
FROM staging.ons_ratio;
ALTER TABLE core.dim_council ADD PRIMARY KEY (council_code);

-- One row per combination of property type, new build and tenure that occurs.
CREATE TABLE core.dim_property (
    property_key  int GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    property_type char(1) NOT NULL,
    type_label    text    NOT NULL,
    new_build     boolean NOT NULL,
    tenure        char(1),
    UNIQUE NULLS NOT DISTINCT (property_type, new_build, tenure)
);

INSERT INTO core.dim_property (property_type, type_label, new_build, tenure)
SELECT DISTINCT property_type,
       CASE property_type WHEN 'D' THEN 'Detached' WHEN 'S' THEN 'Semi-detached'
                          WHEN 'T' THEN 'Terraced' WHEN 'F' THEN 'Flat' ELSE 'Other' END,
       new_build,
       tenure
FROM staging.sales;

-- One row per sale.
CREATE TABLE core.fact_sale (
    transaction_id text    PRIMARY KEY,
    date_key       int     NOT NULL REFERENCES core.dim_date,
    council_code   text    NOT NULL REFERENCES core.dim_council,
    property_key   int     NOT NULL REFERENCES core.dim_property,
    price          integer NOT NULL,
    is_outlier     boolean NOT NULL
);

INSERT INTO core.fact_sale (transaction_id, date_key, council_code, property_key, price, is_outlier)
SELECT s.transaction_id,
       to_char(s.sale_date, 'YYYYMMDD')::int,
       s.council_code,
       p.property_key,
       s.price,
       s.is_outlier
FROM staging.sales s
JOIN core.dim_property p
  ON p.property_type = s.property_type
 AND p.new_build = s.new_build
 AND p.tenure IS NOT DISTINCT FROM s.tenure;

-- One row per council per ONS year.
CREATE TABLE core.fact_earnings (
    council_code    text    NOT NULL REFERENCES core.dim_council,
    year            integer NOT NULL,
    median_earnings numeric,
    PRIMARY KEY (council_code, year)
);

INSERT INTO core.fact_earnings (council_code, year, median_earnings)
SELECT la_code, year, value
FROM staging.ons_earnings
WHERE la_code IN (SELECT council_code FROM core.dim_council);

CREATE INDEX ON core.fact_sale (council_code, date_key);
ANALYZE core.fact_sale;