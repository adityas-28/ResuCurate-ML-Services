from fastapi import APIRouter, File, UploadFile, HTTPException, Header
from fastapi.responses import JSONResponse
from app.services.ats_scanner import get_ats_score, parse_ats_response
from app.services.pdf_parser import (
    extract_textpdf,
    extract_links_from_pdf,
    extract_links,
    classify_links
)
from typing import Optional

router = APIRouter(prefix="/api", tags=["ATS"])


@router.post("/ats-score")
async def calculate_ats_score(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Upload a PDF resume and get ATS score analysis.
    """
    # print("/ats-score hit")
    try:
        # Validate file type
        filename = file.filename or "unknown.pdf"
        if not filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        file_bytes = await file.read()
        
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

        return JSONResponse(content=response)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
