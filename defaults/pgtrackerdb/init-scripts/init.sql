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
    started_at TIMESTAMP,
    PRIMARY KEY(id, started_at)
) partition by range (started_at);