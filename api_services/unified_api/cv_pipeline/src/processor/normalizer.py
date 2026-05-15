"""
normalizer.py
-------------
Normalises skill names using a curated alias dictionary loaded from
data/keywords.json.

Examples:
  "js"         → "JavaScript"
  "react.js"   → "React"
  "k8s"        → "Kubernetes"
  "postgres"   → "PostgreSQL"

The normaliser also title-cases unknown skills so that the CV looks
consistent (e.g. "python" → "Python").
"""

import json
import os
from typing import Any, Dict, List, Optional


class SkillNormalizer:
    """
    Maps raw skill strings to their canonical names.

    The alias table is sourced from data/keywords.json under the key
    "skill_aliases".  Look-ups are case-insensitive.
    """

    def __init__(self, keywords_path: Optional[str] = None) -> None:
        """
        Load the alias table from the keywords JSON file.

        Parameters
        ----------
        keywords_path : str, optional
            Explicit path to keywords.json.  When omitted the file is
            located relative to this module's directory.
        """
        if keywords_path is None:
            # Walk up two levels: src/processor → src → project root → data/
            base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            keywords_path = os.path.join(base, "data", "keywords.json")

        with open(keywords_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        # Build a lower-case key → canonical value dict for O(1) look-ups
        raw_aliases: Dict[str, str] = data.get("skill_aliases", {})
        self._aliases: Dict[str, str] = {
            key.lower(): value for key, value in raw_aliases.items()
        }

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def normalize(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Walk through all skill lists (technical, soft, tools) and the
        technologies lists inside projects, normalising each skill token.

        Returns the mutated cv_data dict.
        """
        # --- skills section ---
        skills = cv_data.get("skills", {})
        for category in ("technical", "soft", "tools"):
            skills[category] = [
                self._normalize_skill(s) for s in skills.get(category, [])
            ]
        # Deduplicate after normalisation (e.g. "js" and "JavaScript" → one entry)
        for category in ("technical", "soft", "tools"):
            skills[category] = list(dict.fromkeys(skills[category]))

        cv_data["skills"] = skills

        # --- project technologies ---
        for project in cv_data.get("projects", []):
            project["technologies"] = list(dict.fromkeys(
                self._normalize_skill(t) for t in project.get("technologies", [])
            ))

        return cv_data

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _normalize_skill(self, skill: str) -> str:
        """
        Return the canonical form for a single skill token.

        1. Look up the lower-cased skill in the alias table.
        2. If not found, title-case the original string.
        """
        key = skill.strip().lower()
        canonical = self._aliases.get(key)
        if canonical:
            return canonical
        # Title-case multi-word skills; preserve all-caps acronyms unchanged
        return self._smart_title(skill.strip())

    @staticmethod
    def _smart_title(skill: str) -> str:
        """
        Title-case a skill string while preserving known acronyms and
        tokens that are already capitalised in a meaningful way.

        Examples:
          "python"    → "Python"
          "REST API"  → "REST API"   (already correct)
          "ci/cd"     → "CI/CD"      (upper-case short tokens)
        """
        # If the skill is short (≤5 chars) and contains no spaces → upper-case
        if len(skill) <= 5 and " " not in skill:
            return skill.upper()
        # Otherwise apply title-case
        return skill.title()


