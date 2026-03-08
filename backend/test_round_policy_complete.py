#!/usr/bin/env python
"""
Comprehensive backend test for Round Policy Configuration
Tests all selection criteria: EMERGENCY, ALL, REGION, SIZE, EXPERIENCE, MANUAL
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.database import Base, SessionLocal
from app.models.hospital import Hospital
from app.models.hospitals_profile import HospitalProfile
from app.models.training_rounds import TrainingRound
from app.models.round_allowed_hospital import RoundAllowedHospital
from app.services.round_service import RoundService
from app.services.participation_service import ParticipationService
from app.utils.security import pwd_context
import json
from datetime import datetime

# Create test database connection
db = SessionLocal()

def cleanup_test_data():
    """Clean up all test data"""
    print("\n>>> Cleaning up test data...")
    db.query(RoundAllowedHospital).delete()
    db.query(TrainingRound).delete()
    db.query(HospitalProfile).delete()
    db.query(Hospital).delete()
    db.commit()
    print("✓ Cleanup complete")

def create_test_hospital(hospital_id: str, name: str, region: str, size: str, experience: str) -> Hospital:
    """Create a test hospital with profile"""
    hospital = Hospital(
        hospital_id=hospital_id,
        hospital_name=name,
        contact_email=f"{hospital_id}@test.local",
        hashed_password=pwd_context.hash("testpass123"),
        is_active=True,
        is_verified=True,
        verification_status="VERIFIED",
        is_allowed_federated=True
    )
    db.add(hospital)
    db.flush()
    
    profile = HospitalProfile(
        hospital_id=hospital.id,
        region=region,
        size_category=size,
        experience_level=experience,
        bed_capacity=100 if size == "SMALL" else 500,
        icu_capacity=10 if size == "SMALL" else 50
    )
    db.add(profile)
    db.commit()
    
    print(f"  ✓ Created: {name} ({region}, {size}, {experience})")
    return hospital

def test_emergency_round():
    """Test EMERGENCY round - all verified hospitals should be eligible"""
    print("\n=== TEST 1: EMERGENCY Round ===")
    
    round_obj = RoundService.create_new_round(
        db, 
        target_column="bed_occupancy",
        is_emergency=True  # Emergency override
    )
    print(f"✓ Created emergency round #{round_obj.round_number}")
    print(f"  - is_emergency: {round_obj.is_emergency}")
    print(f"  - participation_policy: {round_obj.participation_policy}")
    
    # All hospitals should be eligible
    hospitals = db.query(Hospital).all()
    for hospital in hospitals:
        eligible, reason = ParticipationService.can_participate(hospital.id, round_obj.id, db)
        status = "✓" if eligible else "✗"
        print(f"  {status} {hospital.hospital_name}: {reason}")
        assert eligible, f"Emergency round should make {hospital.hospital_name} eligible"
    
    return round_obj

def test_all_round():
    """Test ALL round - all verified hospitals should be eligible"""
    print("\n=== TEST 2: ALL (No restrictions) Round ===")
    
    round_obj = RoundService.create_new_round(
        db,
        target_column="bed_occupancy",
        is_emergency=False,
        participation_mode="ALL"
    )
    print(f"✓ Created round #{round_obj.round_number} (ALL mode)")
    print(f"  - participation_policy: {round_obj.participation_policy}")
    
    # All hospitals should be eligible
    hospitals = db.query(Hospital).all()
    for hospital in hospitals:
        eligible, reason = ParticipationService.can_participate(hospital.id, round_obj.id, db)
        status = "✓" if eligible else "✗"
        print(f"  {status} {hospital.hospital_name}: {reason}")
        assert eligible, f"ALL round should make {hospital.hospital_name} eligible"
    
    return round_obj

def test_region_round():
    """Test REGION-based selection"""
    print("\n=== TEST 3: REGION-based Selection ===")
    
    round_obj = RoundService.create_new_round(
        db,
        target_column="bed_occupancy",
        is_emergency=False,
        participation_mode="SELECTIVE",
        selection_criteria="REGION",
        selection_value="EAST"
    )
    print(f"✓ Created round #{round_obj.round_number} (REGION=EAST)")
    print(f"  - selection_criteria: {round_obj.selection_criteria}")
    print(f"  - selection_value: {round_obj.selection_value}")
    
    hospitals = db.query(Hospital).all()
    east_count = 0
    for hospital in hospitals:
        eligible, reason = ParticipationService.can_participate(hospital.id, round_obj.id, db)
        status = "✓" if eligible else "✗"
        profile = db.query(HospitalProfile).filter(HospitalProfile.hospital_id==hospital.id).first()
        print(f"  {status} {hospital.hospital_name} ({profile.region}): {reason}")
        if eligible:
            east_count += 1
            assert profile.region == "EAST", f"{hospital.hospital_name} should only be eligible if in EAST"
    
    print(f"  → {east_count} out of {len(hospitals)} hospitals eligible")
    assert east_count > 0, "Should have at least one EAST hospital eligible"
    
    return round_obj

def test_size_round():
    """Test SIZE-based selection"""
    print("\n=== TEST 4: SIZE-based Selection ===")
    
    round_obj = RoundService.create_new_round(
        db,
        target_column="bed_occupancy",
        is_emergency=False,
        participation_mode="SELECTIVE",
        selection_criteria="SIZE",
        selection_value="LARGE"
    )
    print(f"✓ Created round #{round_obj.round_number} (SIZE=LARGE)")
    print(f"  - selection_criteria: {round_obj.selection_criteria}")
    print(f"  - selection_value: {round_obj.selection_value}")
    
    hospitals = db.query(Hospital).all()
    large_count = 0
    for hospital in hospitals:
        eligible, reason = ParticipationService.can_participate(hospital.id, round_obj.id, db)
        status = "✓" if eligible else "✗"
        profile = db.query(HospitalProfile).filter(HospitalProfile.hospital_id==hospital.id).first()
        print(f"  {status} {hospital.hospital_name} ({profile.size_category}): {reason}")
        if eligible:
            large_count += 1
            assert profile.size_category == "LARGE", f"{hospital.hospital_name} should only be eligible if LARGE"
    
    print(f"  → {large_count} out of {len(hospitals)} hospitals eligible")
    assert large_count > 0, "Should have at least one LARGE hospital eligible"
    
    return round_obj

def test_experience_round():
    """Test EXPERIENCE-based selection"""
    print("\n=== TEST 5: EXPERIENCE-based Selection ===")
    
    round_obj = RoundService.create_new_round(
        db,
        target_column="bed_occupancy",
        is_emergency=False,
        participation_mode="SELECTIVE",
        selection_criteria="EXPERIENCE",
        selection_value="EXPERIENCED"
    )
    print(f"✓ Created round #{round_obj.round_number} (EXPERIENCE=EXPERIENCED)")
    print(f"  - selection_criteria: {round_obj.selection_criteria}")
    print(f"  - selection_value: {round_obj.selection_value}")
    
    hospitals = db.query(Hospital).all()
    exp_count = 0
    for hospital in hospitals:
        eligible, reason = ParticipationService.can_participate(hospital.id, round_obj.id, db)
        status = "✓" if eligible else "✗"
        profile = db.query(HospitalProfile).filter(HospitalProfile.hospital_id==hospital.id).first()
        print(f"  {status} {hospital.hospital_name} ({profile.experience_level}): {reason}")
        if eligible:
            exp_count += 1
            assert profile.experience_level == "EXPERIENCED", f"{hospital.hospital_name} should only be eligible if EXPERIENCED"
    
    print(f"  → {exp_count} out of {len(hospitals)} hospitals eligible")
    assert exp_count > 0, "Should have at least one EXPERIENCED hospital eligible"
    
    return round_obj

def test_manual_round():
    """Test MANUAL selection"""
    print("\n=== TEST 6: MANUAL Selection ===")
    
    # Get first 2 hospitals for manual selection
    hospitals = db.query(Hospital).limit(2).all()
    hospital_ids = [h.id for h in hospitals]
    
    round_obj = RoundService.create_new_round(
        db,
        target_column="bed_occupancy",
        is_emergency=False,
        participation_mode="SELECTIVE",
        selection_criteria="MANUAL"
    )
    print(f"✓ Created round #{round_obj.round_number} (MANUAL)")
    
    # Manually add allowed hospitals
    for hosp_id in hospital_ids:
        allowed = RoundAllowedHospital(round_id=round_obj.id, hospital_id=hosp_id)
        db.add(allowed)
    db.commit()
    
    print(f"  - Manually selected {len(hospital_ids)} hospitals")
    
    all_hospitals = db.query(Hospital).all()
    manual_count = 0
    for hospital in all_hospitals:
        eligible, reason = ParticipationService.can_participate(hospital.id, round_obj.id, db)
        status = "✓" if eligible else "✗"
        print(f"  {status} {hospital.hospital_name}: {reason}")
        if hospital.id in hospital_ids:
            assert eligible, f"{hospital.hospital_name} should be manually eligible"
            manual_count += 1
        else:
            assert not eligible, f"{hospital.hospital_name} should NOT be eligible (not in manual list)"
    
    print(f"  → {manual_count} manually selected hospitals are eligible")
    assert manual_count == len(hospital_ids), "All manually selected hospitals should be eligible"
    
    return round_obj

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("ROUND POLICY CONFIGURATION BACKEND TEST SUITE")
    print("="*70)
    
    try:
        # Setup test data
        cleanup_test_data()
        
        print("\n>>> Creating test hospitals...")
        h1 = create_test_hospital("H001", "East Regional", "EAST", "LARGE", "EXPERIENCED")
        h2 = create_test_hospital("H002", "West Community", "WEST", "SMALL", "NEW")
        h3 = create_test_hospital("H003", "East Teaching", "EAST", "LARGE", "NEW")
        h4 = create_test_hospital("H004", "West Clinic", "WEST", "LARGE", "EXPERIENCED")
        
        # Run all tests
        test_emergency_round()
        test_all_round()
        test_region_round()
        test_size_round()
        test_experience_round()
        test_manual_round()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS PASSED")
        print("="*70)
        print("\nBackend Round Policy Configuration is fully operational:")
        print("  ✓ EMERGENCY rounds work (bypass all policies)")
        print("  ✓ ALL mode works (all verified hospitals accessible)")
        print("  ✓ REGION selection works")
        print("  ✓ SIZE selection works")
        print("  ✓ EXPERIENCE selection works")
        print("  ✓ MANUAL selection works")
        print("\nReady for frontend implementation!")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
