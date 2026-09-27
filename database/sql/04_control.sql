-- ============================================================
-- ETL BATCH CONTROL
-- ============================================================

CREATE TABLE IF NOT EXISTS control.etl_batch
(
    batch_id BIGSERIAL PRIMARY KEY,

    batch_name VARCHAR(150) NOT NULL,

    batch_type VARCHAR(50),

    source_name VARCHAR(150),

    start_time TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    end_time TIMESTAMP,

    status VARCHAR(30)
        NOT NULL DEFAULT 'RUNNING',

    records_received BIGINT DEFAULT 0,

    records_inserted BIGINT DEFAULT 0,

    records_updated BIGINT DEFAULT 0,

    records_rejected BIGINT DEFAULT 0,

    error_message TEXT,

    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- DATA QUALITY LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS control.data_quality_log
(
    quality_log_id BIGSERIAL PRIMARY KEY,

    batch_id BIGINT,

    table_name VARCHAR(150) NOT NULL,

    rule_name VARCHAR(150) NOT NULL,

    rule_type VARCHAR(50),

    records_checked BIGINT DEFAULT 0,

    failed_records BIGINT DEFAULT 0,

    severity VARCHAR(20),

    status VARCHAR(20),

    details TEXT,

    checked_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_quality_batch
        FOREIGN KEY (batch_id)
        REFERENCES control.etl_batch(batch_id)
);


-- ============================================================
-- AUDIT LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS control.audit_log
(
    audit_id BIGSERIAL PRIMARY KEY,

    event_timestamp TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    username VARCHAR(100),

    module VARCHAR(100),

    action VARCHAR(200) NOT NULL,

    entity_type VARCHAR(100),

    entity_id VARCHAR(100),

    status VARCHAR(30),

    details TEXT
);