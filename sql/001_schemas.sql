-- Schemas: one per layer, plus etl for the pipeline's own bookkeeping.
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS core;
CREATE SCHEMA IF NOT EXISTS mart;
CREATE SCHEMA IF NOT EXISTS etl;

CREATE TABLE IF NOT EXISTS etl.run_log (
    log_id        bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    run_id        uuid        NOT NULL,
    step          text        NOT NULL,
    source        text        NOT NULL,
    rows_in       bigint,
    rows_out      bigint,
    rows_rejected bigint,
    started_at    timestamptz NOT NULL,
    finished_at   timestamptz NOT NULL DEFAULT now(),
    status        text        NOT NULL CHECK (status IN ('ok', 'failed')),
    message       text
);