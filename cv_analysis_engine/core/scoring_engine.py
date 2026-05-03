def calculate_score(extracted_data: dict) -> int:
    score = 0
    score += extracted_data.get("experience_score", 0)
    score += sum(extracted_data.get("job_scores", []))
    score += sum(extracted_data.get("skill_scores", []))
    return score
