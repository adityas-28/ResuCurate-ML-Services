from typing import List, Optional
from pydantic import BaseModel

class ResumeSections(BaseModel):
    personal_information: Optional[dict]
    professional_summary: Optional[str]
    career_objective: Optional[str]

    professional_experience: Optional[List[dict]]
    education: Optional[List[dict]]
    projects: Optional[List[dict]]

    skills: Optional[List[str]]

    certifications: Optional[List[str]]
    awards_and_honors: Optional[List[str]]
    publications: Optional[List[str]]
    leadership_and_activities: Optional[List[dict]]
    research_experience: Optional[List[str]]
