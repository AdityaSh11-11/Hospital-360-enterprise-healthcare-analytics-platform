-- ============================================================
-- HOSPITAL 360
-- DIMENSION TABLES
-- ============================================================


-- ============================================================
-- DATE DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_date
(
    date_key INTEGER PRIMARY KEY,

    full_date DATE UNIQUE NOT NULL,

    day INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,

    week_of_year INTEGER NOT NULL,

    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,

    quarter INTEGER NOT NULL,

    year INTEGER NOT NULL,

    is_weekend BOOLEAN NOT NULL DEFAULT FALSE
);


-- ============================================================
-- PATIENT DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_patient
(
    patient_key BIGSERIAL PRIMARY KEY,

    patient_id VARCHAR(30) UNIQUE NOT NULL,

    first_name VARCHAR(100),
    last_name VARCHAR(100),

    gender VARCHAR(20),

    date_of_birth DATE,

    blood_group VARCHAR(10),

    city VARCHAR(100),
    state VARCHAR(100),

    insurance_status VARCHAR(30),

    chronic_condition VARCHAR(200),

    registration_date DATE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    CONSTRAINT chk_patient_gender
        CHECK (
            gender IS NULL
            OR gender IN (
                'Male',
                'Female',
                'Other'
            )
        )
);


-- ============================================================
-- DEPARTMENT DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_department
(
    department_key SERIAL PRIMARY KEY,

    department_id VARCHAR(20) UNIQUE NOT NULL,

    department_name VARCHAR(100) UNIQUE NOT NULL,

    floor_number INTEGER,

    bed_capacity INTEGER,

    department_type VARCHAR(50),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_bed_capacity
        CHECK (
            bed_capacity IS NULL
            OR bed_capacity >= 0
        )
);


-- ============================================================
-- DOCTOR DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_doctor
(
    doctor_key BIGSERIAL PRIMARY KEY,

    doctor_id VARCHAR(30) UNIQUE NOT NULL,

    doctor_name VARCHAR(150) NOT NULL,

    gender VARCHAR(20),

    specialization VARCHAR(100),

    department_key INTEGER,

    qualification VARCHAR(150),

    experience_years INTEGER,

    consultation_fee NUMERIC(12,2),

    joining_date DATE,

    employment_status VARCHAR(30)
        DEFAULT 'Active',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_doctor_department
        FOREIGN KEY (department_key)
        REFERENCES warehouse.dim_department(department_key),

    CONSTRAINT chk_doctor_experience
        CHECK (
            experience_years IS NULL
            OR experience_years >= 0
        ),

    CONSTRAINT chk_consultation_fee
        CHECK (
            consultation_fee IS NULL
            OR consultation_fee >= 0
        )
);


-- ============================================================
-- INSURER DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_insurer
(
    insurer_key SERIAL PRIMARY KEY,

    insurer_id VARCHAR(30) UNIQUE NOT NULL,

    insurer_name VARCHAR(150) NOT NULL,

    insurer_type VARCHAR(50),

    contact_email VARCHAR(150),

    contact_phone VARCHAR(30),

    active_flag BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- DIAGNOSIS DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_diagnosis
(
    diagnosis_key SERIAL PRIMARY KEY,

    diagnosis_code VARCHAR(30) UNIQUE NOT NULL,

    diagnosis_name VARCHAR(200) NOT NULL,

    diagnosis_category VARCHAR(100),

    chronic_flag BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ============================================================
-- PROCEDURE DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_procedure
(
    procedure_key SERIAL PRIMARY KEY,

    procedure_code VARCHAR(30) UNIQUE NOT NULL,

    procedure_name VARCHAR(200) NOT NULL,

    procedure_category VARCHAR(100),

    standard_cost NUMERIC(14,2),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_procedure_cost
        CHECK (
            standard_cost IS NULL
            OR standard_cost >= 0
        )
);


-- ============================================================
-- MEDICATION DIMENSION
-- ============================================================

CREATE TABLE IF NOT EXISTS warehouse.dim_medication
(
    medication_key SERIAL PRIMARY KEY,

    medication_id VARCHAR(30) UNIQUE NOT NULL,

    medication_name VARCHAR(150) NOT NULL,

    medication_category VARCHAR(100),

    manufacturer VARCHAR(150),

    unit_cost NUMERIC(12,2),

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_medication_cost
        CHECK (
            unit_cost IS NULL
            OR unit_cost >= 0
        )
);