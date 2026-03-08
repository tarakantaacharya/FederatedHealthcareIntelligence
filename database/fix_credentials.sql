USE federated_healthcare;

DELETE FROM admins;
DELETE FROM hospitals;

-- Admin: admin123
INSERT INTO admins (admin_id, admin_name, contact_email, hashed_password, role, is_active, is_super_admin)
VALUES ('CENTRAL-001', 'Central Admin', 'admin@central.com', '$2b$12$fHWKwEYrsNi/ei2NSOVbJufg6R4H4BEl4skLkjlu67vJ.v8yDVNKC', 'ADMIN', TRUE, TRUE);

-- Hospitals: hospital123
INSERT INTO hospitals (hospital_name, hospital_id, contact_email, location, hashed_password, is_active, is_verified, role)
VALUES 
('City General Hospital', 'CGH-001', 'cgh@test.com', 'New York', '$2b$12$gO75AczC/higO1o8KmOO1e21cdfFg9KrSfP2YyclE4fJxK.7VRACa', TRUE, TRUE, 'HOSPITAL'),
('Regional Medical Center', 'RMC-001', 'rmc@test.com', 'Boston', '$2b$12$gO75AczC/higO1o8KmOO1e21cdfFg9KrSfP2YyclE4fJxK.7VRACa', TRUE, TRUE, 'HOSPITAL');
