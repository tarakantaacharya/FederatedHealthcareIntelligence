#!/usr/bin/env python
"""Setup admin account for testing"""
from app.models.admin import Admin
from app.database import SessionLocal
from app.utils.security import pwd_context

db = SessionLocal()

try:
    # Check if admin exists
    existing = db.query(Admin).filter(Admin.admin_id == 'CENTRAL-001').first()
    
    if existing:
        print(f"✓ Admin {existing.admin_id} already exists")
        print(f"  Name: {existing.admin_name}")
        print(f"  Email: {existing.contact_email}")
        print(f"  Role: {existing.role}")
    else:
        # Create admin
        admin = Admin(
            admin_id='CENTRAL-001',
            admin_name='Central Server Admin',
            contact_email='admin@central.com',
            hashed_password=pwd_context.hash('admin123'),
            role='ADMIN',
            is_super_admin=True
        )
        db.add(admin)
        db.commit()
        print("✓ Admin CENTRAL-001 created successfully")
        print(f"  Password: admin123")
        print(f"  Role: ADMIN (Super Admin)")
        
finally:
    db.close()
