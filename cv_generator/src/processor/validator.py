"""
validator.py
------------
Validates and cleans all user-supplied CV data.

Rules applied:
  - Email must match RFC-5322 simplified pattern
  - Phone is normalised to a canonical format
  - URLs must look like valid HTTP(S) or bare domain links
  - Text fields are stripped of leading/trailing whitespace and
    collapsed internal whitespace
  - Required fields are flagged with a warning rather than hard-erroring
    so the rest of the pipeline can still run

Returns the cleaned cv_data dict and a list of ValidationWarning objects.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ------------------------------------------------------------------ #
#  Warning record                                                      #
# ------------------------------------------------------------------ #

@dataclass
class ValidationWarning:
    field: str
    message: str
    severity: str = "warning"   # "warning" | "error"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.field}: {self.message}"


# ------------------------------------------------------------------ #
#  Main validator class                                                #
# ------------------------------------------------------------------ #

class DataValidator:
    """
    Validates and sanitises the raw CV dictionary produced by InputCollector.

    Usage
    -----
        validator = DataValidator()
        clean_data = validator.validate(raw_data)
        # Inspect warnings:
        for w in validator.warnings:
            print(w)
    """

    # Simplified RFC-5322 email pattern
    _EMAIL_RE = re.compile(
        r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    )
    # Accepts +1-555-123-4567 / (555) 123-4567 / 5551234567 / +447911123456 etc.
    _PHONE_RE = re.compile(
        r"^[\+\d][\d\s\-\(\)\.]{6,19}$"
    )
    # Bare or full URL: linkedin.com/... or https://linkedin.com/...
    _URL_RE = re.compile(
        r"^(https?://)?"                       # optional scheme
        r"([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,}"    # domain
        r"(/[^\s]*)?$"                          # optional path
    )

    def __init__(self) -> None:
        self.warnings: List[ValidationWarning] = []

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def validate(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean the cv_data dict in-place.
        Appends ValidationWarning objects to self.warnings for any issues found.
        Returns the (possibly mutated) dict.
        """
        self.warnings.clear()

        cv_data["personal"]       = self._validate_personal(cv_data.get("personal", {}))
        cv_data["education"]      = self._validate_education(cv_data.get("education", []))
        cv_data["experience"]     = self._validate_experience(cv_data.get("experience", []))
        cv_data["skills"]         = self._validate_skills(cv_data.get("skills", {}))
        cv_data["projects"]       = self._validate_projects(cv_data.get("projects", []))
        cv_data["certifications"] = self._validate_certifications(
            cv_data.get("certifications", [])
        )

        # Surface any warnings to stdout so CLI users see them immediately
        if self.warnings:
            print("\n--- VALIDATION NOTICES ---")
            for w in self.warnings:
                print(f"  {w}")

        return cv_data

    # ------------------------------------------------------------------ #
    #  Section validators                                                  #
    # ------------------------------------------------------------------ #

    def _validate_personal(self, personal: Dict[str, str]) -> Dict[str, str]:
        """Clean and validate personal/contact fields."""
        # Required fields
        for req_field in ("name", "email", "phone"):
            if not personal.get(req_field, "").strip():
                self._warn("personal." + req_field, f"'{req_field}' is required.", "error")

        # Clean all text fields
        cleaned: Dict[str, str] = {k: self._clean_text(v) for k, v in personal.items()}

        # Email format check
        email = cleaned.get("email", "")
        if email and not self._EMAIL_RE.match(email):
            self._warn("personal.email", f"'{email}' does not look like a valid email.")
            # Attempt simple fix: strip spaces that crept in
            cleaned["email"] = email.replace(" ", "")

        # Phone normalisation
        phone = cleaned.get("phone", "")
        if phone:
            cleaned["phone"] = self._normalise_phone(phone)
            if not self._PHONE_RE.match(cleaned["phone"]):
                self._warn("personal.phone", f"'{phone}' does not look like a valid phone number.")

        # URL validation for linkedin / github / website
        for url_field in ("linkedin", "github", "website"):
            url = cleaned.get(url_field, "")
            if url and not self._URL_RE.match(url):
                self._warn(
                    f"personal.{url_field}",
                    f"'{url}' does not look like a valid URL.",
                )

        return cleaned

    def _validate_education(
        self, education: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate each education entry."""
        if not education:
            self._warn("education", "No education entries found.")
        cleaned = []
        for i, edu in enumerate(education):
            entry = {k: self._clean_text(str(v)) if isinstance(v, str) else v
                     for k, v in edu.items()}
            if not entry.get("institution"):
                self._warn(f"education[{i}].institution", "Institution name is missing.")
            # Ensure achievements is always a list
            if isinstance(entry.get("achievements"), str):
                entry["achievements"] = [
                    a.strip() for a in entry["achievements"].split(",") if a.strip()
                ]
            cleaned.append(entry)
        return cleaned

    def _validate_experience(
        self, experience: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate each experience entry and clean bullet points."""
        if not experience:
            self._warn("experience", "No work experience entries found.")
        cleaned = []
        for i, exp in enumerate(experience):
            entry = {k: self._clean_text(str(v)) if isinstance(v, str) else v
                     for k, v in exp.items()}
            if not entry.get("company"):
                self._warn(f"experience[{i}].company", "Company name is missing.")
            if not entry.get("title"):
                self._warn(f"experience[{i}].title", "Job title is missing.")
            # Clean bullet points
            bullets = entry.get("bullets", [])
            if isinstance(bullets, str):
                bullets = [b.strip() for b in bullets.split("\n") if b.strip()]
            entry["bullets"] = [
                self._clean_text(b) for b in bullets if b.strip()
            ]
            if not entry["bullets"]:
                self._warn(
                    f"experience[{i}].bullets",
                    "No bullet points for this role — consider adding achievements.",
                )
            cleaned.append(entry)
        return cleaned

    def _validate_skills(self, skills: Dict[str, Any]) -> Dict[str, List[str]]:
        """Deduplicate and clean each skills category."""
        cleaned: Dict[str, List[str]] = {}
        for category, skill_list in skills.items():
            if isinstance(skill_list, str):
                # Handle comma-separated strings that weren't pre-split
                skill_list = [s.strip() for s in skill_list.split(",") if s.strip()]
            deduped = list(dict.fromkeys(
                self._clean_text(s) for s in skill_list if s.strip()
            ))
            cleaned[category] = deduped
        if not any(cleaned.values()):
            self._warn("skills", "No skills provided — this section is critical for ATS.")
        return cleaned

    def _validate_projects(
        self, projects: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate project entries."""
        cleaned = []
        for i, proj in enumerate(projects):
            entry = {k: self._clean_text(str(v)) if isinstance(v, str) else v
                     for k, v in proj.items()}
            if not entry.get("name"):
                self._warn(f"projects[{i}].name", "Project name is missing.")
            # Ensure technologies is always a list
            techs = entry.get("technologies", [])
            if isinstance(techs, str):
                techs = [t.strip() for t in techs.split(",") if t.strip()]
            entry["technologies"] = techs
            cleaned.append(entry)
        return cleaned

    def _validate_certifications(
        self, certs: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Clean certification entries."""
        return [
            {k: self._clean_text(str(v)) for k, v in cert.items()}
            for cert in certs
            if cert.get("name", "").strip()
        ]

    # ------------------------------------------------------------------ #
    #  Utility helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Strip leading/trailing whitespace and collapse internal runs of
        whitespace to a single space.
        """
        return re.sub(r"\s+", " ", text).strip()

    @staticmethod
    def _normalise_phone(phone: str) -> str:
        """
        Light normalisation: strip unusual separators while preserving
        the leading '+' for international numbers.
        """
        # Keep digits, +, spaces, dashes, parens, and dots
        normalised = re.sub(r"[^\d\+\s\-\(\)\.]", "", phone).strip()
        return normalised

    def _warn(self, field: str, message: str, severity: str = "warning") -> None:
        """Append a ValidationWarning and print it immediately."""
        w = ValidationWarning(field=field, message=message, severity=severity)
        self.warnings.append(w)
