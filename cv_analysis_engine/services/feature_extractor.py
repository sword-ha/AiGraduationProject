from core.features import FEATURES

def get_experience_score(years: int) -> int:
    if years < 1:
        return 0
    elif years < 2:
        return FEATURES["experience"]["1-2"]
    elif years < 3:
        return FEATURES["experience"]["2-3"]
    elif years < 5:
        return FEATURES["experience"]["3-5"]
    elif years < 7:
        return FEATURES["experience"]["5-7"]
    elif years < 10:
        return FEATURES["experience"]["7-10"]
    elif years < 15:
        return FEATURES["experience"]["10-15"]
    else:
        return FEATURES["experience"]["15+"]

def extract_job_scores(text: str):
    scores = []
    for title, score in FEATURES["job_titles"].items():
        if title.lower() in text.lower():
            scores.append(score)
    return scores

def extract_skill_scores(text: str):
    scores = []
    for skill, score in FEATURES["skills"].items():
        if skill.lower() in text.lower():
            scores.append(score)
    return scores
