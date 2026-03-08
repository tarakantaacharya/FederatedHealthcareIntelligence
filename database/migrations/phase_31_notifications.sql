-- Phase 31: Notifications Engine
-- Creates tables for in-app notifications and email preferences

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT NULL,
    admin_id INT NULL,
    type ENUM('info', 'success', 'warning', 'error') DEFAULT 'info',
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    action_url VARCHAR(512) NULL,
    action_label VARCHAR(100) NULL,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE,
    FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE CASCADE,
    INDEX idx_hospital_id (hospital_id),
    INDEX idx_admin_id (admin_id),
    INDEX idx_is_read (is_read),
    INDEX idx_created_at (created_at)
);

-- Notification preferences table
CREATE TABLE IF NOT EXISTS notification_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hospital_id INT UNIQUE NOT NULL,
    email_enabled BOOLEAN DEFAULT TRUE,
    email_capacity_alerts BOOLEAN DEFAULT TRUE,
    email_forecast_degradation BOOLEAN DEFAULT TRUE,
    email_model_updates BOOLEAN DEFAULT TRUE,
    email_data_quality BOOLEAN DEFAULT TRUE,
    inapp_enabled BOOLEAN DEFAULT TRUE,
    inapp_capacity_alerts BOOLEAN DEFAULT TRUE,
    inapp_forecast_degradation BOOLEAN DEFAULT TRUE,
    inapp_model_updates BOOLEAN DEFAULT TRUE,
    inapp_data_quality BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE CASCADE
);

-- Seed default preferences for existing hospitals
INSERT INTO notification_preferences (hospital_id)
SELECT id FROM hospitals
WHERE id NOT IN (SELECT hospital_id FROM notification_preferences);
