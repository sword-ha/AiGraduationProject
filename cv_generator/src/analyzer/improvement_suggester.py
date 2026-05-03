"""
improvement_suggester.py
------------------------
Rule-based CV improvement engine — no LLM required.

Rules implemented
-----------------
1.  Weak verbs          — detect first-word weak verbs in experience bullets
                          and suggest strong alternatives
2.  Missing sections    — flag any of: summary, projects, certifications
3.  Short bullets       — bullets under 8 words are too terse
4.  Duplicate phrases   — exact phrase repetition across all bullets
5.  Missing metrics     — bullets without any number or % sign
6.  Summary length      — too short (<20 words) or too long (>100 words)
7.  Missing LinkedIn    — ATS and recruiters use LinkedIn heavily
8.  Skill section gaps  — soft skills or tools category is empty
9.  Missing keywords    — top missing keywords from ATS optimiser
10. Single bullet roles — roles with only 1 bullet lack depth
11. Keyword stuffing    — more than 40 skills listed (hurts readability)
12. Missing dates       — experience/education entries without dates

Each suggestion is a dict:
  {
    "type":    "weak_verb" | "missing_section" | "quantification" | ...,
    "message": str,
    "field":   str,   # which part of the CV this refers to
    "priority": "high" | "medium" | "low",
  }
"""

import re
from collections import Counter
from typing import Any, Dict, List, Optional


class ImprovementSuggester:
    """
    Analyses a CV dictionary and returns a prioritised list of
    improvement suggestions, entirely rule-based.

    Usage
    -----
        suggester = ImprovementSuggester()
        suggestions = suggester.suggest(cv_data)
        for s in suggestions:
            print(f"[{s['priority'].upper()}] {s['message']}")
    """

    # ------------------------------------------------------------------ #
    #  Weak → strong verb map (subset; loaded from keywords.json if avail)#
    # ------------------------------------------------------------------ #
    _WEAK_VERB_MAP: Dict[str, str] = {
        "worked":              "Developed / Engineered / Built",
        "helped":              "Collaborated / Contributed / Supported",
        "did":                 "Executed / Completed / Delivered",
        "made":                "Created / Developed / Produced",
        "used":                "Leveraged / Utilised / Applied",
        "got":                 "Achieved / Obtained / Secured",
        "went":                "Transitioned / Progressed / Advanced",
        "handled":             "Managed / Oversaw / Administered",
        "tried":               "Piloted / Implemented / Tested",
        "fixed":               "Resolved / Debugged / Remediated",
        "changed":             "Improved / Enhanced / Optimised / Refactored",
        "ran":                 "Executed / Operated / Led",
        "showed":              "Demonstrated / Presented",
        "talked":              "Communicated / Presented / Negotiated",
        "wrote":               "Developed / Authored / Documented",
        "assisted":            "Supported / Contributed / Collaborated",
        "responsible for":     "Led / Managed / Owned",
        "was responsible for": "Led / Managed / Owned",
        "took care of":        "Managed / Administered",
    }

    def __init__(self, keywords_path: Optional[str] = None) -> None:
        """
        Optionally load the weak-verb map from keywords.json to stay
        in sync with the data file.
        """
        import json, os
        if keywords_path is None:
            base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            keywords_path = os.path.join(base, "data", "keywords.json")

        try:
            with open(keywords_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            # Merge JSON weak verbs into the class-level dict
            for weak, strong in data.get("weak_verbs", {}).items():
                self._WEAK_VERB_MAP[weak.lower()] = strong
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # fall back to the hard-coded map above

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def suggest(self, cv_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Return all improvement suggestions sorted by priority
        (high → medium → low).
        """
        suggestions: List[Dict[str, Any]] = []

        suggestions += self._check_weak_verbs(cv_data)
        suggestions += self._check_missing_sections(cv_data)
        suggestions += self._check_short_bullets(cv_data)
        suggestions += self._check_duplicate_phrases(cv_data)
        suggestions += self._check_missing_metrics(cv_data)
        suggestions += self._check_summary_length(cv_data)
        suggestions += self._check_linkedin(cv_data)
        suggestions += self._check_skill_gaps(cv_data)
        suggestions += self._check_missing_keywords(cv_data)
        suggestions += self._check_single_bullet_roles(cv_data)
        suggestions += self._check_keyword_stuffing(cv_data)
        suggestions += self._check_missing_dates(cv_data)

        # Sort: high first, then medium, then low
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: priority_order.get(s["priority"], 99))

        return suggestions

    # ------------------------------------------------------------------ #
    #  Individual checks                                                   #
    # ------------------------------------------------------------------ #

    def _check_weak_verbs(self, cv_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flag experience bullets that start with a weak verb."""
        results: List[Dict[str, Any]] = []
        for i, exp in enumerate(cv_data.get("experience", [])):
            for bullet in exp.get("bullets", []):
                first = re.match(r"^[\-\*\•]?\s*(\w[\w\s]{0,20})", bullet)
                if not first:
                    continue
                phrase = first.group(1).strip().lower()
                # Check the first 1-3 words against weak patterns
                for weak_phrase, strong_options in self._WEAK_VERB_MAP.items():
                    if phrase.startswith(weak_phrase):
                        results.append({
                            "type":     "weak_verb",
                            "field":    f"experience[{i}].bullets",
                            "priority": "high",
                            "message":  (
                                f"Weak verb detected: \"{first.group(1).strip()[:30]}…\"\n"
                                f"          → Consider: {strong_options}"
                            ),
                        })
                        break   # one suggestion per bullet is enough
        return results

    def _check_missing_sections(self, cv_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest adding sections that are absent."""
        results: List[Dict[str, Any]] = []

        if not cv_data.get("personal", {}).get("summary", "").strip():
            results.append({
                "type": "missing_section", "field": "personal.summary",
                "priority": "high",
                "message": "Professional Summary is missing. "
                           "A 3-4 sentence summary greatly improves ATS ranking.",
            })

        if not cv_data.get("projects", []):
            results.append({
                "type": "missing_section", "field": "projects",
                "priority": "medium",
                "message": "No Projects section found. "
                           "Projects demonstrate applied skills and differentiate candidates.",
            })

        if not cv_data.get("certifications", []):
            results.append({
                "type": "missing_section", "field": "certifications",
                "priority": "low",
                "message": "No Certifications listed. "
                           "Relevant certs (AWS, PMP, etc.) add credibility and keywords.",
            })

        return results

    def _check_short_bullets(self, cv_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flag bullets that are too short to be meaningful."""
        results: List[Dict[str, Any]] = []
        for i, exp in enumerate(cv_data.get("experience", [])):
            for j, bullet in enumerate(exp.get("bullets", [])):
                word_count = len(bullet.split())
                if 0 < word_count < 8:
                    results.append({
                        "type":     "short_bullet",
                        "field":    f"experience[{i}].bullets[{j}]",
                        "priority": "medium",
                        "message":  (
                            f"Bullet is too short ({word_count} words): \"{bullet[:60]}\"\n"
                            "          → Expand with context, tools used, and impact."
                        ),
                    })
        return results

    def _check_duplicate_phrases(
        self, cv_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect repeated phrases across all bullets (exact phrase matching)."""
        results: List[Dict[str, Any]] = []
        # Collect all 3-word n-grams from all bullets
        all_bullets = [
            b for exp in cv_data.get("experience", [])
            for b in exp.get("bullets", []) if b.strip()
        ]
        ngrams: List[str] = []
        for bullet in all_bullets:
            words = re.findall(r"\w+", bullet.lower())
            ngrams += [" ".join(words[i:i+3]) for i in range(len(words) - 2)]

        counter = Counter(ngrams)
        duplicates = [ngram for ngram, count in counter.items() if count >= 2]

        if duplicates:
            top = duplicates[:3]
            results.append({
                "type":     "duplicate_phrases",
                "field":    "experience.bullets",
                "priority": "medium",
                "message":  (
                    f"Repeated phrases detected (e.g. \"{top[0]}\"). "
                    "Vary your language to avoid ATS de-duplication penalties."
                ),
            })
        return results

    def _check_missing_metrics(
        self, cv_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Flag if fewer than 40% of bullets contain quantifiable data."""
        results: List[Dict[str, Any]] = []
        bullets = [
            b for exp in cv_data.get("experience", [])
            for b in exp.get("bullets", []) if b.strip()
        ]
        if not bullets:
            return results

        number_re = re.compile(r"\d+")
        quantified = sum(1 for b in bullets if number_re.search(b))
        ratio = quantified / len(bullets)

        if ratio < 0.4:
            results.append({
                "type":     "missing_metrics",
                "field":    "experience.bullets",
                "priority": "high",
                "message":  (
                    f"Only {quantified}/{len(bullets)} bullets include numbers or metrics. "
                    "Quantify impact: 'Reduced load time by 35%', "
                    "'Managed team of 8 engineers', 'Processed 2M records/day'."
                ),
            })
        return results

    def _check_summary_length(
        self, cv_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Flag summaries that are too short or too long."""
        results: List[Dict[str, Any]] = []
        summary = cv_data.get("personal", {}).get("summary", "").strip()
        if not summary:
            return results   # handled by missing_sections check

        wc = len(summary.split())
        if wc < 20:
            results.append({
                "type": "summary_length", "field": "personal.summary",
                "priority": "medium",
                "message": (
                    f"Summary is too brief ({wc} words). "
                    "Aim for 40-80 words covering your role, experience, and key skills."
                ),
            })
        elif wc > 100:
            results.append({
                "type": "summary_length", "field": "personal.summary",
                "priority": "low",
                "message": (
                    f"Summary is too long ({wc} words). "
                    "Recruiters spend ~7 seconds on the first pass — keep it under 80 words."
                ),
            })
        return results

    def _check_linkedin(self, cv_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest adding a LinkedIn URL if missing."""
        results: List[Dict[str, Any]] = []
        if not cv_data.get("personal", {}).get("linkedin", "").strip():
            results.append({
                "type": "missing_linkedin", "field": "personal.linkedin",
                "priority": "medium",
                "message": "LinkedIn URL is missing. 87% of recruiters use LinkedIn "
                           "to verify candidates.",
            })
        return results

    def _check_skill_gaps(self, cv_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Flag if soft skills or tools categories are empty."""
        results: List[Dict[str, Any]] = []
        skills = cv_data.get("skills", {})

        if not skills.get("technical", []):
            results.append({
                "type": "empty_skills_category", "field": "skills.technical",
                "priority": "high",
                "message": "Technical Skills section is empty — this is critical for ATS parsing.",
            })
        if not skills.get("soft", []):
            results.append({
                "type": "empty_skills_category", "field": "skills.soft",
                "priority": "low",
                "message": "Soft Skills are empty. Adding 3-5 soft skills rounds out your profile.",
            })
        if not skills.get("tools", []):
            results.append({
                "type": "empty_skills_category", "field": "skills.tools",
                "priority": "low",
                "message": "Tools & Technologies section is empty. "
                           "List IDEs, platforms, and productivity tools.",
            })
        return results

    def _check_missing_keywords(
        self, cv_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Surface top missing ATS keywords from the optimiser's output."""
        results: List[Dict[str, Any]] = []
        ats_opt = cv_data.get("meta", {}).get("ats_optimization", {})
        missing = ats_opt.get("missing_keywords", [])[:8]

        if missing:
            results.append({
                "type":     "missing_keywords",
                "field":    "skills / experience",
                "priority": "high",
                "message":  (
                    "High-value keywords not found in your CV:\n"
                    f"          {', '.join(missing)}\n"
                    "          → Add them naturally in Skills, Experience, or Projects."
                ),
            })
        return results

    def _check_single_bullet_roles(
        self, cv_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Flag experience entries with only one bullet point."""
        results: List[Dict[str, Any]] = []
        for i, exp in enumerate(cv_data.get("experience", [])):
            bullets = [b for b in exp.get("bullets", []) if b.strip()]
            if len(bullets) == 1:
                results.append({
                    "type":     "thin_experience",
                    "field":    f"experience[{i}]",
                    "priority": "medium",
                    "message":  (
                        f"'{exp.get('title', 'Role')} at {exp.get('company', '')}' "
                        "has only 1 bullet. Add 3-5 achievements to show depth."
                    ),
                })
        return results

    def _check_keyword_stuffing(
        self, cv_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Warn if the skills section has an excessive number of items."""
        results: List[Dict[str, Any]] = []
        skills = cv_data.get("skills", {})
        total_skills = sum(len(v) for v in skills.values())

        if total_skills > 40:
            results.append({
                "type":     "keyword_stuffing",
                "field":    "skills",
                "priority": "low",
                "message":  (
                    f"Skills section has {total_skills} items — this may look like "
                    "keyword stuffing. Keep the most relevant 20-30 skills."
                ),
            })
        return results

    def _check_missing_dates(
        self, cv_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Flag experience or education entries that lack start/end dates."""
        results: List[Dict[str, Any]] = []

        for i, exp in enumerate(cv_data.get("experience", [])):
            if not exp.get("start_date", "").strip():
                results.append({
                    "type":     "missing_dates",
                    "field":    f"experience[{i}]",
                    "priority": "medium",
                    "message":  (
                        f"'{exp.get('company', 'Experience entry')}' is missing a start date. "
                        "ATS systems use dates to calculate tenure."
                    ),
                })

        for i, edu in enumerate(cv_data.get("education", [])):
            if not edu.get("start_date", "").strip() and not edu.get("end_date", "").strip():
                results.append({
                    "type":     "missing_dates",
                    "field":    f"education[{i}]",
                    "priority": "low",
                    "message":  (
                        f"'{edu.get('institution', 'Education entry')}' has no dates. "
                        "Add graduation year at minimum."
                    ),
                })

        return results
