import logging
import os
import sys
from typing import Any, Dict

from cv_generator_svc.schemas.cv_schema import ATSBreakdown, CVGenerateRequest, CVGenerateResponse

logger = logging.getLogger(__name__)

_CV_GEN_DIR = os.getenv(
    "CV_GENERATOR_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "cv_generator"),
)
sys.path.insert(0, os.path.abspath(_CV_GEN_DIR))

OUTPUT_DIR = os.getenv("CV_OUTPUT_DIR", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class CVGeneratorService:
    def __init__(self):
        from src.processor.validator import DataValidator
        from src.processor.normalizer import SkillNormalizer
        from src.processor.optimizer import ATSOptimizer
        from src.scorer.ats_scorer import ATSScorer
        from src.analyzer.improvement_suggester import ImprovementSuggester
        from src.builder.pdf_builder import PDFBuilder

        self._validator = DataValidator()
        self._normalizer = SkillNormalizer()
        self._optimizer = ATSOptimizer()
        self._scorer = ATSScorer()
        self._suggester = ImprovementSuggester()
        self._pdf_builder = PDFBuilder()

    def _build_cv_dict(self, req: CVGenerateRequest) -> Dict[str, Any]:
        personal = req.personal
        return {
            "personal": {
                "name": personal.name,
                "email": personal.email,
                "phone": personal.phone,
                "linkedin": personal.linkedin or "",
                "github": personal.github or "",
                "location": personal.location or "",
                "website": personal.website or "",
                "summary": personal.summary or "",
            },
            "education": [
                {
                    "institution": e.institution,
                    "degree": e.degree or "",
                    "field": e.field or "",
                    "start_date": e.start_date or "",
                    "end_date": e.end_date or "",
                    "gpa": e.gpa or "",
                    "achievements": e.achievements or [],
                }
                for e in (req.education or [])
            ],
            "experience": [
                {
                    "company": exp.company,
                    "title": exp.title or "",
                    "start_date": exp.start_date or "",
                    "end_date": exp.end_date or "",
                    "location": exp.location or "",
                    "bullets": exp.bullets or [],
                }
                for exp in (req.experience or [])
            ],
            "skills": {
                "technical": (req.skills.technical if req.skills else []) or [],
                "soft": (req.skills.soft if req.skills else []) or [],
                "tools": (req.skills.tools if req.skills else []) or [],
            },
            "projects": [
                {
                    "name": p.name,
                    "description": p.description or "",
                    "tech_stack": p.tech_stack or [],
                    "url": p.url or "",
                    "bullets": p.bullets or [],
                }
                for p in (req.projects or [])
            ],
            "certifications": [
                {
                    "name": c.name,
                    "issuer": c.issuer or "",
                    "date": c.date or "",
                    "url": c.url or "",
                }
                for c in (req.certifications or [])
            ],
            "meta": {},
        }

    def _render_cv_text(self, cv_data: Dict[str, Any]) -> str:
        lines = []
        personal = cv_data.get("personal", {})

        lines.append(personal.get("name", "").upper())
        contact_parts = filter(None, [
            personal.get("email"),
            personal.get("phone"),
            personal.get("location"),
        ])
        lines.append(" | ".join(contact_parts))
        for link_key in ("linkedin", "github", "website"):
            if personal.get(link_key):
                lines.append(personal[link_key])
        if personal.get("summary"):
            lines += ["", "PROFESSIONAL SUMMARY", "-" * 40, personal["summary"]]

        if cv_data.get("experience"):
            lines += ["", "EXPERIENCE", "-" * 40]
            for exp in cv_data["experience"]:
                lines.append(f"{exp.get('title','')} | {exp.get('company','')} | {exp.get('start_date','')} – {exp.get('end_date','')}")
                if exp.get("location"):
                    lines.append(exp["location"])
                for b in exp.get("bullets", []):
                    lines.append(f"  - {b}")

        if cv_data.get("education"):
            lines += ["", "EDUCATION", "-" * 40]
            for edu in cv_data["education"]:
                lines.append(f"{edu.get('degree','')} in {edu.get('field','')} | {edu.get('institution','')}")
                lines.append(f"{edu.get('start_date','')} – {edu.get('end_date','')}")
                if edu.get("gpa"):
                    lines.append(f"GPA: {edu['gpa']}")

        skills = cv_data.get("skills", {})
        if any(skills.values()):
            lines += ["", "SKILLS", "-" * 40]
            if skills.get("technical"):
                lines.append("Technical: " + ", ".join(skills["technical"]))
            if skills.get("tools"):
                lines.append("Tools: " + ", ".join(skills["tools"]))
            if skills.get("soft"):
                lines.append("Soft Skills: " + ", ".join(skills["soft"]))

        if cv_data.get("projects"):
            lines += ["", "PROJECTS", "-" * 40]
            for proj in cv_data["projects"]:
                lines.append(proj.get("name", ""))
                if proj.get("description"):
                    lines.append(proj["description"])
                if proj.get("tech_stack"):
                    lines.append("Tech: " + ", ".join(proj["tech_stack"]))
                for b in proj.get("bullets", []):
                    lines.append(f"  - {b}")

        if cv_data.get("certifications"):
            lines += ["", "CERTIFICATIONS", "-" * 40]
            for cert in cv_data["certifications"]:
                lines.append(f"{cert.get('name','')} — {cert.get('issuer','')} ({cert.get('date','')})")

        return "\n".join(lines)

    async def generate(self, req: CVGenerateRequest) -> CVGenerateResponse:
        cv_data = self._build_cv_dict(req)

        self._validator.warnings.clear()
        cv_data = self._validator.validate(cv_data)
        cv_data = self._normalizer.normalize(cv_data)

        job_title = req.target_job_title or "General"
        cv_data = self._optimizer.optimize(cv_data, job_title, None)

        score_report = self._scorer.score(cv_data)
        suggestions_raw = self._suggester.suggest(cv_data)
        suggestions = [s["message"] for s in suggestions_raw[:10]]

        cv_text = self._render_cv_text(cv_data)
        pdf_path = self._pdf_builder.build(cv_data, output_dir=OUTPUT_DIR)
        pdf_filename = os.path.basename(pdf_path)

        breakdown_raw = score_report.get("breakdown", {})

        def _get(key: str) -> int:
            return breakdown_raw.get(key, {}).get("score", 0)

        breakdown = ATSBreakdown(
            section_completeness=_get("section_completeness"),
            keyword_coverage=_get("keyword_coverage"),
            action_verb_quality=_get("action_verb_quality"),
            quantification=_get("quantification"),
            formatting_quality=_get("formatting_quality"),
            contact_completeness=_get("contact_completeness"),
        )

        ats_meta = cv_data.get("meta", {}).get("ats_optimization", {})

        logger.info(f"CV generated for '{req.personal.name}' — ATS score={score_report['total_score']}")

        return CVGenerateResponse(
            cv_text=cv_text,
            ats_score=score_report["total_score"],
            ats_grade=score_report["grade"],
            ats_breakdown=breakdown,
            matched_keywords=ats_meta.get("matched_keywords", []),
            missing_keywords=ats_meta.get("missing_keywords", [])[:10],
            suggestions=suggestions,
            pdf_url=f"/api/v1/cv/download-cv/{pdf_filename}",
        )
