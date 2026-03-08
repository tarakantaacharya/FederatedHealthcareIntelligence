"""
Phase 33-40 Database Migration
Creates tables for new features
"""

-- Phase 34: Model Registry
CREATE TABLE IF NOT EXISTS model_registry (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL COMMENT 'baseline_rf, tft, lstm, xgboost, category_specific',
    version VARCHAR(20) NOT NULL,
    hospital_id INT NULL COMMENT 'NULL = global model',
    is_global BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    accuracy FLOAT NULL,
    loss FLOAT NULL,
    metadata JSON NULL COMMENT 'Model config, hyperparameters, etc.',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_model_name (model_name),
    INDEX idx_model_type (model_type),
    INDEX idx_is_active (is_active),
    INDEX idx_hospital_id (hospital_id),
    
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Phase 37: System Metrics (optional - Prometheus uses time-series DB)
-- This table stores historical snapshots for long-term analysis
CREATE TABLE IF NOT EXISTS system_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    labels JSON NULL COMMENT 'Metric labels (hospital_id, round_number, etc.)',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_metric_name (metric_name),
    INDEX idx_timestamp (timestamp)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Phase 39: Security Audit Log
CREATE TABLE IF NOT EXISTS security_audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL COMMENT 'login_attempt, rate_limit_exceeded, etc.',
    ip_address VARCHAR(45) NOT NULL,
    hospital_id INT NULL,
    user_agent TEXT NULL,
    request_path VARCHAR(255) NULL,
    status_code INT NULL,
    details JSON NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_event_type (event_type),
    INDEX idx_ip_address (ip_address),
    INDEX idx_hospital_id (hospital_id),
    INDEX idx_timestamp (timestamp),
    
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Seed initial model registry entries for existing models
INSERT INTO model_registry (model_name, model_type, version, is_global, is_active, metadata)
VALUES 
    ('Global Baseline', 'baseline_rf', '1.0.0', TRUE, TRUE, '{"description": "Initial Random Forest baseline model"}'),
    ('TFT Global', 'tft', '1.0.0', TRUE, FALSE, '{"description": "Temporal Fusion Transformer (optional)"}')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;
