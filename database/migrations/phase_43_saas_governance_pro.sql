-- Phase A-Pro: SaaS-Grade Federated Healthcare Governance
-- Migration: Hospital verification UX, round participation policies, isolation refinements

-- 1. Extend training_rounds table with participation governance
ALTER TABLE training_rounds 
ADD COLUMN participation_policy VARCHAR(20) DEFAULT 'ALL' NOT NULL;

ALTER TABLE training_rounds 
ADD COLUMN is_emergency BOOLEAN DEFAULT FALSE NOT NULL;

-- 2. Create round_allowed_hospitals junction table (SELECTED policy)
CREATE TABLE IF NOT EXISTS round_allowed_hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    round_id INTEGER NOT NULL,
    hospital_id INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (round_id) REFERENCES training_rounds(id),
    FOREIGN KEY (hospital_id) REFERENCES hospitals(id),
    UNIQUE(round_id, hospital_id)
);

-- Create indexes for round eligibility queries
CREATE INDEX IF NOT EXISTS idx_round_allowed_hospitals_round_id 
ON round_allowed_hospitals(round_id);

CREATE INDEX IF NOT EXISTS idx_round_allowed_hospitals_hospital_id 
ON round_allowed_hospitals(hospital_id);

CREATE INDEX IF NOT EXISTS idx_training_rounds_participation_policy 
ON training_rounds(participation_policy);

CREATE INDEX IF NOT EXISTS idx_training_rounds_is_emergency 
ON training_rounds(is_emergency);

-- 3. Ensure hospitals_profile has region for REGION_BASED filtering
-- (already created in phase_42_governance_extensions.sql, verify here)
-- ALTER TABLE hospitals_profile ADD COLUMN region VARCHAR(255);

-- 4. Add metadata column to training_rounds for policy-specific data (capacity threshold, region list, etc.)
ALTER TABLE training_rounds 
ADD COLUMN policy_metadata JSON DEFAULT NULL;

-- Schema: 
-- REGION_BASED: {"allowed_regions": ["Region1", "Region2"]}
-- CAPACITY_BASED: {"bed_capacity_threshold": 100}
-- ALL: null or {}
-- SELECTED: null or {}
