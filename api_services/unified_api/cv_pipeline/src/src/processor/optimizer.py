"""
optimizer.py
------------
ATS keyword optimisation module.

Responsibilities
----------------
1. Extract all text from the CV and build a keyword frequency map.
2. Load the recommended keyword set for the target job title from
   data/keywords.json.
3. Compute a simple TF-IDF-inspired relevance score for each keyword
   present in the CV (no third-party ML library required).
4. Identify *missing* high-value keywords that the candidate should
   consider adding to their CV.
5. Attach optimisation metadata to cv_data["meta"]["ats_optimization"]
   so downstream modules (scorer, GUI) can read it.
"""

import json
import math
import os
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple


class ATSOptimizer:
    """
    Keyword-based ATS optimiser.

    The core algorithm:
      - Collect all words from the CV (summary, bullets, skills, etc.)
      - For a user-specified job title, load the target keyword list
      - Compute term-frequency for each target keyword
      - Report matched keywords, missing keywords, and a keyword coverage %
    """

    def __init__(self, keywords_path: Optional[str] = None) -> None:
        if keywords_path is None:
            base = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            keywords_path = os.path.join(base, "data", "keywords.json")

        with open(keywords_path, "r", encoding="utf-8") as fh:
            self._kw_data: Dict[str, Any] = json.load(fh)

        self._job_titles: Dict[str, Any] = self._kw_data.get("job_titles", {})

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    def optimize(
        self,
        cv_data: Dict[str, Any],
        job_title: str,
        job_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyse the CV against the target job title/description and attach
        optimisation results to cv_data["meta"]["ats_optimization"].

        Parameters
        ----------
        cv_data        : validated & normalised CV dictionary
        job_title      : free-form job title string entered by the user
        job_description: optional raw job description text for deeper matching
        """
        # 1. Extract all CV text as a single corpus
        cv_text = self._extract_cv_text(cv_data)

        # 2. Tokenise into individual words and phrases
        cv_words = self._tokenize(cv_text)

        # 3. Determine target keywords (from JSON + optional JD)
        target_keywords = self._resolve_target_keywords(job_title, job_description)

        # 4. Score each target keyword against the CV text
        matched, missing = self._match_keywords(cv_words, cv_text, target_keywords)

        # 5. Compute keyword coverage percentage
        coverage = (len(matched) / len(target_keywords) * 100) if target_keywords else 0.0

        # 6. TF-IDF-style importance ranking for matched keywords
        tf_scores = self._compute_tf(cv_words, matched)

        # 7. Attach results to meta
        cv_data.setdefault("meta", {})
        cv_data["meta"]["target_job_title"] = job_title
        cv_data["meta"]["ats_optimization"] = {
            "matched_keywords": sorted(matched),
            "missing_keywords": sorted(missing),
            "keyword_coverage_pct": round(coverage, 1),
            "tf_scores": tf_scores,
            "total_target_keywords": len(target_keywords),
        }

        print(f"\n  Keyword coverage: {coverage:.1f}% "
              f"({len(matched)}/{len(target_keywords)} keywords matched)")
        if missing:
            top_missing = sorted(missing)[:10]
            print(f"  Top missing keywords: {', '.join(top_missing)}")

        return cv_data

    # ------------------------------------------------------------------ #
    #  Text extraction                                                     #
    # ------------------------------------------------------------------ #

    def _extract_cv_text(self, cv_data: Dict[str, Any]) -> str:
        """Concatenate all meaningful text from the CV into one string."""
        parts: List[str] = []

        # Personal summary
        personal = cv_data.get("personal", {})
        parts.append(personal.get("summary", ""))

        # Experience bullets and job titles
        for exp in cv_data.get("experience", []):
            parts.append(exp.get("title", ""))
            parts.extend(exp.get("bullets", []))

        # Skills (all categories)
        skills = cv_data.get("skills", {})
        for skill_list in skills.values():
            parts.extend(skill_list)

        # Project descriptions and technologies
        for proj in cv_data.get("projects", []):
            parts.append(proj.get("description", ""))
            parts.extend(proj.get("technologies", []))
            parts.append(proj.get("name", ""))

        # Education fields
        for edu in cv_data.get("education", []):
            parts.append(edu.get("field", ""))
            parts.append(edu.get("degree", ""))
            parts.extend(edu.get("achievements", []))

        # Certifications
        for cert in cv_data.get("certifications", []):
            parts.append(cert.get("name", ""))

        return " ".join(filter(None, parts))

    # ------------------------------------------------------------------ #
    #  Keyword resolution                                                  #
    # ------------------------------------------------------------------ #

    def _resolve_target_keywords(
        self,
        job_title: str,
        job_description: Optional[str],
    ) -> List[str]:
        """
        Build the list of target keywords for the specified job title.

        Strategy:
          1. Fuzzy-match the user's job title against our JSON keys.
          2. Extract high-frequency terms from the job description (if given).
          3. Merge and deduplicate.
        """
        # Step 1: find the best matching job title key
        best_key = self._fuzzy_match_job_title(job_title)
        json_keywords: List[str] = []
        if best_key:
            json_keywords = self._job_titles[best_key].get("keywords", [])

        # Step 2: extract keywords from job description
        jd_keywords: List[str] = []
        if job_description:
            jd_keywords = self._extract_jd_keywords(job_description, top_n=30)

        # Merge, deduplicate, case-insensitive
        seen = set()
        merged: List[str] = []
        for kw in json_keywords + jd_keywords:
            if kw.lower() not in seen:
                seen.add(kw.lower())
                merged.append(kw)

        return merged

    def _fuzzy_match_job_title(self, job_title: str) -> Optional[str]:
        """
        Return the JSON key whose label best overlaps with the user's job title.
        Uses simple token-overlap (Jaccard similarity).
        """
        query_tokens = set(re.sub(r"[^a-z0-9 ]", "", job_title.lower()).split())
        best_key: Optional[str] = None
        best_score: float = 0.0

        for key in self._job_titles:
            key_tokens = set(key.replace("_", " ").split())
            intersection = query_tokens & key_tokens
            union = query_tokens | key_tokens
            score = len(intersection) / len(union) if union else 0.0
            if score > best_score:
                best_score = score
                best_key = key

        return best_key if best_score > 0.0 else None

    # ------------------------------------------------------------------ #
    #  TF-IDF helpers                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        Lower-case, split on non-alphanumeric chars, return a list of tokens.
        Multi-word skill phrases are NOT split here; phrase matching is done
        separately via substring search.
        """
        return re.findall(r"[a-zA-Z0-9\+\#\.]+", text.lower())

    def _match_keywords(
        self,
        cv_words: List[str],
        cv_text: str,
        target_keywords: List[str],
    ) -> Tuple[List[str], List[str]]:
        """
        Determine which target keywords are present in the CV.

        Single-word keywords are matched against the tokenised word list.
        Multi-word keywords (e.g. "REST API") are matched via case-insensitive
        substring search against the full CV text.
        """
        cv_text_lower = cv_text.lower()
        cv_word_set = set(cv_words)

        matched: List[str] = []
        missing: List[str] = []

        for kw in target_keywords:
            kw_lower = kw.lower()
            tokens = kw_lower.split()
            if len(tokens) == 1:
                # Single-word: check token set
                found = kw_lower in cv_word_set
            else:
                # Multi-word phrase: check substring
                found = kw_lower in cv_text_lower

            (matched if found else missing).append(kw)

        return matched, missing

    @staticmethod
    def _compute_tf(
        cv_words: List[str],
        matched_keywords: List[str],
    ) -> Dict[str, float]:
        """
        Compute normalised term-frequency for each matched keyword.
        TF(t) = count(t in doc) / total_words
        """
        total = len(cv_words) or 1
        counter = Counter(cv_words)
        tf_scores: Dict[str, float] = {}
        for kw in matched_keywords:
            kw_token = kw.lower().split()[0]   # use first token for single-word check
            tf_scores[kw] = round(counter.get(kw_token, 0) / total, 6)
        return tf_scores

    # ------------------------------------------------------------------ #
    #  Job description keyword extraction                                  #
    # ------------------------------------------------------------------ #

    def _extract_jd_keywords(
        self, job_description: str, top_n: int = 30
    ) -> List[str]:
        """
        Extract the most important terms from a job description using TF
        (within a single document, IDF is constant so TF alone ranks terms).
        Stop-words are filtered out.
        """
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "as", "is", "are", "was", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did",
            "will", "would", "could", "should", "may", "might", "shall",
            "we", "you", "they", "he", "she", "it", "this", "that",
            "our", "your", "their", "its", "about", "from", "by", "not",
            "all", "also", "can", "who", "which", "what", "how", "when",
            "than", "more", "some", "other", "such", "any", "each",
            "required", "preferred", "experience", "ability", "skills",
            "work", "team", "candidate", "job", "role", "position",
        }
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9\+\#\.]{1,}", job_description.lower())
        filtered = [w for w in words if w not in stop_words and len(w) > 2]
        counter = Counter(filtered)
        top_words = [word for word, _ in counter.most_common(top_n)]
        # Title-case them so they look like proper skill names
        return [w.title() for w in top_words]
