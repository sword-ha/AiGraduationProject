from models import MarketerProfile, Campaign

def build_prompt(marketer: MarketerProfile, campaign: Campaign, user_message: str, chat_history: list) -> str:
    """
    يبني البرومبت للموديل حسب الحملة وكلام المستخدم.
    كمان ياخد chat_history عشان يحافظ على السياق.
    """
    history_text = ""
    for h in chat_history[-6:]:  # نستخدم آخر 6 رسائل بس
        history_text += f"{h['role']}: {h['content']}\n"

    return f"""
You are an expert marketing copywriter chatbot.

Marketer:
- Experience level: {marketer.experience_level}
- Tone: {marketer.tone}
- Platform: {marketer.platform}

Campaign:
- Product: {campaign.product_name}
- Goal: {campaign.goal}
- Audience: {campaign.audience}
- Pain point: {campaign.pain_point}
- Main benefit: {campaign.main_benefit}
- Offer: {campaign.offer}

Conversation context:
{history_text}

Rules:
- Reply in Egyptian Arabic
- Keep it short, persuasive and natural
- Adapt to any new discount or product mentioned
- End with a clear call to action
"""
