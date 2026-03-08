"""
File storage utilities for dataset uploads
"""
import os
import shutil
from datetime import datetime
from fastapi import UploadFile
from app.config import get_settings

settings = get_settings()


async def save_uploaded_file(file: UploadFile, hospital_id: str) -> dict:
    """
    Save uploaded CSV file to storage
    
    Args:
        file: Uploaded file from FastAPI
        hospital_id: Hospital identifier for folder organization
    
    Returns:
        Dictionary with file metadata
    """
    # Create hospital-local dataset directory (not used by aggregation logic)
    hospital_dir = os.path.join(settings.UPLOAD_DIR, hospital_id, "datasets")
    os.makedirs(hospital_dir, exist_ok=True)
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = file.filename or "dataset.csv"
    filename_parts = os.path.splitext(original_filename)
    unique_filename = f"{filename_parts[0]}_{timestamp}{filename_parts[1]}"
    
    file_path = os.path.join(hospital_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    return {
        "filename": unique_filename,
        "original_filename": original_filename,
        "file_path": file_path,
        "file_size_bytes": file_size
    }


def delete_file(file_path: str) -> bool:
    """
    Delete a file from storage
    
    Args:
        file_path: Path to file
    
    Returns:
        True if deleted, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False
