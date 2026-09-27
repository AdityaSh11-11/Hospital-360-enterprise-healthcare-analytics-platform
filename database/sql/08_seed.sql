-- ============================================================
-- DEPARTMENTS
-- ============================================================

INSERT INTO warehouse.dim_department
(
    department_id,
    department_name,
    floor_number,
    bed_capacity,
    department_type
)
VALUES
('DEP001', 'Emergency', 1, 40, 'Emergency'),
('DEP002', 'Cardiology', 2, 35, 'Specialty'),
('DEP003', 'Neurology', 3, 30, 'Specialty'),
('DEP004', 'Orthopedics', 4, 40, 'Specialty'),
('DEP005', 'Pediatrics', 5, 30, 'Specialty'),
('DEP006', 'General Medicine', 6, 50, 'General'),
('DEP007', 'Oncology', 7, 25, 'Specialty'),
('DEP008', 'Gynecology', 8, 35, 'Specialty'),
('DEP009', 'ENT', 9, 20, 'Specialty'),
('DEP010', 'Dermatology', 10, 15, 'Specialty')
ON CONFLICT (department_id)
DO NOTHING;


-- ============================================================
-- INSURERS
-- Synthetic companies for portfolio/demo purposes
-- ============================================================

INSERT INTO warehouse.dim_insurer
(
    insurer_id,
    insurer_name,
    insurer_type
)
VALUES
('INS001', 'HealthSecure Insurance', 'Private'),
('INS002', 'MediShield Assurance', 'Private'),
('INS003', 'CarePlus Health', 'Private'),
('INS004', 'National Health Plan', 'Government'),
('INS005', 'LifeCare Insurance', 'Private')
ON CONFLICT (insurer_id)
DO NOTHING;


-- ============================================================
-- DIAGNOSES
-- ============================================================

INSERT INTO warehouse.dim_diagnosis
(
    diagnosis_code,
    diagnosis_name,
    diagnosis_category,
    chronic_flag
)
VALUES
(
    'DX001',
    'Hypertension',
    'Cardiovascular',
    TRUE
),
(
    'DX002',
    'Type 2 Diabetes',
    'Endocrine',
    TRUE
),
(
    'DX003',
    'Pneumonia',
    'Respiratory',
    FALSE
),
(
    'DX004',
    'Asthma',
    'Respiratory',
    TRUE
),
(
    'DX005',
    'Bone Fracture',
    'Orthopedic',
    FALSE
),
(
    'DX006',
    'Migraine',
    'Neurological',
    TRUE
),
(
    'DX007',
    'Coronary Artery Disease',
    'Cardiovascular',
    TRUE
),
(
    'DX008',
    'Chronic Kidney Disease',
    'Renal',
    TRUE
),
(
    'DX009',
    'Gastroenteritis',
    'Gastrointestinal',
    FALSE
),
(
    'DX010',
    'Anemia',
    'Hematological',
    TRUE
)
ON CONFLICT (diagnosis_code)
DO NOTHING;