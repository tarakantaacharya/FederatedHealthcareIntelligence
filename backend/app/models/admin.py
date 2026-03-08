"""
Admin ORM Model
Authentication & authorization for central governance
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(String(50), unique=True, index=True, nullable=False)
    admin_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    role = Column(String(20), default="ADMIN", nullable=False)
    is_active = Column(Boolean, default=True)
    is_super_admin = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Admin {self.admin_id}>"
