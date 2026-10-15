-- Staging for sales: typed, checked rows in staging.sales,
-- and every row that fails a rule in staging.sales_rejected with the reason.
DROP TABLE IF EXISTS staging.sales, staging.sales_rejected;

CREATE TABLE staging.sales (
    transaction_id text    PRIMARY KEY,
    price          integer NOT NULL CHECK (price > 0),
    sale_date      date    NOT NULL,
    postcode       text,
    property_type  char(1) NOT NULL CHECK (property_type IN ('D', 'S', 'T', 'F', 'O')),
    new_build      boolean NOT NULL,
    tenure         char(1) CHECK (tenure IN ('F', 'L', 'U')),
    category       char(1) NOT NULL,
    council_code   text    NOT NULL,
    sale_year      integer NOT NULL,
    ons_year       integer NOT NULL,
    is_outlier     boolean NOT NULL,
    source_file    text    NOT NULL
);

CREATE TABLE staging.sales_rejected (
    transaction_id text,
    source_file    text,
    reason         text NOT NULL,
    raw_price      text,
    raw_date       text,
    district       text
);

-- Decide each row's fate once. reject_reason is NULL for rows we keep.
CREATE TEMP TABLE classified ON COMMIT DROP AS
SELECT r.*,
       m.council_code,
       CASE
           WHEN r.price !~ '^[0-9]+$'                              THEN 'bad price'
           WHEN r.price::bigint = 0                                THEN 'zero price'
           WHEN r.price::bigint > 2147483647                       THEN 'price too large'
           WHEN NOT pg_input_is_valid(r.date_of_transfer, 'timestamp') THEN 'bad date'
           WHEN extract(year FROM r.date_of_transfer::timestamp)
                <> substring(r.source_file FROM 'pp-([0-9]{4})')::int THEN 'date outside file year'
           WHEN r.ppd_category <> 'A'                              THEN 'category B'
           WHEN m.council_code IS NULL                             THEN 'unmapped district'
           WHEN m.council_code LIKE 'W%'                           THEN 'Wales'
       END AS reject_reason
FROM raw.price_paid r
LEFT JOIN staging.district_map m ON m.district_name = r.district;

INSERT INTO staging.sales
SELECT transaction_id,
       price::int,
       date_of_transfer::timestamp::date,
       nullif(upper(trim(postcode)), ''),
       property_type,
       old_new = 'Y',
       nullif(duration, ''),
       ppd_category,
       council_code,
       extract(year FROM date_of_transfer::timestamp)::int,
       -- ONS years end in September, so October to December count towards the next year.
       extract(year FROM date_of_transfer::timestamp + interval '3 months')::int,
       price::bigint < 10000 OR price::bigint > 10000000,
       source_file
FROM classified
WHERE reject_reason IS NULL;

INSERT INTO staging.sales_rejected
SELECT transaction_id, source_file, reject_reason, price, date_of_transfer, district
FROM classified
WHERE reject_reason IS NOT NULL;