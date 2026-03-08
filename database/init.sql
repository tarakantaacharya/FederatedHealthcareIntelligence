-- Federated Healthcare Intelligence Database Schema
-- Phase 0 Bootstrap

CREATE DATABASE IF NOT EXISTS federated_healthcare;
USE federated_healthcare;

-- Hospitals table (Phase 1)
CREATE TABLE IF NOT EXISTS hospitals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_name VARCHAR(255) NOT NULL UNIQUE,
    hospital_id VARCHAR(100) NOT NULL UNIQUE,
    contact_email VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(20) DEFAULT 'HOSPITAL' NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_hospital_name (hospital_name),
    INDEX idx_hospital_id (hospital_id),
    INDEX idx_role (role)
);

-- Datasets table (Phase 2)
CREATE TABLE IF NOT EXISTS datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(512) NOT NULL,
    file_size_bytes INT,
    num_rows INT,
    num_columns INT,
    column_names TEXT,
    is_normalized BOOLEAN DEFAULT FALSE,
    normalized_path VARCHAR(512),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    INDEX idx_hospital_id (hospital_id)
);

-- Model weights table (Phase 4)
CREATE TABLE IF NOT EXISTS model_weights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NULL,  -- NULL means global model
    round_number INT NOT NULL DEFAULT 0,
    model_path VARCHAR(512) NOT NULL,
    model_type VARCHAR(50) DEFAULT 'sklearn_baseline',
    local_loss FLOAT,
    local_accuracy FLOAT,
    is_global BOOLEAN DEFAULT FALSE,
    model_hash VARCHAR(128) NULL,  -- Phase 8: SHA256 hash
    hash_algorithm VARCHAR(50) DEFAULT 'sha256',  -- Phase 8: Hash algorithm
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE SET NULL,
    INDEX idx_hospital_round (hospital_id, round_number),
    INDEX idx_global (is_global, round_number)
);

-- Training rounds table (Phase 7)
CREATE TABLE IF NOT EXISTS training_rounds (
    id INT AUTO_INCREMENT PRIMARY KEY,
    round_number INT NOT NULL UNIQUE,
    global_model_id INT,
    num_participating_hospitals INT DEFAULT 0,
    average_loss FLOAT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    status ENUM('pending', 'in_progress', 'completed', 'failed') DEFAULT 'pending',
    FOREIGN KEY (global_model_id) REFERENCES model_weights(id) ON DELETE SET NULL,
    INDEX idx_round_number (round_number),
    INDEX idx_status (status)
);

-- Schema mappings table (Phase 9)
CREATE TABLE IF NOT EXISTS schema_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    dataset_id INT NOT NULL,
    original_column VARCHAR(255) NOT NULL,
    canonical_field VARCHAR(255) NOT NULL,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
    UNIQUE KEY unique_mapping (dataset_id, original_column)
);

-- Schema versions table (Phase 12)
CREATE TABLE IF NOT EXISTS schema_versions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    version VARCHAR(20) NOT NULL UNIQUE,
    schema_content TEXT NOT NULL,
    category_content TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deprecated_at TIMESTAMP NULL,
    INDEX idx_version (version),
    INDEX idx_active (is_active)
);

-- Add to existing init.sql

-- Alerts table (Phase 18)
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    alert_type ENUM('capacity_warning', 'capacity_critical', 'anomaly_detection', 'forecast_degradation', 'data_quality') NOT NULL,
    severity ENUM('info', 'warning', 'critical') NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    threshold_value FLOAT,
    actual_value FLOAT,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP NULL,
    resolved_at TIMESTAMP NULL,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    INDEX idx_hospital_id (hospital_id),
    INDEX idx_severity (severity),
    INDEX idx_is_resolved (is_resolved)
);

-- Add model hash column to model_weights table
ALTER TABLE model_weights ADD COLUMN model_hash VARCHAR(64);
ALTER TABLE model_weights ADD COLUMN hash_algorithm VARCHAR(20) DEFAULT 'sha256';

-- Add index for hash lookups
CREATE INDEX idx_model_hash ON model_weights(model_hash);

-- Privacy budgets table (Phase 25)
CREATE TABLE IF NOT EXISTS privacy_budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NOT NULL,
    round_number INT NOT NULL,
    epsilon FLOAT NOT NULL,
    delta FLOAT NOT NULL,
    epsilon_spent FLOAT DEFAULT 0.0,
    total_epsilon_budget FLOAT,
    mechanism VARCHAR(100),
    sensitivity FLOAT,
    noise_multiplier FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    INDEX idx_hospital_round (hospital_id, round_number),
    INDEX idx_epsilon_spent (epsilon_spent)
);

-- Model governance table (Phase 29)
CREATE TABLE IF NOT EXISTS model_governance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    round_number INT NOT NULL,
    model_hash VARCHAR(256) NOT NULL,
    approved BOOLEAN DEFAULT FALSE NOT NULL,
    approved_by VARCHAR(100),
    signature VARCHAR(512),
    policy_version VARCHAR(50) DEFAULT 'v1' NOT NULL,
    policy_details TEXT,
    rejection_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_round_number (round_number),
    INDEX idx_model_hash (model_hash),
    INDEX idx_approved (approved)
);

-- Admins table (Phase 29/30 - Governance & RBAC)
CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    admin_id VARCHAR(50) NOT NULL UNIQUE,
    admin_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'ADMIN',
    is_active BOOLEAN DEFAULT TRUE,
    is_super_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_admin_id (admin_id),
    INDEX idx_role (role)
);

-- Seed initial admin account (development only)
-- Seed initial admin account (development only)
-- Password: admin123 (verified working hash)
INSERT IGNORE INTO admins (
    admin_id, admin_name, contact_email, hashed_password, role, is_active, is_super_admin
) VALUES (
    'CENTRAL-001', 'Central Admin', 'admin@central.com', '$2b$12$fHWKwEYrsNi/ei2NSOVbJufg6R4H4BEl4skLkjlu67vJ.v8yDVNKC', 'ADMIN', TRUE, TRUE
);

-- Seed test hospital accounts (development only)
-- Password: hospital123 (verified working hash)
INSERT IGNORE INTO hospitals (
    hospital_name, hospital_id, contact_email, location, hashed_password, is_active, is_verified, role
) VALUES (
    'City General Hospital', 'CGH-001', 'cgh@test.com', 'New York', '$2b$12$gO75AczC/higO1o8KmOO1e21cdfFg9KrSfP2YyclE4fJxK.7VRACa', TRUE, TRUE, 'HOSPITAL'
);

INSERT IGNORE INTO hospitals (
    hospital_name, hospital_id, contact_email, location, hashed_password, is_active, is_verified, role
) VALUES (
    'Regional Medical Center', 'RMC-001', 'rmc@test.com', 'Boston', '$2b$12$gO75AczC/higO1o8KmOO1e21cdfFg9KrSfP2YyclE4fJxK.7VRACa', TRUE, TRUE, 'HOSPITAL'
);

COMMIT;
