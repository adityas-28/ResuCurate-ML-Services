"""
Supabase Storage service for handling file uploads and retrieval.
"""
from supabase import Client
from app.services.supabase_client import get_supabase_client
from typing import Optional
import uuid
from datetime import datetime

BUCKET_NAME = "resumes"  # Supabase storage bucket name


def upload_resume(file_bytes: bytes, filename: str, user_id: Optional[str] = None) -> dict:
    """
    Upload a resume PDF to Supabase Storage.
    
    Args:
        file_bytes: PDF file content as bytes
        filename: Original filename
        user_id: Optional user ID for organizing files
    
    Returns:
        dict with file_path and public_url
    """
    supabase = get_supabase_client()
    
    # Generate unique file path
    file_id = str(uuid.uuid4())
    file_extension = filename.split('.')[-1] if '.' in filename else 'pdf'
    file_path = f"{user_id or 'anonymous'}/{file_id}.{file_extension}"
    
    # Upload to Supabase Storage
    response = supabase.storage.from_(BUCKET_NAME).upload(
        path=file_path,
        file=file_bytes,
        file_options={"content-type": "application/pdf", "upsert": "false"}
    )
    
    # Get public URL
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
    
    return {
        "file_path": file_path,
        "public_url": public_url,
        "file_id": file_id,
        "filename": filename
    }


def get_resume(file_path: str) -> bytes:
    """
    Download a resume from Supabase Storage.
    
    Args:
        file_path: Path to the file in storage
    
    Returns:
        File content as bytes
    """
    supabase = get_supabase_client()
    response = supabase.storage.from_(BUCKET_NAME).download(file_path)
    return response


def delete_resume(file_path: str) -> bool:
    """
    Delete a resume from Supabase Storage.
    
    Args:
        file_path: Path to the file in storage
    
    Returns:
        True if successful
    """
    supabase = get_supabase_client()
    try:
        supabase.storage.from_(BUCKET_NAME).remove([file_path])
        return True
    except Exception:
        return False
