-- ============================================================
-- HOSPITAL 360
-- PHASE 5.4 — ANALYTICS PERFORMANCE INDEXES
-- ============================================================
--
-- CREATE INDEX IF NOT EXISTS makes this script rerunnable.
--
-- These indexes target:
--   fact -> dimension joins
--   date filtering
--   department / doctor / diagnosis slicing
--   patient history queries
--   claim insurer/date analysis
-- ============================================================


-- ============================================================
-- FACT ADMISSION
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_fact_admission_patient_key
ON warehouse.fact_admission (
    patient_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_admission_doctor_key
ON warehouse.fact_admission (
    doctor_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_admission_department_key
ON warehouse.fact_admission (
    department_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_admission_diagnosis_key
ON warehouse.fact_admission (
    diagnosis_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_admission_admission_date_key
ON warehouse.fact_admission (
    admission_date_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_admission_discharge_date_key
ON warehouse.fact_admission (
    discharge_date_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_admission_department_date
ON warehouse.fact_admission (
    department_key,
    admission_date_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_admission_doctor_date
ON warehouse.fact_admission (
    doctor_key,
    admission_date_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_admission_diagnosis_date
ON warehouse.fact_admission (
    diagnosis_key,
    admission_date_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_admission_patient_timestamp
ON warehouse.fact_admission (
    patient_key,
    admission_timestamp
);


-- ============================================================
-- FACT BILLING
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_fact_billing_admission_key
ON warehouse.fact_billing (
    admission_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_billing_patient_key
ON warehouse.fact_billing (
    patient_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_billing_date_key
ON warehouse.fact_billing (
    billing_date_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_billing_payment_status
ON warehouse.fact_billing (
    payment_status
);


CREATE INDEX IF NOT EXISTS
    idx_fact_billing_payment_method
ON warehouse.fact_billing (
    payment_method
);


CREATE INDEX IF NOT EXISTS
    idx_fact_billing_patient_date
ON warehouse.fact_billing (
    patient_key,
    billing_date_key
);


-- ============================================================
-- FACT CLAIM
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_fact_claim_billing_key
ON warehouse.fact_claim (
    billing_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_claim_patient_key
ON warehouse.fact_claim (
    patient_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_claim_insurer_key
ON warehouse.fact_claim (
    insurer_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_claim_submission_date_key
ON warehouse.fact_claim (
    submission_date_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_claim_settlement_date_key
ON warehouse.fact_claim (
    settlement_date_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_claim_status
ON warehouse.fact_claim (
    claim_status
);


CREATE INDEX IF NOT EXISTS
    idx_fact_claim_insurer_submission
ON warehouse.fact_claim (
    insurer_key,
    submission_date_key
);


-- ============================================================
-- FACT LAB TEST
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_fact_lab_patient_key
ON warehouse.fact_lab_test (
    patient_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_lab_admission_key
ON warehouse.fact_lab_test (
    admission_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_lab_doctor_key
ON warehouse.fact_lab_test (
    doctor_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_lab_test_date_key
ON warehouse.fact_lab_test (
    test_date_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_lab_abnormal_flag
ON warehouse.fact_lab_test (
    abnormal_flag
);


-- ============================================================
-- FACT MEDICATION
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_fact_medication_patient_key
ON warehouse.fact_medication (
    patient_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_medication_admission_key
ON warehouse.fact_medication (
    admission_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_medication_medication_key
ON warehouse.fact_medication (
    medication_key
);


CREATE INDEX IF NOT EXISTS
    idx_fact_medication_date_key
ON warehouse.fact_medication (
    prescribed_date_key
);


-- ============================================================
-- DIMENSION SUPPORT
-- ============================================================

CREATE INDEX IF NOT EXISTS
    idx_dim_patient_registration_date
ON warehouse.dim_patient (
    registration_date
);


CREATE INDEX IF NOT EXISTS
    idx_dim_patient_state_city
ON warehouse.dim_patient (
    state,
    city
);


CREATE INDEX IF NOT EXISTS
    idx_dim_patient_chronic_condition
ON warehouse.dim_patient (
    chronic_condition
);


CREATE INDEX IF NOT EXISTS
    idx_dim_doctor_department_key
ON warehouse.dim_doctor (
    department_key
);


CREATE INDEX IF NOT EXISTS
    idx_dim_diagnosis_category
ON warehouse.dim_diagnosis (
    diagnosis_category
);


-- ============================================================
-- UPDATE PLANNER STATISTICS
-- ============================================================

ANALYZE warehouse.fact_admission;
ANALYZE warehouse.fact_billing;
ANALYZE warehouse.fact_claim;
ANALYZE warehouse.fact_lab_test;
ANALYZE warehouse.fact_medication;

ANALYZE warehouse.dim_patient;
ANALYZE warehouse.dim_doctor;
ANALYZE warehouse.dim_department;
ANALYZE warehouse.dim_diagnosis;
ANALYZE warehouse.dim_insurer;
ANALYZE warehouse.dim_medication;