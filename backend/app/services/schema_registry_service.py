"""
Schema registry service
Manages schema versions and migrations
"""
import json
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.schema_versions import SchemaVersion
from app.services.schema_validation_service import SchemaValidationService
from app.services.category_service import CategoryService


class SchemaRegistryService:
    """Service for schema version management"""
    
    def __init__(self):
        self.schema_service = SchemaValidationService()
        self.category_service = CategoryService()
    
    def register_schema_version(
        self,
        version: str,
        description: str,
        db: Session
    ) -> SchemaVersion:
        """
        Register a new schema version
        
        Args:
            version: Version string (e.g., "1.0")
            description: Version description
            db: Database session
        
        Returns:
            Created SchemaVersion object
        """
        # Check if version already exists
        existing = db.query(SchemaVersion).filter(
            SchemaVersion.version == version
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Schema version {version} already exists"
            )
        
        # Load current schema and categories
        schema_content = json.dumps(self.schema_service.get_schema())
        category_content = json.dumps(self.category_service.get_all_categories())
        
        # Create schema version
        schema_version = SchemaVersion(
            version=version,
            schema_content=schema_content,
            category_content=category_content,
            is_active=False,  # Must be explicitly activated
            is_deprecated=False,
            description=description
        )
        
        db.add(schema_version)
        db.commit()
        db.refresh(schema_version)
        
        return schema_version
    
    def activate_schema_version(
        self,
        version: str,
        db: Session
    ) -> SchemaVersion:
        """
        Activate a schema version (deactivates others)
        
        Args:
            version: Version to activate
            db: Database session
        
        Returns:
            Activated SchemaVersion
        """
        # Deactivate all versions
        db.query(SchemaVersion).update({SchemaVersion.is_active: False})
        
        # Activate specified version
        schema_version = db.query(SchemaVersion).filter(
            SchemaVersion.version == version
        ).first()
        
        if not schema_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema version {version} not found"
            )
        
        schema_version.is_active = True
        db.commit()
        db.refresh(schema_version)
        
        return schema_version
    
    def get_active_version(self, db: Session) -> SchemaVersion:
        """
        Get currently active schema version
        
        Args:
            db: Database session
        
        Returns:
            Active SchemaVersion
        """
        schema_version = db.query(SchemaVersion).filter(
            SchemaVersion.is_active == True
        ).first()
        
        if not schema_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active schema version found"
            )
        
        return schema_version
    
    def list_all_versions(self, db: Session) -> list:
        """
        List all schema versions
        
        Args:
            db: Database session
        
        Returns:
            List of SchemaVersion objects
        """
        return db.query(SchemaVersion).order_by(SchemaVersion.created_at.desc()).all()
    
    def deprecate_version(
        self,
        version: str,
        db: Session
    ) -> SchemaVersion:
        """
        Deprecate a schema version
        
        Args:
            version: Version to deprecate
            db: Database session
        
        Returns:
            Deprecated SchemaVersion
        """
        schema_version = db.query(SchemaVersion).filter(
            SchemaVersion.version == version
        ).first()
        
        if not schema_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schema version {version} not found"
            )
        
        if schema_version.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deprecate active schema version"
            )
        
        schema_version.is_deprecated = True
        from datetime import datetime
        schema_version.deprecated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(schema_version)
        
        return schema_version
