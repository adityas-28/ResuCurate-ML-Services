import os
from dotenv import load_dotenv
import google.generativeai as genai

from app.services.pdf_parser import (
    extract_textpdf,
    extract_links_from_pdf,
    extract_links,
    classify_links
)

from app.services.genai_integration import model

# ------------------ ATS PROMPT ------------------
ATS_PROMPT = """
You are an Applicant Tracking System (ATS) used by recruiters.

First, identify the candidate’s primary professional field 
(e.g., Software Engineering, Data Science, Sales, Marketing, Medical, Finance, Student/Fresher)
based ONLY on the resume content.

Then, evaluate the resume against a GENERAL ATS standard for that field.

Your evaluation must include:

1. ATS Score (0–100) based on:
   - keyword relevance
   - clarity of experience
   - impact-oriented bullet points
   - technical depth (if applicable)
   - formatting & ATS readability

2. Strengths (2–3 short bullet points)

3. Improvements Needed (3–5 short, actionable bullet points)
   - missing keywords
   - weak bullet phrasing
   - lack of metrics
   - formatting issues
   - gaps specific to the identified field

Rules:
- Do NOT fabricate experience or skills
- Base everything strictly on the resume
- Be concise and professional
- Assume this resume is being screened by a modern ATS

Return the response in this exact format:

Field: <identified field>

ATS Score: <number only>

Strengths:
- ...
- ...

Improvements:
- ...
- ...
"""

# ------------------ ATS SCORE FUNCTION ------------------
def get_ats_score(resume_text):
    response = model.invoke([
        ATS_PROMPT,
        "RESUME:\n" + resume_text
    ])
    return response.content

import re

def parse_ats_response(ats_text: str):
    result = {
        "field": None,
        "ats_score": None,
        "strengths": [],
        "improvements": []
    }

    # ---------- FIELD ----------
    field_match = re.search(r"Field:\s*(.+)", ats_text)
    if field_match:
        result["field"] = field_match.group(1).strip()

    # ---------- ATS SCORE ----------
    score_match = re.search(r"ATS Score:\s*(\d+)", ats_text)
    if score_match:
        result["ats_score"] = int(score_match.group(1))

    # ---------- STRENGTHS ----------
    strengths_match = re.search(
        r"Strengths:\s*((?:- .+\n?)+)", ats_text
    )
    if strengths_match:
        strengths_block = strengths_match.group(1)
        result["strengths"] = [
            s.strip("- ").strip()
            for s in strengths_block.split("\n")
            if s.strip()
        ]

    # ---------- IMPROVEMENTS ----------
    improvements_match = re.search(
        r"Improvements:\s*((?:- .+\n?)+)", ats_text
    )
    if improvements_match:
        improvements_block = improvements_match.group(1)
        result["improvements"] = [
            i.strip("- ").strip()
            for i in improvements_block.split("\n")
            if i.strip()
        ]

    return result


# ------------------ MAIN ------------------
if __name__ == "__main__":
    with open("resume.pdf", "rb") as f:
        file_bytes = f.read()

    #  Reuse your parser
    resume_text = extract_textpdf(file_bytes)

    links_from_pdf = extract_links_from_pdf(file_bytes)
    links_from_text = extract_links(resume_text)
    classified_links = classify_links(
        list(set(links_from_pdf + links_from_text))
    )


    ats_result = get_ats_score(resume_text)
    result = parse_ats_response(str(ats_result))
    result["links"] = classified_links

    print("\n===== RESULT =====\n")
    print(result)