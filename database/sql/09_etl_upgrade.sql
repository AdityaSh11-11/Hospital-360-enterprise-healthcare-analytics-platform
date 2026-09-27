-- ============================================================
-- HOSPITAL 360
-- PHASE 4 ETL UPGRADE
-- ============================================================


-- ============================================================
-- DOCTOR STAGING
-- ============================================================

CREATE TABLE IF NOT EXISTS staging.stg_doctors
(
    batch_id BIGINT,

    doctor_id VARCHAR(50),

    doctor_name VARCHAR(200),

    gender VARCHAR(50),

    specialization VARCHAR(150),

    department_id VARCHAR(50),

    qualification VARCHAR(200),

    experience_years VARCHAR(50),

    consultation_fee VARCHAR(50),

    joining_date VARCHAR(50),

    employment_status VARCHAR(50),

    loaded_at TIMESTAMP
        NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- LAB STAGING
-- ============================================================

CREATE TABLE IF NOT EXISTS staging.stg_labs
(
    batch_id BIGINT,

    lab_test_id VARCHAR(50),

    patient_id VARCHAR(50),

    admission_id VARCHAR(50),

    doctor_id VARCHAR(50),

    test_date VARCHAR(100),

    test_name VARCHAR(200),

    test_category VARCHAR(150),

    result_value VARCHAR(150),

    result_unit VARCHAR(50),

    result_status VARCHAR(50),

    test_cost VARCHAR(50),

    abnormal_flag VARCHAR(20),

    loaded_at TIMESTAMP
        NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- MEDICATION MASTER STAGING
-- ============================================================

CREATE TABLE IF NOT EXISTS staging.stg_medication_master
(
    batch_id BIGINT,

    medication_id VARCHAR(50),

    medication_name VARCHAR(200),

    medication_category VARCHAR(150),

    manufacturer VARCHAR(200),

    unit_cost VARCHAR(50),

    loaded_at TIMESTAMP
        NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- MEDICATION EVENT STAGING
-- ============================================================

CREATE TABLE IF NOT EXISTS staging.stg_medication_events
(
    batch_id BIGINT,

    medication_event_id VARCHAR(50),

    patient_id VARCHAR(50),

    admission_id VARCHAR(50),

    medication_id VARCHAR(50),

    prescribed_date VARCHAR(100),

    quantity VARCHAR(50),

    unit_price VARCHAR(50),

    total_amount VARCHAR(50),

    loaded_at TIMESTAMP
        NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- REJECTED RECORDS
-- ============================================================

CREATE TABLE IF NOT EXISTS control.rejected_record
(
    rejection_id BIGSERIAL PRIMARY KEY,

    batch_id BIGINT,

    dataset_name VARCHAR(100) NOT NULL,

    record_identifier VARCHAR(100),

    rule_name VARCHAR(150) NOT NULL,

    rejection_reason TEXT NOT NULL,

    record_data JSONB,

    rejected_at TIMESTAMP
        NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_rejected_batch
        FOREIGN KEY (batch_id)
        REFERENCES control.etl_batch(batch_id)
);


CREATE INDEX IF NOT EXISTS idx_rejected_batch
ON control.rejected_record(batch_id);


CREATE INDEX IF NOT EXISTS idx_rejected_dataset
ON control.rejected_record(dataset_name);


-- ============================================================
-- SOURCE BATCH TRACKING
-- ============================================================

ALTER TABLE control.etl_batch
ADD COLUMN IF NOT EXISTS source_batch_id VARCHAR(150);


ALTER TABLE control.etl_batch
ADD COLUMN IF NOT EXISTS business_date DATE;


ALTER TABLE control.etl_batch
ADD COLUMN IF NOT EXISTS duration_seconds NUMERIC(14,2);


ALTER TABLE control.etl_batch
ADD COLUMN IF NOT EXISTS source_path TEXT;


-- Prevent the same source batch being successfully
-- loaded repeatedly.
CREATE UNIQUE INDEX IF NOT EXISTS uq_etl_source_batch
ON control.etl_batch(source_batch_id)
WHERE source_batch_id IS NOT NULL
AND status = 'SUCCESS';