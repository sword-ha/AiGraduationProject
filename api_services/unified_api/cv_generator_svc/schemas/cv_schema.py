from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional


class PersonalInfo(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    phone: str = Field(..., min_length=7, max_length=30)
    linkedin: Optional[str] = None
    github: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    summary: Optional[str] = None


class EducationEntry(BaseModel):
    institution: str
    degree: Optional[str] = None
    field: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    gpa: Optional[str] = None
    achievements: Optional[List[str]] = []


class ExperienceEntry(BaseModel):
    company: str
    title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    location: Optional[str] = None
    bullets: Optional[List[str]] = []


class ProjectEntry(BaseModel):
    name: str
    description: Optional[str] = None
    tech_stack: Optional[List[str]] = []
    url: Optional[str] = None
    bullets: Optional[List[str]] = []


class SkillsSection(BaseModel):
    technical: Optional[List[str]] = []
    soft: Optional[List[str]] = []
    tools: Optional[List[str]] = []


class CertificationEntry(BaseModel):
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None


class CVGenerateRequest(BaseModel):
    personal: PersonalInfo
    education: Optional[List[EducationEntry]] = []
    experience: Optional[List[ExperienceEntry]] = []
    skills: Optional[SkillsSection] = None
    projects: Optional[List[ProjectEntry]] = []
    certifications: Optional[List[CertificationEntry]] = []
    target_job_title: Optional[str] = Field(
        None, description="Target job title for ATS keyword optimization"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "personal": {
                    "name": "Ahmed Ali",
                    "email": "ahmed@example.com",
                    "phone": "+20 100 000 0000",
                    "linkedin": "linkedin.com/in/ahmedali",
                    "location": "Cairo, Egypt",
                    "summary": "Software engineer with 3 years of experience in Python and AI.",
                },
                "education": [
                    {
                        "institution": "Cairo University",
                        "degree": "Bachelor of Science",
                        "field": "Computer Science",
                        "start_date": "Sep 2018",
                        "end_date": "Jun 2022",
                        "gpa": "3.7",
                    }
                ],
                "experience": [
                    {
                        "company": "Tech Corp",
                        "title": "Backend Developer",
                        "start_date": "Jul 2022",
                        "end_date": "Present",
                        "bullets": [
                            "Built REST APIs serving 100K+ daily users",
                            "Reduced query latency by 40% via indexing",
                        ],
                    }
                ],
                "skills": {
                    "technical": ["Python", "FastAPI", "PostgreSQL"],
                    "soft": ["Communication", "Problem Solving"],
                    "tools": ["Docker", "Git", "AWS"],
                },
                "target_job_title": "Backend Developer",
            }
        }
    }


class ATSBreakdown(BaseModel):
    section_completeness: int
    keyword_coverage: int
    action_verb_quality: int
    quantification: int
    formatting_quality: int
    contact_completeness: int


class CVGenerateResponse(BaseModel):
    cv_text: str
    ats_score: int
    ats_grade: str
    ats_breakdown: Optional[ATSBreakdown] = None
    matched_keywords: Optional[List[str]] = None
    missing_keywords: Optional[List[str]] = None
    suggestions: Optional[List[str]] = None
    pdf_url: Optional[str] = None
