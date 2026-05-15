"""
input_collector.py
------------------
Responsible for gathering all CV data from the user via CLI prompts.
Supports multi-entry sections (education, experience, projects).
Returns a structured dictionary ready for validation.
"""

from typing import Dict, List, Any


class InputCollector:
    """
    Collects all user input required to build a CV.

    Sections collected:
      - Personal information
      - Education history (multiple entries)
      - Work experience (multiple entries)
      - Skills (technical, soft, tools)
      - Projects (multiple entries)
      - Certifications (optional)
    """

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def collect(self) -> Dict[str, Any]:
        """
        Drive the full CLI interview and return a structured CV dict.
        """
        print("\n" + "=" * 60)
        print("  Welcome to the ATS CV Generator — Let's build your CV!")
        print("=" * 60)
        print("Tip: Press Enter to skip optional fields.\n")

        cv_data: Dict[str, Any] = {
            "personal":       self._collect_personal(),
            "education":      self._collect_education(),
            "experience":     self._collect_experience(),
            "skills":         self._collect_skills(),
            "projects":       self._collect_projects(),
            "certifications": self._collect_certifications(),
            "meta":           {},
        }
        return cv_data

    # ------------------------------------------------------------------ #
    #  Section collectors                                                  #
    # ------------------------------------------------------------------ #

    def _collect_personal(self) -> Dict[str, str]:
        """Collect basic contact and profile information."""
        self._section_header("PERSONAL INFORMATION")
        return {
            "name":     self._ask("Full Name", required=True),
            "email":    self._ask("Email Address", required=True),
            "phone":    self._ask("Phone Number", required=True),
            "linkedin": self._ask("LinkedIn URL (optional)"),
            "github":   self._ask("GitHub URL (optional)"),
            "location": self._ask("Location, e.g. New York, NY (optional)"),
            "website":  self._ask("Personal Website (optional)"),
            "summary":  self._ask_multiline(
                "Professional Summary (2-4 sentences — or press Enter to skip)"
            ),
        }

    def _collect_education(self) -> List[Dict[str, Any]]:
        """Collect one or more education entries."""
        self._section_header("EDUCATION")
        print("Enter your education history. You can add multiple entries.")
        entries: List[Dict[str, Any]] = []
        index = 1
        while True:
            print(f"\n  [Education #{index}]")
            institution = self._ask("  Institution Name", required=(index == 1))
            if not institution:
                break
            entry = {
                "institution": institution,
                "degree":      self._ask("  Degree (e.g. Bachelor of Science)"),
                "field":       self._ask("  Field of Study (e.g. Computer Science)"),
                "start_date":  self._ask("  Start Date (e.g. Sep 2018)"),
                "end_date":    self._ask("  End Date (e.g. Jun 2022 or Present)"),
                "gpa":         self._ask("  GPA (optional)"),
                "achievements": self._ask_list(
                    "  Achievements / Activities (one per line, blank to finish)"
                ),
            }
            entries.append(entry)
            index += 1
            if not self._ask_yes_no("  Add another education entry?"):
                break
        return entries

    def _collect_experience(self) -> List[Dict[str, Any]]:
        """Collect one or more work experience entries."""
        self._section_header("WORK EXPERIENCE")
        print("Enter your work experience. List most recent first.")
        entries: List[Dict[str, Any]] = []
        index = 1
        while True:
            print(f"\n  [Experience #{index}]")
            company = self._ask("  Company Name", required=(index == 1))
            if not company:
                break
            entry = {
                "company":    company,
                "title":      self._ask("  Job Title"),
                "start_date": self._ask("  Start Date (e.g. Jul 2022)"),
                "end_date":   self._ask("  End Date (e.g. Present)"),
                "location":   self._ask("  Location (optional)"),
                "bullets":    self._ask_list(
                    "  Key Achievements / Responsibilities\n"
                    "  (one bullet per line, start with an action verb, blank to finish)"
                ),
            }
            entries.append(entry)
            index += 1
            if not self._ask_yes_no("  Add another experience entry?"):
                break
        return entries

    def _collect_skills(self) -> Dict[str, List[str]]:
        """Collect skills grouped by category."""
        self._section_header("SKILLS")
        print("Enter skills as comma-separated values.\n")
        return {
            "technical": self._ask_csv(
                "Technical Skills (e.g. Python, SQL, Docker, AWS)"
            ),
            "soft": self._ask_csv(
                "Soft Skills (e.g. Leadership, Communication, Problem-solving)"
            ),
            "tools": self._ask_csv(
                "Tools & Technologies (e.g. Git, Jira, Figma)"
            ),
        }

    def _collect_projects(self) -> List[Dict[str, Any]]:
        """Collect one or more personal / side projects."""
        self._section_header("PROJECTS")
        print("Enter notable projects (personal, open-source, academic).")
        entries: List[Dict[str, Any]] = []
        index = 1
        while True:
            print(f"\n  [Project #{index}]")
            name = self._ask("  Project Name", required=(index == 1))
            if not name:
                break
            entry = {
                "name":         name,
                "description":  self._ask_multiline(
                    "  Brief Description (what it does, your role, impact)"
                ),
                "technologies": self._ask_csv(
                    "  Technologies Used (e.g. Python, React, PostgreSQL)"
                ),
                "link":         self._ask("  Project Link (GitHub / Live URL, optional)"),
            }
            entries.append(entry)
            index += 1
            if not self._ask_yes_no("  Add another project?"):
                break
        return entries

    def _collect_certifications(self) -> List[Dict[str, str]]:
        """Collect optional certification entries."""
        self._section_header("CERTIFICATIONS (Optional)")
        if not self._ask_yes_no("Do you have any certifications to add?"):
            return []
        entries: List[Dict[str, str]] = []
        index = 1
        while True:
            print(f"\n  [Certification #{index}]")
            name = self._ask("  Certification Name")
            if not name:
                break
            entry = {
                "name":   name,
                "issuer": self._ask("  Issuing Organization"),
                "date":   self._ask("  Date Obtained (e.g. Mar 2023)"),
                "id":     self._ask("  Credential ID (optional)"),
            }
            entries.append(entry)
            index += 1
            if not self._ask_yes_no("  Add another certification?"):
                break
        return entries

    # ------------------------------------------------------------------ #
    #  Helper input methods                                                #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _ask(prompt: str, required: bool = False) -> str:
        """
        Prompt for a single-line string input.
        If required=True, re-prompt until a non-empty value is entered.
        """
        suffix = " *" if required else ""
        while True:
            value = input(f"  {prompt}{suffix}: ").strip()
            if value or not required:
                return value
            print("  (This field is required — please enter a value.)")

    @staticmethod
    def _ask_multiline(prompt: str) -> str:
        """
        Prompt for multi-line text.
        User types content and presses Enter on a blank line to finish.
        """
        print(f"  {prompt}")
        print("  (Enter text; press Enter on a blank line when done)")
        lines: List[str] = []
        while True:
            line = input("  > ")
            if not line:
                break
            lines.append(line)
        return " ".join(lines)

    @staticmethod
    def _ask_list(prompt: str) -> List[str]:
        """
        Collect multiple lines, each becoming a list item.
        A blank line terminates input.
        """
        print(f"  {prompt}:")
        items: List[str] = []
        while True:
            item = input("  - ").strip()
            if not item:
                break
            items.append(item)
        return items

    @staticmethod
    def _ask_csv(prompt: str) -> List[str]:
        """
        Collect a comma-separated string and return a list of tokens.
        """
        raw = input(f"  {prompt}: ").strip()
        if not raw:
            return []
        return [token.strip() for token in raw.split(",") if token.strip()]

    @staticmethod
    def _ask_yes_no(prompt: str) -> bool:
        """Prompt for a yes/no answer. Defaults to 'no' on empty input."""
        answer = input(f"  {prompt} (y/n) [n]: ").strip().lower()
        return answer in ("y", "yes")

    @staticmethod
    def _section_header(title: str) -> None:
        """Print a formatted section header."""
        print(f"\n{'─' * 60}")
        print(f"  {title}")
        print(f"{'─' * 60}")
