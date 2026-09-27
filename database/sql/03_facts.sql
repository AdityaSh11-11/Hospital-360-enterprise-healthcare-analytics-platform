-- ============================================================
-- HOSPITAL 360
-- FACT TABLES
-- ============================================================


-- ============================================================
-- ADMISSIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.fact_admission
(
    admission_key BIGSERIAL PRIMARY KEY,

    admission_id VARCHAR(40) UNIQUE NOT NULL,

    patient_key BIGINT NOT NULL,
    doctor_key BIGINT,
    department_key INTEGER,

    diagnosis_key INTEGER,

    admission_date_key INTEGER NOT NULL,
    discharge_date_key INTEGER,

    admission_timestamp TIMESTAMP NOT NULL,
    discharge_timestamp TIMESTAMP,

    admission_type VARCHAR(30),

    room_type VARCHAR(50),

    bed_number VARCHAR(30),

    length_of_stay INTEGER,

    icu_flag BOOLEAN NOT NULL DEFAULT FALSE,

    readmission_flag BOOLEAN NOT NULL DEFAULT FALSE,

    emergency_flag BOOLEAN NOT NULL DEFAULT FALSE,

    outcome VARCHAR(50),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_admission_patient
        FOREIGN KEY (patient_key)
        REFERENCES warehouse.dim_patient(patient_key),

    CONSTRAINT fk_admission_doctor
        FOREIGN KEY (doctor_key)
        REFERENCES warehouse.dim_doctor(doctor_key),

    CONSTRAINT fk_admission_department
        FOREIGN KEY (department_key)
        REFERENCES warehouse.dim_department(department_key),

    CONSTRAINT fk_admission_diagnosis
        FOREIGN KEY (diagnosis_key)
        REFERENCES warehouse.dim_diagnosis(diagnosis_key),

    CONSTRAINT fk_admission_date
        FOREIGN KEY (admission_date_key)
        REFERENCES warehouse.dim_date(date_key),

    CONSTRAINT fk_discharge_date
        FOREIGN KEY (discharge_date_key)
        REFERENCES warehouse.dim_date(date_key),

    CONSTRAINT chk_length_of_stay
        CHECK (
            length_of_stay IS NULL
            OR length_of_stay >= 0
        )
);


-- ============================================================
-- BILLING
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.fact_billing
(
    billing_key BIGSERIAL PRIMARY KEY,

    bill_id VARCHAR(40) UNIQUE NOT NULL,

    admission_key BIGINT NOT NULL,
    patient_key BIGINT NOT NULL,

    billing_date_key INTEGER NOT NULL,

    room_charge NUMERIC(14,2) DEFAULT 0,
    doctor_charge NUMERIC(14,2) DEFAULT 0,
    procedure_charge NUMERIC(14,2) DEFAULT 0,
    medication_charge NUMERIC(14,2) DEFAULT 0,
    lab_charge NUMERIC(14,2) DEFAULT 0,
    other_charge NUMERIC(14,2) DEFAULT 0,

    gross_amount NUMERIC(14,2) NOT NULL,

    discount_amount NUMERIC(14,2)
        NOT NULL DEFAULT 0,

    insurance_amount NUMERIC(14,2)
        NOT NULL DEFAULT 0,

    patient_amount NUMERIC(14,2)
        NOT NULL DEFAULT 0,

    tax_amount NUMERIC(14,2)
        NOT NULL DEFAULT 0,

    net_amount NUMERIC(14,2) NOT NULL,

    paid_amount NUMERIC(14,2)
        NOT NULL DEFAULT 0,

    outstanding_amount NUMERIC(14,2)
        NOT NULL DEFAULT 0,

    payment_status VARCHAR(30),

    payment_method VARCHAR(50),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_billing_admission
        FOREIGN KEY (admission_key)
        REFERENCES warehouse.fact_admission(admission_key),

    CONSTRAINT fk_billing_patient
        FOREIGN KEY (patient_key)
        REFERENCES warehouse.dim_patient(patient_key),

    CONSTRAINT fk_billing_date
        FOREIGN KEY (billing_date_key)
        REFERENCES warehouse.dim_date(date_key),

    CONSTRAINT chk_gross_amount
        CHECK (gross_amount >= 0),

    CONSTRAINT chk_net_amount
        CHECK (net_amount >= 0)
);


-- ============================================================
-- INSURANCE CLAIM
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.fact_claim
(
    claim_key BIGSERIAL PRIMARY KEY,

    claim_id VARCHAR(40) UNIQUE NOT NULL,

    billing_key BIGINT NOT NULL,

    patient_key BIGINT NOT NULL,

    insurer_key INTEGER NOT NULL,

    submission_date_key INTEGER,

    settlement_date_key INTEGER,

    claim_amount NUMERIC(14,2) NOT NULL,

    approved_amount NUMERIC(14,2)
        NOT NULL DEFAULT 0,

    rejected_amount NUMERIC(14,2)
        NOT NULL DEFAULT 0,

    claim_status VARCHAR(30),

    rejection_reason VARCHAR(250),

    processing_days INTEGER,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_claim_billing
        FOREIGN KEY (billing_key)
        REFERENCES warehouse.fact_billing(billing_key),

    CONSTRAINT fk_claim_patient
        FOREIGN KEY (patient_key)
        REFERENCES warehouse.dim_patient(patient_key),

    CONSTRAINT fk_claim_insurer
        FOREIGN KEY (insurer_key)
        REFERENCES warehouse.dim_insurer(insurer_key),

    CONSTRAINT fk_claim_submission_date
        FOREIGN KEY (submission_date_key)
        REFERENCES warehouse.dim_date(date_key),

    CONSTRAINT fk_claim_settlement_date
        FOREIGN KEY (settlement_date_key)
        REFERENCES warehouse.dim_date(date_key),

    CONSTRAINT chk_claim_amount
        CHECK (claim_amount >= 0),

    CONSTRAINT chk_approved_amount
        CHECK (approved_amount >= 0)
);


-- ============================================================
-- LAB TEST
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.fact_lab_test
(
    lab_test_key BIGSERIAL PRIMARY KEY,

    lab_test_id VARCHAR(40) UNIQUE NOT NULL,

    patient_key BIGINT NOT NULL,

    admission_key BIGINT,

    doctor_key BIGINT,

    test_date_key INTEGER NOT NULL,

    test_name VARCHAR(150) NOT NULL,

    test_category VARCHAR(100),

    result_value VARCHAR(100),

    result_unit VARCHAR(30),

    result_status VARCHAR(30),

    test_cost NUMERIC(12,2),

    abnormal_flag BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_lab_patient
        FOREIGN KEY (patient_key)
        REFERENCES warehouse.dim_patient(patient_key),

    CONSTRAINT fk_lab_admission
        FOREIGN KEY (admission_key)
        REFERENCES warehouse.fact_admission(admission_key),

    CONSTRAINT fk_lab_doctor
        FOREIGN KEY (doctor_key)
        REFERENCES warehouse.dim_doctor(doctor_key),

    CONSTRAINT fk_lab_date
        FOREIGN KEY (test_date_key)
        REFERENCES warehouse.dim_date(date_key)
);


-- ============================================================
-- MEDICATION FACT
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.fact_medication
(
    medication_fact_key BIGSERIAL PRIMARY KEY,

    medication_event_id VARCHAR(40) UNIQUE NOT NULL,

    patient_key BIGINT NOT NULL,

    admission_key BIGINT,

    medication_key INTEGER NOT NULL,

    prescribed_date_key INTEGER NOT NULL,

    quantity INTEGER NOT NULL,

    unit_price NUMERIC(12,2),

    total_amount NUMERIC(14,2),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_med_fact_patient
        FOREIGN KEY (patient_key)
        REFERENCES warehouse.dim_patient(patient_key),

    CONSTRAINT fk_med_fact_admission
        FOREIGN KEY (admission_key)
        REFERENCES warehouse.fact_admission(admission_key),

    CONSTRAINT fk_med_fact_medication
        FOREIGN KEY (medication_key)
        REFERENCES warehouse.dim_medication(medication_key),

    CONSTRAINT fk_med_fact_date
        FOREIGN KEY (prescribed_date_key)
        REFERENCES warehouse.dim_date(date_key),

    CONSTRAINT chk_medication_quantity
        CHECK (quantity > 0)
);