from fastapi import APIRouter, File, UploadFile, HTTPException, Header
from fastapi.responses import JSONResponse
from app.services.ats_scanner import get_ats_score, parse_ats_response
from app.services.pdf_parser import (
    extract_textpdf,
    extract_links_from_pdf,
    extract_links,
    classify_links
)
from app.services.supabase_storage import upload_resume
from app.services.supabase_db import save_scan_result
from typing import Optional
import os

router = APIRouter(prefix="/api", tags=["ATS"])

# Check if Supabase is enabled
USE_SUPABASE = os.getenv("USE_SUPABASE", "false").lower() == "true"


@router.post("/ats-score")
async def calculate_ats_score(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Upload a PDF resume and get ATS score analysis.
    Optionally saves to Supabase if USE_SUPABASE is enabled.
    """
    try:
        # Validate file type
        filename = file.filename or "unknown.pdf"
        if not filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        file_bytes = await file.read()
        
        # Extract user ID from authorization header if using Supabase
        user_id = None
        if USE_SUPABASE and authorization:
            # Extract user ID from JWT token (simplified - you may want to verify the token)
            # In production, verify the token with Supabase Auth
            try:
                from app.services.supabase_client import get_supabase_client
                supabase = get_supabase_client()
                # Verify token and get user
                auth_response = supabase.auth.get_user(authorization.replace("Bearer ", ""))
                if auth_response and auth_response.user:
                    user_id = auth_response.user.id
            except Exception:
                # If token verification fails, continue as anonymous user
                pass
        
        # Extract text from PDF
        resume_text = extract_textpdf(file_bytes)
        
        if not resume_text or not resume_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF. Please ensure the PDF contains readable text.")
        
        # Extract links
        links_from_pdf = extract_links_from_pdf(file_bytes)
        links_from_text = extract_links(resume_text)
        classified_links = classify_links(
            list(set(links_from_pdf + links_from_text))
        )
        
        # Get ATS score
        ats_result = get_ats_score(resume_text)
        result = parse_ats_response(str(ats_result))
        result["links"] = classified_links
        
        # Format response to match frontend expectations
        response = {
            "overallScore": result.get("ats_score", 0),
            "field": result.get("field", "Unknown"),
            "breakdown": {
                "keywordRelevance": result.get("ats_score", 0),
                "formatting": result.get("ats_score", 0),
                "experience": result.get("ats_score", 0),
            },
            "strengths": result.get("strengths", []),
            "improvements": result.get("improvements", []),
            "links": result.get("links", {}),
            "resumeName": filename
        }
        
        # Save to Supabase if enabled
        if USE_SUPABASE:
            try:
                # Upload file to Supabase Storage
                storage_result = upload_resume(file_bytes, filename, user_id)
                
                # Save scan result to database
                db_result = save_scan_result(
                    user_id=user_id,
                    file_path=storage_result["file_path"],
                    scan_result=response,
                    filename=filename
                )
                
                # Add scan ID to response
                response["scanId"] = db_result.get("id")
                response["fileUrl"] = storage_result["public_url"]
            except Exception as e:
                # Log error but don't fail the request
                print(f"Supabase save error: {str(e)}")
                # Continue without Supabase features
        
        return JSONResponse(content=response)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")


@router.get("/scan-history")
async def get_scan_history(authorization: Optional[str] = Header(None)):
    """
    Get scan history for the authenticated user.
    Requires Supabase to be enabled.
    """
    if not USE_SUPABASE:
        raise HTTPException(status_code=501, detail="Supabase is not enabled")
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization required")
    
    try:
        from app.services.supabase_client import get_supabase_client
        from app.services.supabase_db import get_user_scan_history
        
        supabase = get_supabase_client()
        auth_response = supabase.auth.get_user(authorization.replace("Bearer ", ""))
        
        if not auth_response or not auth_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        history = get_user_scan_history(auth_response.user.id)
        return JSONResponse(content={"history": history})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching scan history: {str(e)}")
