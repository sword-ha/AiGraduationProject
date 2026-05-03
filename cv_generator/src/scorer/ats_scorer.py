"""
ats_scorer.py
-------------
Evaluates how ATS-friendly a CV is and returns a detailed score report.

Scoring dimensions (total 100 points)
--------------------------------------
| Dimension               | Max pts | Description                              |
|-------------------------|---------|------------------------------------------|
| Section completeness    |   30    | All key sections present and non-empty   |
| Keyword coverage        |   25    | % of target keywords found in CV         |
| Action verb quality     |   15    | Strong action verbs in experience bullets|
| Quantification          |   15    | Numbers/metrics in experience bullets    |
| Formatting quality      |   10    | Length, no special chars, clean text     |
| Contact completeness    |    5    | Name, email, phone present               |

A final letter grade is also assigned:
  90-100 → A+   Excellent ATS compatibility
  80-89  → A    Very good
  70-79  → B    Good, minor improvements needed
  60-69  → C    Average, several improvements needed
  50-59  → D    Poor ATS compatibility
  <50    → F    Major overhaul recommended
"""

import re
from typing import Any, Dict, List, Tuple


class ATSScorer:
    """
    Scores a CV dictionary against ATS best-practice rules.

    Usage
    -----
        scorer = ATSScorer()
        report = scorer.score(cv_data)
        print(report["total_score"])     # 0-100
        print(report["grade"])           # e.g. "A"
        for dim, details in report["breakdown"].items():
            print(dim, details["score"], "/", details["max"])
    """

    # ------------------------------------------------------------------ #
    #  Strong action verb list (subset — extend freely)                   #
    # ------------------------------------------------------------------ #
    _STRONG_VERBS = {
        "achieved", "accelerated", "architected", "automated", "boosted",
        "built", "collaborated", "conceptualized", "configured", "contributed",
        "created", "delivered", "deployed", "designed", "developed",
        "directed", "drove", "engineered", "enhanced", "established",
        "evaluated", "executed", "facilitated", "generated", "implemented",
        "improved", "increased", "integrated", "launched", "led",
        "managed", "mentored", "migrated", "modeled", "monitored",
        "optimized", "orchestrated", "overhauled", "partnered", "planned",
        "produced", "reduced", "refactored", "researched", "resolved",
        "scaled", "secured", "shipped", "spearheaded", "streamlined",
        "transformed", "validated", "visualized", "authored", "championed",
        "consolidated", "coordinated", "cultivated", "defined", "demonstrated",
        "diagnosed", "enabled", "ensured", "expanded", "identified",
        "initiated", "introduced", "led", "maintained", "maximized",
        "minimized", "operated", "prioritized", "published", "rebuilt",
        "restructured", "standardised", "standardized", "supported",
    }

    _WEAK_VERBS = {
        "worked", "helped", "did", "made", "used", "got",
        "went", "handled", "tried", "fixed", "changed", "ran",
        "showed", "talked", "wrote", "assisted", "was", "were",
    }

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def score(self, cv_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute the full ATS score for the given CV data.

        Returns a dict with keys:
          total_score  : int (0-100)
          grade        : str ("A+", "A", "B", "C", "D", "F")
          breakdown    : dict of {dimension_name: {score, max, message, details}}
        """
        breakdown: Dict[str, Dict[str, Any]] = {}

        # 1. Section completeness
        sc_score, sc_msg, sc_details = self._score_sections(cv_data)
        breakdown["Section Completeness"] = {
            "score": sc_score, "max": 30,
            "message": sc_msg, "details": sc_details,
        }

        # 2. Keyword coverage
        kw_score, kw_msg, kw_details = self._score_keywords(cv_data)
        breakdown["Keyword Coverage"] = {
            "score": kw_score, "max": 25,
            "message": kw_msg, "details": kw_details,
        }

        # 3. Action verb quality
        av_score, av_msg, av_details = self._score_action_verbs(cv_data)
        breakdown["Action Verb Quality"] = {
            "score": av_score, "max": 15,
            "message": av_msg, "details": av_details,
        }

        # 4. Quantification
        qt_score, qt_msg, qt_details = self._score_quantification(cv_data)
        breakdown["Quantification"] = {
            "score": qt_score, "max": 15,
            "message": qt_msg, "details": qt_details,
        }

        # 5. Formatting quality
        fq_score, fq_msg, fq_details = self._score_formatting(cv_data)
        breakdown["Formatting Quality"] = {
            "score": fq_score, "max": 10,
            "message": fq_msg, "details": fq_details,
        }

        # 6. Contact completeness
        cc_score, cc_msg, cc_details = self._score_contact(cv_data)
        breakdown["Contact Completeness"] = {
            "score": cc_score, "max": 5,
            "message": cc_msg, "details": cc_details,
        }

        total = sum(d["score"] for d in breakdown.values())
        grade = self._grade(total)

        report = {
            "total_score": total,
            "grade":       grade,
            "breakdown":   breakdown,
        }

        # Store in meta for GUI / other modules to read
        cv_data.setdefault("meta", {})
        cv_data["meta"]["ats_score_report"] = report

        return report

    # ------------------------------------------------------------------ #
    #  Scoring dimensions                                                  #
    # ------------------------------------------------------------------ #

    def _score_sections(
        self, cv_data: Dict[str, Any]
    ) -> Tuple[int, str, List[str]]:
        """Award points for having all essential CV sections populated."""
        max_pts = 30
        details: List[str] = []
        score   = 0

        checks = [
            ("personal.name",    cv_data.get("personal", {}).get("name", ""),       4),
            ("summary",          cv_data.get("personal", {}).get("summary", ""),    4),
            ("experience",       cv_data.get("experience", []),                      8),
            ("education",        cv_data.get("education",  []),                      6),
            ("skills.technical", cv_data.get("skills", {}).get("technical", []),     5),
            ("projects",         cv_data.get("projects",  []),                       3),
        ]

        for section_name, value, pts in checks:
            present = bool(value)
            if present:
                score += pts
                details.append(f"[+{pts}] {section_name} — present")
            else:
                details.append(f"[ 0] {section_name} — MISSING")

        pct = score / max_pts * 100
        msg = (
            "All key sections present."
            if score == max_pts
            else f"Missing sections reduce your score ({score}/{max_pts})."
        )
        return score, msg, details

    def _score_keywords(
        self, cv_data: Dict[str, Any]
    ) -> Tuple[int, str, List[str]]:
        """Scale keyword coverage percentage to 0-25 points."""
        max_pts     = 25
        ats_opt     = cv_data.get("meta", {}).get("ats_optimization", {})
        coverage    = ats_opt.get("keyword_coverage_pct", 0.0)
        matched     = ats_opt.get("matched_keywords", [])
        missing_top = ats_opt.get("missing_keywords", [])[:5]

        if not ats_opt:
            # Optimiser hasn't run yet — partial credit based on skill count
            skill_count = sum(
                len(v) for v in cv_data.get("skills", {}).values()
            )
            score = min(max_pts, skill_count)
            return score, f"Run optimiser for precise score. Estimated: {score}/{max_pts}.", []

        score = int(coverage / 100 * max_pts)
        details: List[str] = [
            f"Coverage: {coverage:.1f}%  ({len(matched)} keywords matched)",
        ]
        if missing_top:
            details.append(f"Top missing: {', '.join(missing_top)}")

        msg = (
            f"Good keyword coverage ({coverage:.0f}%)."
            if coverage >= 60
            else f"Low keyword coverage ({coverage:.0f}%) — add more relevant keywords."
        )
        return score, msg, details

    def _score_action_verbs(
        self, cv_data: Dict[str, Any]
    ) -> Tuple[int, str, List[str]]:
        """Award points based on the proportion of bullets with strong action verbs."""
        max_pts = 15
        bullets = self._collect_all_bullets(cv_data)
        if not bullets:
            return 0, "No experience bullets found.", []

        strong_count = 0
        weak_found:  List[str] = []
        details:     List[str] = []

        for bullet in bullets:
            first_word = re.match(r"^[\-\*\•]?\s*(\w+)", bullet)
            if first_word:
                word = first_word.group(1).lower()
                if word in self._STRONG_VERBS:
                    strong_count += 1
                elif word in self._WEAK_VERBS:
                    weak_found.append(first_word.group(1))

        ratio = strong_count / len(bullets)
        score = int(ratio * max_pts)

        details.append(f"{strong_count}/{len(bullets)} bullets start with a strong verb.")
        if weak_found:
            details.append(f"Weak verbs detected: {', '.join(set(weak_found))}")

        msg = (
            "Strong action verbs used throughout."
            if ratio >= 0.8
            else f"Improve action verbs — {strong_count}/{len(bullets)} are strong."
        )
        return score, msg, details

    def _score_quantification(
        self, cv_data: Dict[str, Any]
    ) -> Tuple[int, str, List[str]]:
        """Award points for experience bullets containing numbers/metrics."""
        max_pts = 15
        bullets = self._collect_all_bullets(cv_data)
        if not bullets:
            return 0, "No experience bullets found.", []

        # Pattern: any digit (percentage, count, dollar, X-fold, etc.)
        number_pattern = re.compile(r"\d+[\.,]?\d*\s*(%|x|\$|k|M|million|billion)?", re.I)

        quantified = sum(1 for b in bullets if number_pattern.search(b))
        ratio  = quantified / len(bullets)
        score  = int(ratio * max_pts)
        details = [f"{quantified}/{len(bullets)} bullets contain quantifiable metrics."]

        msg = (
            "Good use of metrics and numbers."
            if ratio >= 0.5
            else "Add more measurable results — numbers make bullets 40% more impactful."
        )
        return score, msg, details

    def _score_formatting(
        self, cv_data: Dict[str, Any]
    ) -> Tuple[int, str, List[str]]:
        """
        Award points for clean formatting:
          - Summary word count in 30-80 range
          - No excessive special characters
          - Experience has at least 2 bullets per role
        """
        max_pts = 10
        score   = 10
        issues: List[str] = []

        # Check summary length
        summary = cv_data.get("personal", {}).get("summary", "")
        wc = len(summary.split())
        if wc < 20:
            score -= 3
            issues.append(f"Summary is too short ({wc} words; aim for 30-80).")
        elif wc > 120:
            score -= 2
            issues.append(f"Summary is too long ({wc} words; aim for 30-80).")

        # Check experience bullet count
        for exp in cv_data.get("experience", []):
            bullets = [b for b in exp.get("bullets", []) if b.strip()]
            if len(bullets) < 2:
                score -= 2
                issues.append(
                    f"'{exp.get('title', 'Role')} at {exp.get('company', '')}' "
                    f"has only {len(bullets)} bullet(s) — add at least 3."
                )
                break  # penalise once

        # Check for special chars that confuse parsers
        all_text = " ".join(
            b for exp in cv_data.get("experience", [])
            for b in exp.get("bullets", [])
        )
        if re.search(r"[^\x00-\x7F]", all_text):
            score -= 1
            issues.append("Non-ASCII characters found in bullets — may confuse some ATS.")

        score = max(0, score)
        details = issues if issues else ["Formatting looks clean."]
        msg = "Clean formatting." if not issues else "; ".join(issues[:2])
        return score, msg, details

    def _score_contact(
        self, cv_data: Dict[str, Any]
    ) -> Tuple[int, str, List[str]]:
        """Award 1-2 points per essential contact field."""
        max_pts = 5
        personal = cv_data.get("personal", {})
        details: List[str] = []
        score   = 0

        for field, pts in [("name", 2), ("email", 2), ("phone", 1)]:
            if personal.get(field, "").strip():
                score += pts
                details.append(f"[+{pts}] {field} present")
            else:
                details.append(f"[ 0] {field} MISSING")

        msg = (
            "All essential contact details present."
            if score == max_pts
            else "Missing contact fields — fill them in."
        )
        return score, msg, details

    # ------------------------------------------------------------------ #
    #  Utilities                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _collect_all_bullets(cv_data: Dict[str, Any]) -> List[str]:
        """Return all bullet-point strings from experience entries."""
        return [
            b
            for exp in cv_data.get("experience", [])
            for b in exp.get("bullets", [])
            if b.strip()
        ]

    @staticmethod
    def _grade(score: int) -> str:
        """Convert a numeric score (0-100) to a letter grade."""
        if score >= 90: return "A+"
        if score >= 80: return "A"
        if score >= 70: return "B"
        if score >= 60: return "C"
        if score >= 50: return "D"
        return "F"
