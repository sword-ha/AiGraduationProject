"""
pdf_builder.py
--------------
Generates an ATS-friendly PDF CV using ReportLab's Platypus framework.

ATS-friendly design choices:
  - Single-column layout (no tables for content)
  - Standard fonts: Helvetica (sans-serif)
  - Clean section dividers using HRFlowable
  - Machine-readable text (no images, no text boxes)
  - Consistent heading hierarchy: Name > Section > Sub-section
  - Bullet character is a plain ASCII hyphen to avoid Unicode issues
  - No headers/footers that may confuse parsers
"""

import os
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


class PDFBuilder:
    """
    Builds an ATS-optimised single-page (or multi-page) PDF from a CV dict.

    Usage
    -----
        builder = PDFBuilder()
        path = builder.build(cv_data, output_dir="output")
    """

    # ------------------------------------------------------------------ #
    #  Style constants                                                     #
    # ------------------------------------------------------------------ #
    _FONT          = "Helvetica"
    _FONT_BOLD     = "Helvetica-Bold"
    _COLOR_DARK    = colors.HexColor("#1a1a2e")
    _COLOR_ACCENT  = colors.HexColor("#16213e")
    _COLOR_LINE    = colors.HexColor("#cccccc")

    # Page margins (left/right 2 cm, top/bottom 1.5 cm for more content)
    _MARGIN_H = 2.0 * cm
    _MARGIN_V = 1.5 * cm

    def __init__(self) -> None:
        self._styles = self._build_styles()

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def build(self, cv_data: Dict[str, Any], output_dir: str = "output") -> str:
        """
        Render cv_data to a PDF file and return the output file path.
        """
        os.makedirs(output_dir, exist_ok=True)

        # Create a safe filename from the candidate's name
        name_slug = self._slug(cv_data.get("personal", {}).get("name", "cv"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"{name_slug}_cv_{timestamp}.pdf"
        filepath  = os.path.join(output_dir, filename)

        # Build the flowable story
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            leftMargin=self._MARGIN_H,
            rightMargin=self._MARGIN_H,
            topMargin=self._MARGIN_V,
            bottomMargin=self._MARGIN_V,
            title=cv_data.get("personal", {}).get("name", "CV"),
            author=cv_data.get("personal", {}).get("name", ""),
            subject="Curriculum Vitae",
        )

        story = self._build_story(cv_data)
        doc.build(story)
        return filepath

    # ------------------------------------------------------------------ #
    #  Story builder                                                       #
    # ------------------------------------------------------------------ #

    def _build_story(self, cv_data: Dict[str, Any]) -> List:
        """Assemble all flowable elements in reading order."""
        story: List = []
        personal = cv_data.get("personal", {})

        # ---- Header: Name & contact ----
        story += self._build_header(personal)

        # ---- Professional Summary ----
        summary = personal.get("summary", "").strip()
        if summary:
            story += self._build_section("Professional Summary")
            story.append(Paragraph(summary, self._styles["body_justify"]))
            story.append(Spacer(1, 0.3 * cm))

        # ---- Experience ----
        experience = cv_data.get("experience", [])
        if experience:
            story += self._build_section("Work Experience")
            for exp in experience:
                story += self._build_experience_entry(exp)

        # ---- Education ----
        education = cv_data.get("education", [])
        if education:
            story += self._build_section("Education")
            for edu in education:
                story += self._build_education_entry(edu)

        # ---- Skills ----
        skills = cv_data.get("skills", {})
        if any(skills.values()):
            story += self._build_section("Skills")
            story += self._build_skills(skills)

        # ---- Projects ----
        projects = cv_data.get("projects", [])
        if projects:
            story += self._build_section("Projects")
            for proj in projects:
                story += self._build_project_entry(proj)

        # ---- Certifications ----
        certs = cv_data.get("certifications", [])
        if certs:
            story += self._build_section("Certifications")
            for cert in certs:
                story += self._build_cert_entry(cert)

        return story

    # ------------------------------------------------------------------ #
    #  Header                                                              #
    # ------------------------------------------------------------------ #

    def _build_header(self, personal: Dict[str, str]) -> List:
        """Build the name + contact information header block."""
        elements: List = []

        # Candidate name — largest element on the page
        name = personal.get("name", "").upper()
        elements.append(Paragraph(name, self._styles["name"]))
        elements.append(Spacer(1, 0.2 * cm))

        # Contact line: Email  |  Phone  |  Location
        contact_parts = []
        if personal.get("email"):
            contact_parts.append(personal["email"])
        if personal.get("phone"):
            contact_parts.append(personal["phone"])
        if personal.get("location"):
            contact_parts.append(personal["location"])

        if contact_parts:
            elements.append(
                Paragraph("  |  ".join(contact_parts), self._styles["contact"])
            )

        # Links line: LinkedIn  |  GitHub  |  Website
        link_parts = []
        for field in ("linkedin", "github", "website"):
            val = personal.get(field, "").strip()
            if val:
                link_parts.append(val)

        if link_parts:
            elements.append(
                Paragraph("  |  ".join(link_parts), self._styles["contact"])
            )

        elements.append(Spacer(1, 0.1 * cm))
        elements.append(
            HRFlowable(width="100%", thickness=2, color=self._COLOR_ACCENT)
        )
        elements.append(Spacer(1, 0.25 * cm))
        return elements

    # ------------------------------------------------------------------ #
    #  Section divider                                                     #
    # ------------------------------------------------------------------ #

    def _build_section(self, title: str) -> List:
        """Return a section-header block with a thin rule beneath it."""
        return [
            Paragraph(title.upper(), self._styles["section_heading"]),
            HRFlowable(width="100%", thickness=0.75, color=self._COLOR_LINE),
            Spacer(1, 0.2 * cm),
        ]

    # ------------------------------------------------------------------ #
    #  Experience entry                                                    #
    # ------------------------------------------------------------------ #

    def _build_experience_entry(self, exp: Dict[str, Any]) -> List:
        """Render a single work-experience block."""
        elements: List = []

        # Line 1: Job Title at Company                     Date Range
        title   = exp.get("title", "")
        company = exp.get("company", "")
        dates   = self._date_range(exp.get("start_date"), exp.get("end_date"))
        loc     = exp.get("location", "")

        # Job title (bold) + company
        headline = f"<b>{title}</b> — {company}"
        if loc:
            headline += f", {loc}"
        elements.append(
            Paragraph(headline, self._styles["entry_title"])
        )

        # Date on the same line via a right-aligned paragraph trick
        if dates:
            elements.append(Paragraph(dates, self._styles["date_right"]))

        # Bullet points
        for bullet in exp.get("bullets", []):
            if bullet.strip():
                elements.append(
                    Paragraph(f"- {bullet}", self._styles["bullet"])
                )

        elements.append(Spacer(1, 0.3 * cm))
        return elements

    # ------------------------------------------------------------------ #
    #  Education entry                                                     #
    # ------------------------------------------------------------------ #

    def _build_education_entry(self, edu: Dict[str, Any]) -> List:
        """Render a single education block."""
        elements: List = []

        institution = edu.get("institution", "")
        degree      = edu.get("degree", "")
        field       = edu.get("field", "")
        gpa         = edu.get("gpa", "")
        dates       = self._date_range(edu.get("start_date"), edu.get("end_date"))

        # Degree line
        degree_text = degree
        if field:
            degree_text += f" in {field}"
        if gpa:
            degree_text += f" — GPA: {gpa}"

        elements.append(Paragraph(f"<b>{institution}</b>", self._styles["entry_title"]))
        if degree_text.strip():
            elements.append(Paragraph(degree_text, self._styles["entry_subtitle"]))
        if dates:
            elements.append(Paragraph(dates, self._styles["date_right"]))

        # Achievements
        for ach in edu.get("achievements", []):
            if ach.strip():
                elements.append(Paragraph(f"- {ach}", self._styles["bullet"]))

        elements.append(Spacer(1, 0.25 * cm))
        return elements

    # ------------------------------------------------------------------ #
    #  Skills                                                              #
    # ------------------------------------------------------------------ #

    def _build_skills(self, skills: Dict[str, List[str]]) -> List:
        """Render skills as labelled rows (no table — ATS friendly)."""
        elements: List = []
        label_map = {
            "technical": "Technical",
            "soft":      "Soft Skills",
            "tools":     "Tools & Technologies",
        }
        for key, label in label_map.items():
            skill_list = skills.get(key, [])
            if skill_list:
                text = f"<b>{label}:</b>  {',  '.join(skill_list)}"
                elements.append(Paragraph(text, self._styles["skill_row"]))
        elements.append(Spacer(1, 0.2 * cm))
        return elements

    # ------------------------------------------------------------------ #
    #  Projects                                                            #
    # ------------------------------------------------------------------ #

    def _build_project_entry(self, proj: Dict[str, Any]) -> List:
        """Render a single project block."""
        elements: List = []

        name = proj.get("name", "")
        desc = proj.get("description", "").strip()
        tech = proj.get("technologies", [])
        link = proj.get("link", "").strip()

        elements.append(Paragraph(f"<b>{name}</b>", self._styles["entry_title"]))
        if desc:
            elements.append(Paragraph(desc, self._styles["body"]))
        if tech:
            elements.append(
                Paragraph(
                    f"<b>Technologies:</b>  {', '.join(tech)}",
                    self._styles["entry_subtitle"],
                )
            )
        if link:
            elements.append(Paragraph(f"<b>Link:</b>  {link}", self._styles["entry_subtitle"]))

        elements.append(Spacer(1, 0.25 * cm))
        return elements

    # ------------------------------------------------------------------ #
    #  Certifications                                                      #
    # ------------------------------------------------------------------ #

    def _build_cert_entry(self, cert: Dict[str, str]) -> List:
        """Render a single certification line."""
        name   = cert.get("name", "")
        issuer = cert.get("issuer", "")
        date   = cert.get("date", "")

        text = f"<b>{name}</b>"
        if issuer:
            text += f" — {issuer}"
        if date:
            text += f" ({date})"

        return [
            Paragraph(text, self._styles["body"]),
            Spacer(1, 0.15 * cm),
        ]

    # ------------------------------------------------------------------ #
    #  Style definitions                                                   #
    # ------------------------------------------------------------------ #

    def _build_styles(self) -> Dict[str, ParagraphStyle]:
        """Create and return all named ParagraphStyles used in the CV."""
        base = getSampleStyleSheet()

        def _style(name: str, **kwargs) -> ParagraphStyle:
            return ParagraphStyle(name, parent=base["Normal"], **kwargs)

        return {
            # Candidate's name — centred, large, bold
            "name": _style(
                "CVName",
                fontName=self._FONT_BOLD,
                fontSize=22,
                leading=26,
                alignment=TA_CENTER,
                textColor=self._COLOR_DARK,
                spaceAfter=2,
            ),
            # Contact / link lines
            "contact": _style(
                "CVContact",
                fontName=self._FONT,
                fontSize=9,
                leading=12,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#444444"),
                spaceAfter=2,
            ),
            # SECTION HEADING (all-caps)
            "section_heading": _style(
                "CVSection",
                fontName=self._FONT_BOLD,
                fontSize=11,
                leading=14,
                textColor=self._COLOR_ACCENT,
                spaceAfter=2,
                spaceBefore=8,
            ),
            # Entry title line (company / institution)
            "entry_title": _style(
                "CVEntryTitle",
                fontName=self._FONT_BOLD,
                fontSize=10,
                leading=13,
                textColor=self._COLOR_DARK,
                spaceAfter=1,
            ),
            # Sub-title (degree / field)
            "entry_subtitle": _style(
                "CVEntrySubtitle",
                fontName=self._FONT,
                fontSize=9.5,
                leading=12,
                textColor=colors.HexColor("#333333"),
                spaceAfter=1,
            ),
            # Date range, right-aligned
            "date_right": _style(
                "CVDate",
                fontName=self._FONT,
                fontSize=9,
                leading=11,
                alignment=TA_LEFT,
                textColor=colors.HexColor("#666666"),
                spaceAfter=2,
            ),
            # Bullet points
            "bullet": _style(
                "CVBullet",
                fontName=self._FONT,
                fontSize=9.5,
                leading=13,
                leftIndent=12,
                spaceAfter=2,
                textColor=colors.HexColor("#222222"),
            ),
            # Skill rows
            "skill_row": _style(
                "CVSkillRow",
                fontName=self._FONT,
                fontSize=9.5,
                leading=13,
                spaceAfter=3,
            ),
            # Body paragraph (left-aligned)
            "body": _style(
                "CVBody",
                fontName=self._FONT,
                fontSize=9.5,
                leading=13,
                spaceAfter=3,
            ),
            # Body paragraph (justified)
            "body_justify": _style(
                "CVBodyJustify",
                fontName=self._FONT,
                fontSize=9.5,
                leading=13,
                alignment=TA_JUSTIFY,
                spaceAfter=4,
            ),
        }

    # ------------------------------------------------------------------ #
    #  Utilities                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _slug(text: str) -> str:
        """Convert a name to a filesystem-safe slug."""
        import re
        return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

    @staticmethod
    def _date_range(start: str, end: str) -> str:
        """Format start–end dates into a readable range string."""
        start = (start or "").strip()
        end   = (end   or "Present").strip()
        if start:
            return f"{start} – {end}"
        return end
