from .genai_integration import model
import json
from app.schemas.schemas import ResumeSections

from app.services.pdf_parser import (
    extract_textpdf,
    extract_links_from_pdf,
    extract_links,
    classify_links
)

STRUCTURE_PROMPT = """
You are a resume parser.

Your task is to extract and organize resume content into structured sections.

Extract ONLY information that exists in the resume.
Do NOT fabricate or infer missing details.

Return STRICT JSON matching this schema:

{
  "personal_information": {
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "links": []
  },
  "professional_summary": "",
  "career_objective": "",
  "professional_experience": [
    {
      "company": "",
      "role": "",
      "duration": "",
      "description": ""
    }
  ],
  "education": [
    {
      "institution": "",
      "degree": "",
      "duration": ""
    }
  ],
  "projects": [
    {
      "title": "",
      "description": "",
      "technologies": []
    }
  ],
  "skills": [],
  "certifications": [],
  "awards_and_honors": [],
  "publications": [],
  "leadership_and_activities": [],
  "research_experience": []
}

Rules:
- If a section is missing, return null
- Keep descriptions concise
- Return ONLY valid JSON
"""

def structure_resume(resume_text: str) -> ResumeSections:
    response = model.invoke(
        STRUCTURE_PROMPT + "\n\nRESUME:\n" + resume_text
    )
    response_content = str(response.content)
    response_content = response_content.lstrip("```json").rstrip("```")
    print("Response received...")
    print(response_content)
    return ResumeSections.model_validate(json.loads(str(response_content)))


# ------------------ MAIN ------------------
if __name__ == "__main__":
    print("Starting resume structuring...")
    with open("resume.pdf", "rb") as f:
        file_bytes = f.read()

    resume_text = extract_textpdf(file_bytes)
    print("Extracted resume text...")
    links_from_pdf = extract_links_from_pdf(file_bytes)
    links_from_text = extract_links(resume_text)
    classified_links = classify_links(
        list(set(links_from_pdf + links_from_text))
    )
    print("Classified links...")
    result = structure_resume(resume_text)
    print("Structured resume...")
    # flatten links
    all_links = []
    for group in classified_links.values():
        all_links.extend(group)

    if result.personal_information is not None:
        result.personal_information["links"] = all_links

    print(result.model_dump())
