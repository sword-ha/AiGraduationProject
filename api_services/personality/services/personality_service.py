"""
personality_service.py
----------------------
Pure logic — no GUI, no Tkinter, no CSV loading at startup.
The MBTI axes are determined by a fixed 40-question answer set.
"""

import logging
from typing import List

from schemas.personality_schema import PersonalityAnalysisResponse

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────
# Question bank  (axis, yes_letter, no_letter)
# Each tuple: (question_text, axis, letter_if_yes, letter_if_no)
# ──────────────────────────────────────────────────────────────────────────
QUESTIONS = [
    ("You enjoy social gatherings and meeting new people.", "IE", "E", "I"),
    ("You prefer concrete facts over abstract ideas.", "NS", "S", "N"),
    ("You make decisions based on logic rather than emotions.", "TF", "T", "F"),
    ("You like to plan things in advance rather than go with the flow.", "JP", "J", "P"),
    ("You feel energized after spending time with others.", "IE", "E", "I"),
    ("You enjoy imagining possibilities rather than focusing on reality.", "NS", "N", "S"),
    ("You value fairness over compassion.", "TF", "T", "F"),
    ("You like having a structured schedule.", "JP", "J", "P"),
    ("You prefer quiet time alone.", "IE", "I", "E"),
    ("You trust facts more than theories.", "NS", "S", "N"),
    ("You often rely on feelings when making decisions.", "TF", "F", "T"),
    ("You enjoy being spontaneous.", "JP", "P", "J"),
    ("You are outgoing and talkative.", "IE", "E", "I"),
    ("You focus on ideas rather than details.", "NS", "N", "S"),
    ("You prioritize logic in problem solving.", "TF", "T", "F"),
    ("You prefer organization over flexibility.", "JP", "J", "P"),
    ("You enjoy interacting with many people.", "IE", "E", "I"),
    ("You are imaginative and creative.", "NS", "N", "S"),
    ("You empathize with others easily.", "TF", "F", "T"),
    ("You dislike strict schedules.", "JP", "P", "J"),
    ("You like attending parties.", "IE", "E", "I"),
    ("You focus on the big picture.", "NS", "N", "S"),
    ("You make decisions rationally.", "TF", "T", "F"),
    ("You prefer routines.", "JP", "J", "P"),
    ("You enjoy group activities.", "IE", "E", "I"),
    ("You enjoy abstract thinking.", "NS", "N", "S"),
    ("You consider others' feelings in decisions.", "TF", "F", "T"),
    ("You like to adapt and go with the flow.", "JP", "P", "J"),
    ("You are talkative and energetic.", "IE", "E", "I"),
    ("You rely on intuition.", "NS", "N", "S"),
    ("You prioritize ethical concerns.", "TF", "F", "T"),
    ("You prefer a planned lifestyle.", "JP", "J", "P"),
    ("You enjoy being in social environments.", "IE", "E", "I"),
    ("You focus on possibilities.", "NS", "N", "S"),
    ("You are thoughtful and analytical.", "TF", "T", "F"),
    ("You like to keep things organized.", "JP", "J", "P"),
    ("You enjoy interacting with others.", "IE", "E", "I"),
    ("You use your imagination often.", "NS", "N", "S"),
    ("You consider emotions in decisions.", "TF", "F", "T"),
    ("You prefer flexibility over strict planning.", "JP", "P", "J"),
]

# ──────────────────────────────────────────────────────────────────────────
# MBTI → marketing categories
# ──────────────────────────────────────────────────────────────────────────
MBTI_MARKETING: dict = {
    "INTJ": ["Tech Gadgets", "Books", "Online Courses", "Software Tools"],
    "INTP": ["Tech Gadgets", "Research Tools", "Programming Courses"],
    "ENTJ": ["Business Tools", "Productivity Software", "Leadership Courses"],
    "ENTP": ["Startup Tools", "Adventure Travel", "Innovation Products"],
    "INFJ": ["Wellness Products", "Mindfulness Apps", "Self-Development"],
    "INFP": ["Books", "Creative Apps", "Artistic Products"],
    "ENFJ": ["Leadership Courses", "Social Apps", "Community Platforms"],
    "ENFP": ["Lifestyle Products", "Creative Tools", "Personal Branding"],
    "ISTJ": ["Office Supplies", "Professional Services", "Financial Tools"],
    "ISFJ": ["Home Essentials", "Family Products", "Health & Safety"],
    "ESTJ": ["Management Courses", "Business Tools", "Real Estate"],
    "ESFJ": ["Beauty", "Fashion", "Social Media Marketing"],
    "ISTP": ["Sports Equipment", "DIY Tools", "Electronics"],
    "ISFP": ["Art Supplies", "Music Instruments", "Aesthetic Lifestyle"],
    "ESTP": ["Outdoor Activities", "Adventure Gear", "Cars", "Sports"],
    "ESFP": ["Party Items", "Fashion Accessories", "Entertainment"],
}

MBTI_SUMMARIES: dict = {
    "INTJ": "Strategic, independent thinker with a long-term vision.",
    "INTP": "Analytical and inventive problem-solver who loves abstract ideas.",
    "ENTJ": "Bold, decisive leader who drives results.",
    "ENTP": "Quick-witted innovator who challenges the status quo.",
    "INFJ": "Insightful idealist with a deep concern for others.",
    "INFP": "Empathetic and creative with strong personal values.",
    "ENFJ": "Charismatic leader who inspires and motivates others.",
    "ENFP": "Enthusiastic, imaginative, and passionate about possibilities.",
    "ISTJ": "Responsible, detail-oriented, and dependable.",
    "ISFJ": "Caring, practical, and deeply committed to helping others.",
    "ESTJ": "Organized, efficient leader who values tradition and order.",
    "ESFJ": "Warm and sociable, prioritizing harmony and cooperation.",
    "ISTP": "Practical problem-solver who values efficiency and action.",
    "ISFP": "Gentle, artistic, and deeply in tune with the present moment.",
    "ESTP": "Energetic and action-oriented, thriving on challenge.",
    "ESFP": "Spontaneous, fun-loving, and enthusiastic.",
}

# MBTI → approximate Big Five (OCEAN) mapping
BIG_FIVE_MAP: dict = {
    "INTJ": {"Openness": "High", "Conscientiousness": "High", "Extraversion": "Low", "Agreeableness": "Low", "Neuroticism": "Low"},
    "INTP": {"Openness": "High", "Conscientiousness": "Medium", "Extraversion": "Low", "Agreeableness": "Low", "Neuroticism": "Low"},
    "ENTJ": {"Openness": "High", "Conscientiousness": "High", "Extraversion": "High", "Agreeableness": "Low", "Neuroticism": "Low"},
    "ENTP": {"Openness": "High", "Conscientiousness": "Low", "Extraversion": "High", "Agreeableness": "Low", "Neuroticism": "Low"},
    "INFJ": {"Openness": "High", "Conscientiousness": "High", "Extraversion": "Low", "Agreeableness": "High", "Neuroticism": "Medium"},
    "INFP": {"Openness": "High", "Conscientiousness": "Low", "Extraversion": "Low", "Agreeableness": "High", "Neuroticism": "High"},
    "ENFJ": {"Openness": "High", "Conscientiousness": "High", "Extraversion": "High", "Agreeableness": "High", "Neuroticism": "Medium"},
    "ENFP": {"Openness": "High", "Conscientiousness": "Low", "Extraversion": "High", "Agreeableness": "High", "Neuroticism": "Medium"},
    "ISTJ": {"Openness": "Low", "Conscientiousness": "High", "Extraversion": "Low", "Agreeableness": "Medium", "Neuroticism": "Low"},
    "ISFJ": {"Openness": "Low", "Conscientiousness": "High", "Extraversion": "Low", "Agreeableness": "High", "Neuroticism": "Medium"},
    "ESTJ": {"Openness": "Low", "Conscientiousness": "High", "Extraversion": "High", "Agreeableness": "Low", "Neuroticism": "Low"},
    "ESFJ": {"Openness": "Low", "Conscientiousness": "High", "Extraversion": "High", "Agreeableness": "High", "Neuroticism": "Medium"},
    "ISTP": {"Openness": "Medium", "Conscientiousness": "Medium", "Extraversion": "Low", "Agreeableness": "Low", "Neuroticism": "Low"},
    "ISFP": {"Openness": "High", "Conscientiousness": "Low", "Extraversion": "Low", "Agreeableness": "High", "Neuroticism": "Medium"},
    "ESTP": {"Openness": "Medium", "Conscientiousness": "Low", "Extraversion": "High", "Agreeableness": "Low", "Neuroticism": "Low"},
    "ESFP": {"Openness": "Medium", "Conscientiousness": "Low", "Extraversion": "High", "Agreeableness": "High", "Neuroticism": "Medium"},
}


class PersonalityService:
    def analyze(self, answers: List[bool]) -> PersonalityAnalysisResponse:
        counts = {"I": 0, "E": 0, "N": 0, "S": 0, "T": 0, "F": 0, "J": 0, "P": 0}

        for i, answer in enumerate(answers):
            _, _axis, yes_letter, no_letter = QUESTIONS[i]
            counts[yes_letter if answer else no_letter] += 1

        mbti = (
            ("I" if counts["I"] >= counts["E"] else "E")
            + ("N" if counts["N"] >= counts["S"] else "S")
            + ("T" if counts["T"] >= counts["F"] else "F")
            + ("J" if counts["J"] >= counts["P"] else "P")
        )

        categories = MBTI_MARKETING.get(mbti, ["General Marketing"])
        summary = MBTI_SUMMARIES.get(mbti, "Unique personality profile.")
        big_five = BIG_FIVE_MAP.get(mbti, {})

        explanation = (
            f"Based on your MBTI type ({mbti}), you are {summary.lower()} "
            f"Marketing campaigns focused on {', '.join(categories[:2])} "
            f"tend to resonate strongly with your profile."
        )

        logger.info(f"Personality analysis complete: mbti={mbti}")

        return PersonalityAnalysisResponse(
            mbti_type=mbti,
            dimensions={
                "Introversion_Extraversion": f"{counts['I']}I / {counts['E']}E",
                "Intuition_Sensing": f"{counts['N']}N / {counts['S']}S",
                "Thinking_Feeling": f"{counts['T']}T / {counts['F']}F",
                "Judging_Perceiving": f"{counts['J']}J / {counts['P']}P",
            },
            personality_summary=summary,
            marketing_categories=categories,
            marketing_explanation=explanation,
            big_five_mapping=big_five,
        )
