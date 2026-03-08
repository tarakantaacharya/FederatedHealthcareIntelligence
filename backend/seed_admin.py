#!/usr/bin/env python
"""Seed admin account directly from backend"""
import sys
import os

# Ensure app module is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.admin import Admin
from app.utils.security import hash_password
from sqlalchemy.exc import IntegrityError

db = SessionLocal()

try:
    # Create admin with CENTRAL-001 / admin123 (documented credentials)
    existing_admin = db.query(Admin).filter(Admin.admin_id == 'CENTRAL-001').first()
    if not existing_admin:
        admin = Admin(
            admin_id='CENTRAL-001',
            admin_name='Central Admin',
            contact_email='admin@central.com',
            hashed_password=hash_password('admin123'),
            role='ADMIN',
            is_active=True,
            is_super_admin=True
        )
        db.add(admin)
        db.commit()
        print("✓ Admin CENTRAL-001 created with password: admin123")
    else:
        print("✓ Admin CENTRAL-001 already exists")
        
finally:
    db.close()
