-- Raw layer: every column as text, exactly as the file has it.
CREATE TABLE IF NOT EXISTS raw.price_paid (
    transaction_id   text,
    price            text,
    date_of_transfer text,
    postcode         text,
    property_type    text,
    old_new          text,
    duration         text,
    paon             text,
    saon             text,
    street           text,
    locality         text,
    town_city        text,
    district         text,
    county           text,
    ppd_category     text,
    record_status    text,
    source_file      text        NOT NULL,
    loaded_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS price_paid_source_file_idx ON raw.price_paid (source_file);