def decide_price_range(score: int) -> str:
    if score < 10:
        return "LOW_TICKET"       # أقل من 500 جنيه
    elif score < 20:
        return "MID_TICKET"       # من 500 لـ 10000
    else:
        return "HIGH_TICKET"      # فوق 10000 جنيه
