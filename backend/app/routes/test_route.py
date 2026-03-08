"""Test if DELETE routes work at all"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()

@router.delete("/test-delete")
async def test_delete(
    db: Session = Depends(get_db)
):
    """Simple test endpoint"""
    return {"status": "DELETE works"}

@router.get("/test-get")
async def test_get(db: Session = Depends(get_db)):
    """Simple test endpoint"""
    return {"status": "GET works"}
