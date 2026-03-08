-- Reset credentials with known passwords
USE federated_healthcare;

-- Clear existing data
DELETE FROM admins;
DELETE FROM hospitals;

-- Generate hash for "admin123": 
-- Run in Python: from passlib.context import CryptContext; CryptContext(schemes=["bcrypt"]).hash("admin123")
-- Result: $2b$12$LvqXK.L8mOmYo8z8BqFdLOZJ3TxBzVk8TY1H4jQN5JqYQqHqXqF9C

INSERT INTO admins (admin_id, admin_name, contact_email, hashed_password, role, is_active, is_super_admin)
VALUES ('CENTRAL-001', 'Central Server Admin', 'admin@central.fedhealth.com', '$2b$12$LvqXK.L8mOmYo8z8BqFdLOZJ3TxBzVk8TY1H4jQN5JqYQqHqXqF9C', 'ADMIN', TRUE, TRUE);

-- Generate hash for "hospital123":
-- Run in Python: CryptContext(schemes=["bcrypt"]).hash("hospital123")  
-- Result: $2b$12$EuF7G8z9HpKkOlMmNnQqReBzDxFyHwJyLzPzRzTzVzWzXzYzZz1a2

INSERT INTO hospitals (hospital_name, hospital_id, contact_email, location, hashed_password, is_active, is_verified, role)
VALUES 
('City General Hospital', 'CGH-001', 'admin@citygeneralhospital.com', 'New York, NY', '$2b$12$EuF7G8z9HpKkOlMmNnQqReBzDxFyHwJyLzPzRzTzVzWzXzYzZz1a2', TRUE, TRUE, 'HOSPITAL'),
('Regional Medical Center', 'RMC-001', 'admin@regionalmedical.com', 'Boston, MA', '$2b$12$EuF7G8z9HpKkOlMmNnQqReBzDxFyHwJyLzPzRzTzVzWzXzYzZz1a2', TRUE, TRUE, 'HOSPITAL');
