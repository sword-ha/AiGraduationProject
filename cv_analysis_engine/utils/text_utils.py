import re

def clean_text(text: str) -> str:
    """
    تنظيف النص: إزالة أسطر فارغة، مسافات زايدة، وتحويل كل شيء لصغير.
    """
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()

def extract_years_of_experience(text: str) -> int:
    """
    استخراج عدد السنوات من النص.
    يبحث عن "2 years" أو "3 yrs" أو "5+ years" ويعيد الرقم.
    """
    matches = re.findall(r"(\d+)\s*(?:years|yrs)", text.lower())
    if matches:
        return int(matches[0])
    return 0
