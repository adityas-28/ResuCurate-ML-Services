"""
Supabase Database service for storing scan results and user data.
"""
from supabase import Client
from app.services.supabase_client import get_supabase_client
from typing import Optional, Dict, Any
from datetime import datetime


def save_scan_result(
    user_id: Optional[str],
    file_path: str,
    scan_result: Dict[str, Any],
    filename: str
) -> Dict[str, Any]:
    """
    Save ATS scan result to Supabase database.
    
    Args:
        user_id: User ID (from Supabase Auth)
        file_path: Path to the resume file in storage
        scan_result: The ATS scan result dictionary
        filename: Original filename
    
    Returns:
        Inserted record
    """
    supabase = get_supabase_client()
    
    record = {
        "user_id": user_id,
        "file_path": file_path,
        "filename": filename,
        "overall_score": scan_result.get("overallScore", 0),
        "field": scan_result.get("field", "Unknown"),
        "keyword_relevance": scan_result.get("breakdown", {}).get("keywordRelevance", 0),
        "formatting_score": scan_result.get("breakdown", {}).get("formatting", 0),
        "experience_score": scan_result.get("breakdown", {}).get("experience", 0),
        "strengths": scan_result.get("strengths", []),
        "improvements": scan_result.get("improvements", []),
        "links": scan_result.get("links", {}),
        "scanned_at": datetime.utcnow().isoformat()
    }
    
    response = supabase.table("scan_results").insert(record).execute()
    return response.data[0] if response.data else record


def get_user_scan_history(user_id: str, limit: int = 10) -> list:
    """
    Get scan history for a user.
    
    Args:
        user_id: User ID
        limit: Maximum number of results to return
    
    Returns:
        List of scan results
    """
    supabase = get_supabase_client()
    
    response = supabase.table("scan_results")\
        .select("*")\
        .eq("user_id", user_id)\
        .order("scanned_at", desc=True)\
        .limit(limit)\
        .execute()
    
    return response.data if response.data else []


def get_scan_result(scan_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific scan result by ID.
    
    Args:
        scan_id: Scan result ID
    
    Returns:
        Scan result or None
    """
    supabase = get_supabase_client()
    
    response = supabase.table("scan_results")\
        .select("*")\
        .eq("id", scan_id)\
        .execute()
    
    return response.data[0] if response.data else None


def delete_scan_result(scan_id: str, user_id: Optional[str] = None) -> bool:
    """
    Delete a scan result.
    
    Args:
        scan_id: Scan result ID
        user_id: Optional user ID for authorization check
    
    Returns:
        True if successful
    """
    supabase = get_supabase_client()
    
    query = supabase.table("scan_results").delete().eq("id", scan_id)
    
    if user_id:
        query = query.eq("user_id", user_id)
    
    try:
        query.execute()
        return True
    except Exception:
        return False
