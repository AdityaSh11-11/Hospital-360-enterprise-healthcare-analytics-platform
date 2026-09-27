-- ============================================================
-- DIMENSION INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_patient_city
ON warehouse.dim_patient(city);

CREATE INDEX IF NOT EXISTS idx_patient_state
ON warehouse.dim_patient(state);

CREATE INDEX IF NOT EXISTS idx_patient_registration
ON warehouse.dim_patient(registration_date);

CREATE INDEX IF NOT EXISTS idx_doctor_department
ON warehouse.dim_doctor(department_key);


-- ============================================================
-- ADMISSION INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_admission_patient
ON warehouse.fact_admission(patient_key);

CREATE INDEX IF NOT EXISTS idx_admission_doctor
ON warehouse.fact_admission(doctor_key);

CREATE INDEX IF NOT EXISTS idx_admission_department
ON warehouse.fact_admission(department_key);

CREATE INDEX IF NOT EXISTS idx_admission_date
ON warehouse.fact_admission(admission_date_key);

CREATE INDEX IF NOT EXISTS idx_admission_diagnosis
ON warehouse.fact_admission(diagnosis_key);

CREATE INDEX IF NOT EXISTS idx_admission_readmission
ON warehouse.fact_admission(readmission_flag);


-- ============================================================
-- BILLING INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_billing_patient
ON warehouse.fact_billing(patient_key);

CREATE INDEX IF NOT EXISTS idx_billing_admission
ON warehouse.fact_billing(admission_key);

CREATE INDEX IF NOT EXISTS idx_billing_date
ON warehouse.fact_billing(billing_date_key);

CREATE INDEX IF NOT EXISTS idx_billing_payment_status
ON warehouse.fact_billing(payment_status);


-- ============================================================
-- CLAIM INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_claim_patient
ON warehouse.fact_claim(patient_key);

CREATE INDEX IF NOT EXISTS idx_claim_insurer
ON warehouse.fact_claim(insurer_key);

CREATE INDEX IF NOT EXISTS idx_claim_status
ON warehouse.fact_claim(claim_status);

CREATE INDEX IF NOT EXISTS idx_claim_submission
ON warehouse.fact_claim(submission_date_key);


-- ============================================================
-- CONTROL INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_etl_status
ON control.etl_batch(status);

CREATE INDEX IF NOT EXISTS idx_etl_start
ON control.etl_batch(start_time);

CREATE INDEX IF NOT EXISTS idx_quality_batch
ON control.data_quality_log(batch_id);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp
ON control.audit_log(event_timestamp);