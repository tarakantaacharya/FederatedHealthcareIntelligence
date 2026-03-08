"""
Blockchain model (Phase 18)
Local audit chain records
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class Blockchain(Base):
    __tablename__ = "blockchain"
    
    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, nullable=False, index=True)
    model_hash = Column(String(256), nullable=False, index=True)
    block_hash = Column(String(256), nullable=False, unique=True, index=True)
    prev_block_hash = Column(String(256), nullable=False)
    timestamp = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<Blockchain(round_id={self.round_id}, model_hash={self.model_hash[:16]}...)>"
