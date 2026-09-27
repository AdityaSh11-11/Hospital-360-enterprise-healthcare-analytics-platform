CREATE TABLE IF NOT EXISTS staging.stg_patients
(
    batch_id BIGINT,

    patient_id VARCHAR(50),

    first_name VARCHAR(150),
    last_name VARCHAR(150),

    gender VARCHAR(50),

    date_of_birth VARCHAR(50),

    blood_group VARCHAR(30),

    city VARCHAR(150),
    state VARCHAR(150),

    insurance_status VARCHAR(50),

    chronic_condition VARCHAR(250),

    registration_date VARCHAR(50),

    loaded_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS staging.stg_admissions
(
    batch_id BIGINT,

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

    icu_flag VARCHAR(20),

    readmission_flag VARCHAR(20),

    emergency_flag VARCHAR(20),

    outcome VARCHAR(100),

    loaded_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS staging.stg_billing
(
    batch_id BIGINT,

    bill_id VARCHAR(50),

    admission_id VARCHAR(50),

    patient_id VARCHAR(50),

    billing_date VARCHAR(50),

    room_charge VARCHAR(50),
    doctor_charge VARCHAR(50),
    procedure_charge VARCHAR(50),
    medication_charge VARCHAR(50),
    lab_charge VARCHAR(50),
    other_charge VARCHAR(50),

    gross_amount VARCHAR(50),

    discount_amount VARCHAR(50),

    insurance_amount VARCHAR(50),

    patient_amount VARCHAR(50),

    tax_amount VARCHAR(50),

    net_amount VARCHAR(50),

    paid_amount VARCHAR(50),

    outstanding_amount VARCHAR(50),

    payment_status VARCHAR(50),

    payment_method VARCHAR(100),

    loaded_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS staging.stg_claims
(
    batch_id BIGINT,

    claim_id VARCHAR(50),

    bill_id VARCHAR(50),

    patient_id VARCHAR(50),

    insurer_id VARCHAR(50),

    submission_date VARCHAR(50),

    settlement_date VARCHAR(50),

    claim_amount VARCHAR(50),

    approved_amount VARCHAR(50),

    rejected_amount VARCHAR(50),

    claim_status VARCHAR(50),

    rejection_reason VARCHAR(250),

    loaded_at TIMESTAMP
        DEFAULT CURRENT_TIMESTAMP
);