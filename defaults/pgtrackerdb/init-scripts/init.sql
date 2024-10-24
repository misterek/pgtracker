CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS pss (
    id SERIAL ,
    queryid BIGINT,
    calls BIGINT,
    total_time DOUBLE PRECISION,
    rows BIGINT,
    call_diff BIGINT,
    time_diff DOUBLE PRECISION,
    rows_diff BIGINT,
    seconds_elapsed BIGINT,
    calls_per_second DOUBLE PRECISION,
    rows_per_second DOUBLE PRECISION,
    time_per_call DOUBLE PRECISION,
    sample_time TIMESTAMP,
    PRIMARY KEY(id, sample_time)
) partition by range (sample_time);


-- separate these out as it gets bigger
CREATE TABLE IF NOT EXISTS _main_partition  PARTITION OF pss FOR VALUES FROM ('2023-01-01') TO ('2025-07-01');

CREATE TABLE IF NOT EXISTS psa (
    datid BIGINT NULL,
    datname TEXT,
    pid BIGINT,
    usesysid BIGINT NULL,
    usename TEXT,
    application_name TEXT,
    client_addr TEXT,
    client_hostname TEXT,
    client_port INTEGER NULL,
    backend_start TIMESTAMP,
    xact_start TIMESTAMP,
    query_start TIMESTAMP,
    state_change TIMESTAMP,
    wait_event_type TEXT,
    wait_event TEXT,
    state TEXT,
    backend_xid TEXT,
    backend_xmin TEXT,
    query TEXT,
    backend_type TEXT,
    sample_time TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_psa_on_sample_time ON psa(sample_time);


CREATE TABLE IF NOT EXISTS pss_timescale (
    sample_time TIMESTAMPTZ NOT NULL,
    queryid BIGINT,
    calls BIGINT,
    total_time DOUBLE PRECISION,
    rows BIGINT,
    call_diff BIGINT,
    time_diff DOUBLE PRECISION,
    rows_diff BIGINT,
    seconds_elapsed BIGINT,
    calls_per_second DOUBLE PRECISION,
    rows_per_second DOUBLE PRECISION,
    time_per_call DOUBLE PRECISION
);

SELECT create_hypertable('pss_timescale', 'sample_time');