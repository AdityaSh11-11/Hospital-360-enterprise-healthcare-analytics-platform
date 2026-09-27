-- ============================================================
-- HOSPITAL 360
-- PHASE 4.1
-- STAGING SCHEMA ALIGNMENT
-- ============================================================
--
-- Purpose:
-- Align PostgreSQL staging tables with the CSV schemas produced
-- by the synthetic data engine.
--
-- Staging tables intentionally use permissive data types.
-- Strict type conversion/business validation happens during
-- the ETL transformation and warehouse-loading stages.
-- ============================================================


CREATE SCHEMA IF NOT EXISTS staging;


-- ============================================================
-- 1. DOCTORS
-- ============================================================

DROP TABLE IF EXISTS staging.stg_doctors;

CREATE TABLE staging.stg_doctors
(
    staging_id BIGSERIAL PRIMARY KEY,

    batch_id BIGINT NOT NULL,

    doctor_id VARCHAR(50),
    doctor_name VARCHAR(200),
    gender VARCHAR(30),
    specialization VARCHAR(150),
    department_id VARCHAR(50),
    qualification VARCHAR(150),
    experience_years VARCHAR(50),
    consultation_fee VARCHAR(100),
    joining_date VARCHAR(100),
    employment_status VARCHAR(50),

    loaded_at TIMESTAMPTZ
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 2. PATIENTS
-- ============================================================

DROP TABLE IF EXISTS staging.stg_patients;

CREATE TABLE staging.stg_patients
(
    staging_id BIGSERIAL PRIMARY KEY,

    batch_id BIGINT NOT NULL,

    patient_id VARCHAR(50),
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    gender VARCHAR(30),
    date_of_birth VARCHAR(100),
    blood_group VARCHAR(20),
    city VARCHAR(150),
    state VARCHAR(150),
    insurance_status VARCHAR(50),
    chronic_condition VARCHAR(200),
    registration_date VARCHAR(100),

    loaded_at TIMESTAMPTZ
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 3. ADMISSIONS
-- ============================================================

DROP TABLE IF EXISTS staging.stg_admissions;

CREATE TABLE staging.stg_admissions
(
    staging_id BIGSERIAL PRIMARY KEY,

    batch_id BIGINT NOT NULL,

    admission_id VARCHAR(50),
    patient_id VARCHAR(50),
    doctor_id VARCHAR(50),
    department_id VARCHAR(50),
    diagnosis_code VARCHAR(50),

    admission_timestamp VARCHAR(100),
    discharge_timestamp VARCHAR(100),

    admission_type VARCHAR(50),
    room_type VARCHAR(50),
    bed_number VARCHAR(50),

    length_of_stay VARCHAR(50),

    icu_flag VARCHAR(30),
    readmission_flag VARCHAR(30),
    emergency_flag VARCHAR(30),

    outcome VARCHAR(100),

    loaded_at TIMESTAMPTZ
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 4. BILLING
-- ============================================================

DROP TABLE IF EXISTS staging.stg_billing;

CREATE TABLE staging.stg_billing
(
    staging_id BIGSERIAL PRIMARY KEY,

    batch_id BIGINT NOT NULL,

    bill_id VARCHAR(50),
    admission_id VARCHAR(50),
    patient_id VARCHAR(50),

    billing_date VARCHAR(100),

    room_charge VARCHAR(100),
    doctor_charge VARCHAR(100),
    procedure_charge VARCHAR(100),
    medication_charge VARCHAR(100),
    lab_charge VARCHAR(100),
    other_charge VARCHAR(100),

    gross_amount VARCHAR(100),
    discount_amount VARCHAR(100),
    insurance_amount VARCHAR(100),
    patient_amount VARCHAR(100),
    tax_amount VARCHAR(100),
    net_amount VARCHAR(100),
    paid_amount VARCHAR(100),
    outstanding_amount VARCHAR(100),

    payment_status VARCHAR(50),
    payment_method VARCHAR(50),

    loaded_at TIMESTAMPTZ
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 5. CLAIMS
-- ============================================================

DROP TABLE IF EXISTS staging.stg_claims;

CREATE TABLE staging.stg_claims
(
    staging_id BIGSERIAL PRIMARY KEY,

    batch_id BIGINT NOT NULL,

    claim_id VARCHAR(50),
    bill_id VARCHAR(50),
    patient_id VARCHAR(50),
    insurer_id VARCHAR(50),

    submission_date VARCHAR(100),
    settlement_date VARCHAR(100),

    claim_amount VARCHAR(100),
    approved_amount VARCHAR(100),
    rejected_amount VARCHAR(100),

    claim_status VARCHAR(50),
    rejection_reason VARCHAR(250),
    processing_days VARCHAR(50),

    loaded_at TIMESTAMPTZ
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 6. LABS
-- ============================================================

DROP TABLE IF EXISTS staging.stg_labs;

CREATE TABLE staging.stg_labs
(
    staging_id BIGSERIAL PRIMARY KEY,

    batch_id BIGINT NOT NULL,

    lab_test_id VARCHAR(50),
    patient_id VARCHAR(50),
    admission_id VARCHAR(50),
    doctor_id VARCHAR(50),

    test_date VARCHAR(100),

    test_name VARCHAR(200),
    test_category VARCHAR(150),

    result_value VARCHAR(200),
    result_unit VARCHAR(100),
    result_status VARCHAR(100),

    test_cost VARCHAR(100),
    abnormal_flag VARCHAR(30),

    loaded_at TIMESTAMPTZ
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 7. MEDICATION MASTER
-- ============================================================

DROP TABLE IF EXISTS staging.stg_medication_master;

CREATE TABLE staging.stg_medication_master
(
    staging_id BIGSERIAL PRIMARY KEY,

    batch_id BIGINT NOT NULL,

    medication_id VARCHAR(50),
    medication_name VARCHAR(200),
    medication_category VARCHAR(150),
    manufacturer VARCHAR(200),
    unit_cost VARCHAR(100),

    loaded_at TIMESTAMPTZ
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- 8. MEDICATION EVENTS
-- ============================================================

DROP TABLE IF EXISTS staging.stg_medication_events;

CREATE TABLE staging.stg_medication_events
(
    staging_id BIGSERIAL PRIMARY KEY,

    batch_id BIGINT NOT NULL,

    medication_event_id VARCHAR(50),
    patient_id VARCHAR(50),
    admission_id VARCHAR(50),
    medication_id VARCHAR(50),

    prescribed_date VARCHAR(100),

    quantity VARCHAR(50),
    unit_price VARCHAR(100),
    total_amount VARCHAR(100),

    loaded_at TIMESTAMPTZ
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_stg_doctors_batch
    ON staging.stg_doctors(batch_id);

CREATE INDEX idx_stg_patients_batch
    ON staging.stg_patients(batch_id);

CREATE INDEX idx_stg_admissions_batch
    ON staging.stg_admissions(batch_id);

CREATE INDEX idx_stg_billing_batch
    ON staging.stg_billing(batch_id);

CREATE INDEX idx_stg_claims_batch
    ON staging.stg_claims(batch_id);

CREATE INDEX idx_stg_labs_batch
    ON staging.stg_labs(batch_id);

CREATE INDEX idx_stg_medication_master_batch
    ON staging.stg_medication_master(batch_id);

CREATE INDEX idx_stg_medication_events_batch
    ON staging.stg_medication_events(batch_id);


CREATE INDEX idx_stg_admissions_patient
    ON staging.stg_admissions(patient_id);

CREATE INDEX idx_stg_admissions_doctor
    ON staging.stg_admissions(doctor_id);

CREATE INDEX idx_stg_billing_admission
    ON staging.stg_billing(admission_id);

CREATE INDEX idx_stg_claims_bill
    ON staging.stg_claims(bill_id);

CREATE INDEX idx_stg_labs_admission
    ON staging.stg_labs(admission_id);

CREATE INDEX idx_stg_medication_events_admission
    ON staging.stg_medication_events(admission_id);


-- ============================================================
-- COMMENTS
-- ============================================================

COMMENT ON SCHEMA staging IS
'Raw landing/staging layer for Hospital 360 ETL.';

COMMENT ON TABLE staging.stg_admissions IS
'Raw admission records before warehouse transformation.';

COMMENT ON COLUMN staging.stg_admissions.length_of_stay IS
'Raw LOS value supplied by the synthetic source generator.';