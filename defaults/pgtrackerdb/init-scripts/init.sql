CREATE EXTENSION IF NOT EXISTS timescaledb;

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


CREATE TABLE IF NOT EXISTS pss (
    sample_time TIMESTAMPTZ NOT NULL,
    userid                 BIGINT,               -- User identifier
    dbid                   BIGINT,               -- Database identifier
    toplevel               BOOLEAN,           -- If it's a top-level query
    queryid                BIGINT,            -- Query identifier
    query                  TEXT,              -- Query text
    plans                  BIGINT,            -- Number of plans
    total_plan_time        DOUBLE PRECISION,  -- Total planning time
    min_plan_time          DOUBLE PRECISION,  -- Minimum planning time
    max_plan_time          DOUBLE PRECISION,  -- Maximum planning time
    mean_plan_time         DOUBLE PRECISION,  -- Mean planning time
    stddev_plan_time       DOUBLE PRECISION,  -- Stddev of planning time
    calls                  BIGINT,            -- Total calls
    total_exec_time        DOUBLE PRECISION,  -- Total execution time
    min_exec_time          DOUBLE PRECISION,  -- Minimum execution time
    max_exec_time          DOUBLE PRECISION,  -- Maximum execution time
    mean_exec_time         DOUBLE PRECISION,  -- Mean execution time
    stddev_exec_time       DOUBLE PRECISION,  -- Stddev of execution time
    rows                   BIGINT,            -- Total rows processed
    shared_blks_hit        BIGINT,            -- Shared blocks hit
    shared_blks_read       BIGINT,            -- Shared blocks read
    shared_blks_dirtied    BIGINT,            -- Shared blocks dirtied
    shared_blks_written    BIGINT,            -- Shared blocks written
    local_blks_hit         BIGINT,            -- Local blocks hit
    local_blks_read        BIGINT,            -- Local blocks read
    local_blks_dirtied     BIGINT,            -- Local blocks dirtied
    local_blks_written     BIGINT,            -- Local blocks written
    temp_blks_read         BIGINT,            -- Temp blocks read
    temp_blks_written      BIGINT,            -- Temp blocks written
    blk_read_time          DOUBLE PRECISION,  -- Block read time
    blk_write_time         DOUBLE PRECISION,  -- Block write time
    temp_blk_read_time     DOUBLE PRECISION,  -- Temp block read time
    temp_blk_write_time    DOUBLE PRECISION,  -- Temp block write time
    wal_records            BIGINT,            -- WAL records generated
    wal_fpi                BIGINT,            -- WAL full-page images
    wal_bytes              NUMERIC,           -- WAL bytes generated
    jit_functions          BIGINT,            -- JIT functions count
    jit_generation_time    DOUBLE PRECISION,  -- JIT generation time
    jit_inlining_count     BIGINT,            -- JIT inlining count
    jit_inlining_time      DOUBLE PRECISION,  -- JIT inlining time
    jit_optimization_count BIGINT,            -- JIT optimization count
    jit_optimization_time  DOUBLE PRECISION,  -- JIT optimization time
    jit_emission_count     BIGINT,            -- JIT emission count
    jit_emission_time      DOUBLE PRECISION   -- JIT emission time
);

SELECT create_hypertable('pss', 'sample_time');

CREATE TABLE IF NOT EXISTS db_info (
    id SERIAL ,
    full_version TEXT,
    version TEXT
);

CREATE TABLE IF NOT EXISTS tables (
    id SERIAL ,
    name TEXT,
    oid OID ,
    schema TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tables_on_oid ON tables(oid);


CREATE TABLE IF NOT EXISTS indexes (
    id SERIAL,
    name TEXT,
    oid OID UNIQUE,  -- Ensure each index has a unique OID
    table_oid OID REFERENCES tables(oid),
    schema TEXT,
    definition TEXT
);

CREATE INDEX IF NOT EXISTS idx_indexes_table_oid ON indexes(table_oid);
