from core.scoring_engine import calculate_score
from core.decision_engine import decide_price_range
from core.campaign_mapper import get_campaigns
from services.feature_extractor import (
    get_experience_score,
    extract_job_scores,
    extract_skill_scores
)

def analyze_profile(cv_text: str) -> dict:
    # تجربة استخراج سنوات الخبرة بشكل مبسط (مثال 2 سنوات إذا ذكر "2 years")
    import re
    match = re.search(r"(\d+)\s*year", cv_text.lower())
    years = int(match.group(1)) if match else 0

    extracted_data = {
        "experience_score": get_experience_score(years),
        "job_scores": extract_job_scores(cv_text),
        "skill_scores": extract_skill_scores(cv_text)
    }

    final_score = calculate_score(extracted_data)
    price_range = decide_price_range(final_score)
    campaigns = get_campaigns(price_range)

    return {
        "score": final_score,
        "price_range": price_range,
        "allowed_campaigns": campaigns
    }
