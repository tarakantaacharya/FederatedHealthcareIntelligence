-- Phase 42: Governance extensions (SQLite/MySQL compatible)

-- 1) Hospitals: verification status + federated access toggle
ALTER TABLE hospitals ADD COLUMN verification_status VARCHAR(30) DEFAULT 'PENDING';
ALTER TABLE hospitals ADD COLUMN is_allowed_federated BOOLEAN DEFAULT 1;

-- Backfill verification status from existing flags
UPDATE hospitals
SET verification_status = CASE
    WHEN is_verified = 1 THEN 'VERIFIED'
    ELSE 'PENDING'
END
WHERE verification_status IS NULL;

-- 2) Model weights: training type + architecture
ALTER TABLE model_weights ADD COLUMN training_type VARCHAR(20) DEFAULT 'FEDERATED';
ALTER TABLE model_weights ADD COLUMN model_architecture VARCHAR(20) DEFAULT 'TFT';

-- Backfill defaults for existing rows
UPDATE model_weights
SET training_type = COALESCE(training_type, 'FEDERATED'),
    model_architecture = COALESCE(model_architecture, 'TFT');

-- 3) Hospital profile table
CREATE TABLE IF NOT EXISTS hospitals_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_id INTEGER NOT NULL UNIQUE,
    license_number VARCHAR(100),
    region VARCHAR(100),
    bed_capacity INTEGER,
    icu_capacity INTEGER,
    specializations TEXT,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    accreditation_status VARCHAR(50),
    registration_date DATETIME,
    verification_status VARCHAR(30),
    risk_score FLOAT,
    address_line_1 VARCHAR(255),
    address_line_2 VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    ownership_type VARCHAR(50),
    emergency_contact VARCHAR(255),
    website VARCHAR(255),
    last_audit_date DATETIME,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME,
    FOREIGN KEY(hospital_id) REFERENCES hospitals(id)
);

-- 4) Prediction records table (for saved prediction history)
CREATE TABLE IF NOT EXISTS prediction_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hospital_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    dataset_id INTEGER,
    round_id INTEGER,
    round_number INTEGER,
    target_column VARCHAR(255),
    forecast_horizon INTEGER NOT NULL DEFAULT 72,
    forecast_data JSON NOT NULL,
    schema_validation JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(hospital_id) REFERENCES hospitals(id),
    FOREIGN KEY(model_id) REFERENCES model_weights(id),
    FOREIGN KEY(dataset_id) REFERENCES datasets(id),
    FOREIGN KEY(round_id) REFERENCES training_rounds(id)
);
