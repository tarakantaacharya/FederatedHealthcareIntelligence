"""
Hospital profile service
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.hospitals_profile import HospitalProfile


class HospitalProfileService:
    """Service for hospital profile CRUD."""

    @staticmethod
    def get_or_create_profile(db: Session, hospital_id: int) -> HospitalProfile:
        profile = db.query(HospitalProfile).filter(
            HospitalProfile.hospital_id == hospital_id
        ).first()
        if profile:
            return profile

        profile = HospitalProfile(hospital_id=hospital_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def update_profile(db: Session, hospital_id: int, updates: dict) -> HospitalProfile:
        profile = HospitalProfileService.get_or_create_profile(db, hospital_id)

        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_profile(db: Session, hospital_id: int) -> HospitalProfile:
        profile = db.query(HospitalProfile).filter(
            HospitalProfile.hospital_id == hospital_id
        ).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hospital profile not found"
            )
        return profile
