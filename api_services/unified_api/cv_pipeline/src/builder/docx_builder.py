"""
docx_builder.py
---------------
Generates an ATS-friendly DOCX CV using the python-docx library.

ATS design notes for DOCX:
  - Uses Heading 1 for name, Heading 2 for sections
  - No text boxes, no floating images, no tables for layout
  - Consistent paragraph styles throughout
  - Uses built-in Word styles so ATS parsers recognise them
  - Font: Calibri (universal, ATS-safe)
"""

import os
from datetime import datetime
from typing import Any, Dict, List

try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches, Pt, RGBColor
    _DOCX_AVAILABLE = True
except ImportError:
    _DOCX_AVAILABLE = False


class DOCXBuilder:
    """
    Builds an ATS-optimised DOCX from a CV dictionary.

    Raises ImportError on construction if python-docx is not installed.

    Usage
    -----
        builder = DOCXBuilder()
        path = builder.build(cv_data, output_dir="output")
    """

    _FONT_NAME   = "Calibri"
    _COLOR_DARK  = RGBColor(0x1A, 0x1A, 0x2E) if _DOCX_AVAILABLE else None
    _COLOR_GREY  = RGBColor(0x66, 0x66, 0x66) if _DOCX_AVAILABLE else None

    def __init__(self) -> None:
        if not _DOCX_AVAILABLE:
            raise ImportError(
                "python-docx is not installed. Run: pip install python-docx"
            )

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def build(self, cv_data: Dict[str, Any], output_dir: str = "output") -> str:
        """Render cv_data to a .docx file and return the path."""
        os.makedirs(output_dir, exist_ok=True)

        name_slug = self._slug(cv_data.get("personal", {}).get("name", "cv"))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath  = os.path.join(output_dir, f"{name_slug}_cv_{timestamp}.docx")

        doc = Document()
        self._configure_document(doc)
        self._add_content(doc, cv_data)
        doc.save(filepath)
        return filepath

    # ------------------------------------------------------------------ #
    #  Document configuration                                             #
    # ------------------------------------------------------------------ #

    def _configure_document(self, doc: "Document") -> None:
        """Set page margins and default font to make it ATS-friendly."""
        from docx.oxml.ns import qn
        from docx.oxml   import OxmlElement

        section = doc.sections[0]
        section.top_margin    = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin   = Inches(1.0)
        section.right_margin  = Inches(1.0)

        # Set default font for the document
        style = doc.styles["Normal"]
        font  = style.font
        font.name = self._FONT_NAME
        font.size = Pt(10)

    # ------------------------------------------------------------------ #
    #  Content builder                                                     #
    # ------------------------------------------------------------------ #

    def _add_content(self, doc: "Document", cv_data: Dict[str, Any]) -> None:
        """Populate the document with all CV sections."""
        personal = cv_data.get("personal", {})

        # --- Header ---
        self._add_header(doc, personal)

        # --- Summary ---
        summary = personal.get("summary", "").strip()
        if summary:
            self._add_section_heading(doc, "Professional Summary")
            doc.add_paragraph(summary)

        # --- Experience ---
        experience = cv_data.get("experience", [])
        if experience:
            self._add_section_heading(doc, "Work Experience")
            for exp in experience:
                self._add_experience_entry(doc, exp)

        # --- Education ---
        education = cv_data.get("education", [])
        if education:
            self._add_section_heading(doc, "Education")
            for edu in education:
                self._add_education_entry(doc, edu)

        # --- Skills ---
        skills = cv_data.get("skills", {})
        if any(skills.values()):
            self._add_section_heading(doc, "Skills")
            self._add_skills(doc, skills)

        # --- Projects ---
        projects = cv_data.get("projects", [])
        if projects:
            self._add_section_heading(doc, "Projects")
            for proj in projects:
                self._add_project_entry(doc, proj)

        # --- Certifications ---
        certs = cv_data.get("certifications", [])
        if certs:
            self._add_section_heading(doc, "Certifications")
            for cert in certs:
                self._add_cert_entry(doc, cert)

    # ------------------------------------------------------------------ #
    #  Section helpers                                                     #
    # ------------------------------------------------------------------ #

    def _add_header(self, doc: "Document", personal: Dict[str, str]) -> None:
        """Add the name and contact information header."""
        # Name
        name_para = doc.add_paragraph()
        name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = name_para.add_run(personal.get("name", "").upper())
        run.bold = True
        run.font.size = Pt(20)
        run.font.name = self._FONT_NAME

        # Contact line
        contact_parts = []
        for field in ("email", "phone", "location"):
            val = personal.get(field, "").strip()
            if val:
                contact_parts.append(val)

        if contact_parts:
            contact_para = doc.add_paragraph("  |  ".join(contact_parts))
            contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in contact_para.runs:
                run.font.size = Pt(9)
                run.font.color.rgb = self._COLOR_GREY

        # Links line
        link_parts = []
        for field in ("linkedin", "github", "website"):
            val = personal.get(field, "").strip()
            if val:
                link_parts.append(val)

        if link_parts:
            link_para = doc.add_paragraph("  |  ".join(link_parts))
            link_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in link_para.runs:
                run.font.size = Pt(9)
                run.font.color.rgb = self._COLOR_GREY

        # Horizontal rule via paragraph border (bottom border)
        self._add_horizontal_rule(doc)

    def _add_section_heading(self, doc: "Document", title: str) -> None:
        """Add a bold, upper-cased section heading with spacing."""
        para = doc.add_paragraph()
        para.paragraph_format.space_before = Pt(10)
        para.paragraph_format.space_after  = Pt(2)
        run = para.add_run(title.upper())
        run.bold = True
        run.font.size = Pt(11)
        run.font.name = self._FONT_NAME
        # Bottom border for the heading
        self._add_paragraph_bottom_border(para)

    def _add_experience_entry(self, doc: "Document", exp: Dict[str, Any]) -> None:
        """Add a work experience block."""
        title   = exp.get("title", "")
        company = exp.get("company", "")
        dates   = self._date_range(exp.get("start_date"), exp.get("end_date"))
        loc     = exp.get("location", "")

        # Headline paragraph
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(1)
        r = p.add_run(f"{title}  —  {company}")
        r.bold = True
        r.font.size = Pt(10)
        r.font.name = self._FONT_NAME

        # Date + location line
        detail = []
        if dates:
            detail.append(dates)
        if loc:
            detail.append(loc)
        if detail:
            sub = doc.add_paragraph("  |  ".join(detail))
            sub.paragraph_format.space_after = Pt(2)
            for run in sub.runs:
                run.font.size = Pt(9)
                run.font.color.rgb = self._COLOR_GREY
                run.font.name = self._FONT_NAME

        # Bullets
        for bullet in exp.get("bullets", []):
            if bullet.strip():
                bp = doc.add_paragraph(style="List Bullet")
                bp.paragraph_format.left_indent = Inches(0.25)
                bp.paragraph_format.space_after = Pt(1)
                r = bp.add_run(bullet)
                r.font.size = Pt(10)
                r.font.name = self._FONT_NAME

        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def _add_education_entry(self, doc: "Document", edu: Dict[str, Any]) -> None:
        """Add an education block."""
        institution = edu.get("institution", "")
        degree      = edu.get("degree", "")
        field       = edu.get("field", "")
        gpa         = edu.get("gpa", "")
        dates       = self._date_range(edu.get("start_date"), edu.get("end_date"))

        p = doc.add_paragraph()
        r = p.add_run(institution)
        r.bold = True
        r.font.size = Pt(10)
        r.font.name = self._FONT_NAME

        degree_text = degree
        if field:
            degree_text += f" in {field}"
        if gpa:
            degree_text += f" — GPA: {gpa}"

        if degree_text.strip():
            dp = doc.add_paragraph(degree_text)
            dp.paragraph_format.space_after = Pt(1)
            for run in dp.runs:
                run.font.size = Pt(10)
                run.font.name = self._FONT_NAME

        if dates:
            date_p = doc.add_paragraph(dates)
            date_p.paragraph_format.space_after = Pt(2)
            for run in date_p.runs:
                run.font.size = Pt(9)
                run.font.color.rgb = self._COLOR_GREY
                run.font.name = self._FONT_NAME

        for ach in edu.get("achievements", []):
            if ach.strip():
                bp = doc.add_paragraph(style="List Bullet")
                bp.paragraph_format.left_indent = Inches(0.25)
                r = bp.add_run(ach)
                r.font.size = Pt(10)
                r.font.name = self._FONT_NAME

    def _add_skills(self, doc: "Document", skills: Dict[str, List[str]]) -> None:
        """Add skills as labelled rows."""
        label_map = {
            "technical": "Technical",
            "soft":      "Soft Skills",
            "tools":     "Tools & Technologies",
        }
        for key, label in label_map.items():
            skill_list = skills.get(key, [])
            if skill_list:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(3)
                label_run = p.add_run(f"{label}: ")
                label_run.bold = True
                label_run.font.size = Pt(10)
                label_run.font.name = self._FONT_NAME
                value_run = p.add_run(",  ".join(skill_list))
                value_run.font.size = Pt(10)
                value_run.font.name = self._FONT_NAME

    def _add_project_entry(self, doc: "Document", proj: Dict[str, Any]) -> None:
        """Add a project block."""
        name = proj.get("name", "")
        desc = proj.get("description", "").strip()
        tech = proj.get("technologies", [])
        link = proj.get("link", "").strip()

        p = doc.add_paragraph()
        r = p.add_run(name)
        r.bold = True
        r.font.size = Pt(10)
        r.font.name = self._FONT_NAME

        if desc:
            dp = doc.add_paragraph(desc)
            dp.paragraph_format.space_after = Pt(1)
            for run in dp.runs:
                run.font.size = Pt(10)
                run.font.name = self._FONT_NAME

        if tech:
            tp = doc.add_paragraph()
            tr = tp.add_run("Technologies: ")
            tr.bold = True
            tr.font.size = Pt(10)
            tr.font.name = self._FONT_NAME
            vr = tp.add_run(", ".join(tech))
            vr.font.size = Pt(10)
            vr.font.name = self._FONT_NAME

        if link:
            lp = doc.add_paragraph()
            lr = lp.add_run("Link: ")
            lr.bold = True
            lr.font.size = Pt(10)
            lr.font.name = self._FONT_NAME
            vr = lp.add_run(link)
            vr.font.size = Pt(10)
            vr.font.name = self._FONT_NAME

        doc.add_paragraph().paragraph_format.space_after = Pt(4)

    def _add_cert_entry(self, doc: "Document", cert: Dict[str, str]) -> None:
        """Add a certification line."""
        name   = cert.get("name", "")
        issuer = cert.get("issuer", "")
        date   = cert.get("date", "")

        text = name
        if issuer:
            text += f" — {issuer}"
        if date:
            text += f" ({date})"

        p = doc.add_paragraph(text)
        p.paragraph_format.space_after = Pt(3)
        for run in p.runs:
            run.font.size = Pt(10)
            run.font.name = self._FONT_NAME

    # ------------------------------------------------------------------ #
    #  OOXML helpers                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _add_horizontal_rule(doc: "Document") -> None:
        """Insert a thin horizontal line via paragraph bottom-border XML."""
        from docx.oxml.ns import qn
        from docx.oxml   import OxmlElement

        p    = doc.add_paragraph()
        pPr  = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"),   "single")
        bottom.set(qn("w:sz"),    "6")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "1a1a2e")
        pBdr.append(bottom)
        pPr.append(pBdr)
        p.paragraph_format.space_after = Pt(4)

    @staticmethod
    def _add_paragraph_bottom_border(para: Any) -> None:
        """Add a bottom border to a paragraph via OOXML."""
        from docx.oxml.ns import qn
        from docx.oxml   import OxmlElement

        pPr  = para._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"),   "single")
        bottom.set(qn("w:sz"),    "4")
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "AAAAAA")
        pBdr.append(bottom)
        pPr.append(pBdr)

    # ------------------------------------------------------------------ #
    #  Utilities                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _slug(text: str) -> str:
        import re
        return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")

    @staticmethod
    def _date_range(start: str, end: str) -> str:
        start = (start or "").strip()
        end   = (end   or "Present").strip()
        if start:
            return f"{start} – {end}"
        return end
