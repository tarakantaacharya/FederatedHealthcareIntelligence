"""
Authentication service
Business logic for hospital registration and login
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import timedelta
from app.models.hospital import Hospital
from app.schemas.hospital_schema import HospitalRegister, HospitalLogin, TokenResponse
from app.utils.security import hash_password, verify_password, create_access_token
from app.config import get_settings

settings = get_settings()


class AuthService:
    """Authentication service for hospitals"""
    
    @staticmethod
    def register_hospital(db: Session, hospital_data: HospitalRegister) -> Hospital:
        """
        Register a new hospital
        
        Args:
            db: Database session
            hospital_data: Registration data
        
        Returns:
            Created hospital object
        
        Raises:
            HTTPException: If hospital_name or hospital_id already exists
        """
        import sys
        print("[REGISTER] Starting registration...", flush=True)
        sys.stdout.flush()
        
        # Check if hospital_name already exists
        print("[REGISTER] Checking hospital_name...", flush=True)
        sys.stdout.flush()
        existing_name = db.query(Hospital).filter(
            Hospital.hospital_name == hospital_data.hospital_name
        ).first()
        
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hospital name '{hospital_data.hospital_name}' is already registered"
            )
        
        # Check if hospital_id already exists
        print("[REGISTER] Checking hospital_id...", flush=True)
        sys.stdout.flush()
        existing_id = db.query(Hospital).filter(
            Hospital.hospital_id == hospital_data.hospital_id
        ).first()
        
        if existing_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hospital ID '{hospital_data.hospital_id}' is already registered"
            )
        
        # Create new hospital  
        print("[REGISTER] Creating new hospital object...", flush=True)
        sys.stdout.flush()
        new_hospital = Hospital()
        new_hospital.hospital_name = hospital_data.hospital_name
        new_hospital.hospital_id = hospital_data.hospital_id
        new_hospital.contact_email = hospital_data.contact_email
        new_hospital.location = hospital_data.location
        
        print("[REGISTER] Hashing password...", flush=True)
        sys.stdout.flush()
        new_hospital.hashed_password = hash_password(hospital_data.password)
        
        new_hospital.is_active = True
        new_hospital.is_verified = False  # Admin approval required
        new_hospital.verification_status = "PENDING"
        new_hospital.is_allowed_federated = True
        new_hospital.role = hospital_data.role  # Set role from registration (default HOSPITAL, optional ADMIN)
        
        print("[REGISTER] Adding to database...", flush=True)
        sys.stdout.flush()
        db.add(new_hospital)
        
        print("[REGISTER] Committing...", flush=True)
        sys.stdout.flush()
        db.commit()
        
        print("[REGISTER] Refreshing...", flush=True)
        sys.stdout.flush()
        db.refresh(new_hospital)
        
        print("[REGISTER] Registration complete!", flush=True)
        sys.stdout.flush()
        return new_hospital
    
    @staticmethod
    def login_hospital(db: Session, login_data: HospitalLogin) -> TokenResponse:
        """
        Authenticate hospital and generate JWT token
        
        Args:
            db: Database session
            login_data: Login credentials
        
        Returns:
            JWT access token
        
        Raises:
            HTTPException: If credentials are invalid
        """
        # Find hospital by hospital_id
        hospital = db.query(Hospital).filter(
            Hospital.hospital_id == login_data.hospital_id
        ).first()
        
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid hospital ID or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        try:
            if not verify_password(login_data.password, hospital.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid hospital ID or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except ValueError as e:
            # Hash is corrupted or invalid - log for admin investigation
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Hospital account has corrupted password hash. Contact system administrator."
            )
        
        # Check if hospital is active
        if not hospital.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hospital account is deactivated. Contact administrator."
            )

        # Phase A-Pro: Allow PENDING hospitals to login (limited state)
        # REJECTED hospitals cannot login
        is_pending = hospital.verification_status == "PENDING"
        is_verified = hospital.verification_status == "VERIFIED"
        is_rejected = hospital.verification_status == "REJECTED"
        
        if is_rejected:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hospital registration was rejected. Contact administrator."
            )
        
        # Create JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": hospital.hospital_id,
                "hospital_name": hospital.hospital_name,
                "role": hospital.role,  # Phase 30: Include role in JWT
                "verification_status": hospital.verification_status  # Phase A-Pro
            },
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            hospital_id=hospital.hospital_id,
            hospital_name=hospital.hospital_name,
            verification_status=hospital.verification_status,
            pending_verification=is_pending  # Frontend detects and redirects to /verification-pending
        )
    
    @staticmethod
    def get_current_hospital(db: Session, hospital_id: str) -> Hospital:
        """
        Get hospital by ID (for protected routes)
        
        Args:
            db: Database session
            hospital_id: Hospital identifier
        
        Returns:
            Hospital object
        
        Raises:
            HTTPException: If hospital not found
        """
        hospital = db.query(Hospital).filter(
            Hospital.hospital_id == hospital_id
        ).first()
        
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hospital not found"
            )
        
        return hospital
