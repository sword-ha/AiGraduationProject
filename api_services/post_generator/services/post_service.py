"""
post_service.py
---------------
Generates platform-tailored marketing posts via OpenRouter LLM.
"""

import logging
import os
import re

import httpx

from schemas.post_schema import PostGenerateRequest, PostGenerateResponse

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Platform-specific tone and length guidance
PLATFORM_GUIDANCE: dict = {
    "Facebook": "Write a conversational post (150-300 words). Add paragraph breaks for readability.",
    "Instagram": "Write a short, visually-driven caption (50-150 words). Use emojis heavily. Great visual language.",
    "LinkedIn": "Write a professional post (200-400 words). Tell a story. No excessive emojis.",
    "Twitter": "Write a concise tweet under 280 characters. Punchy and direct.",
    "TikTok": "Write a short, energetic hook (50-100 words). Use Gen-Z friendly language.",
    "WhatsApp": "Write a direct, personal message (80-150 words). Feels like from a friend.",
}


def _build_prompt(req: PostGenerateRequest) -> str:
    platform_note = PLATFORM_GUIDANCE.get(req.platform.value, "")
    emoji_note = "Use relevant emojis." if req.include_emojis else "Do NOT use emojis."
    language_note = f"Write entirely in {req.language}."

    optional_parts = []
    if req.pain_point:
        optional_parts.append(f"- Customer pain point: {req.pain_point}")
    if req.main_benefit:
        optional_parts.append(f"- Main benefit: {req.main_benefit}")
    if req.offer:
        optional_parts.append(f"- Special offer / CTA: {req.offer}")

    optional_block = "\n".join(optional_parts) if optional_parts else ""

    return f"""You are an expert social media marketing copywriter.

Create a {req.tone.value.lower()} marketing post for {req.platform.value}.

Product/Service: {req.product_type}
Target audience: {req.target_audience}
{optional_block}

Platform instructions: {platform_note}
{emoji_note}
{language_note}

After the post, output EXACTLY {req.hashtag_count} relevant hashtags on a new line starting with "HASHTAGS:"
Format: HASHTAGS: #tag1 #tag2 #tag3

Write ONLY the post and the HASHTAGS line. Nothing else.
"""


def _parse_response(raw: str, req: PostGenerateRequest) -> PostGenerateResponse:
    """Split raw LLM output into post body and hashtags."""
    hashtag_match = re.search(r"HASHTAGS:\s*(.+)", raw, re.IGNORECASE)
    hashtags: list[str] = []

    if hashtag_match:
        hashtag_str = hashtag_match.group(1).strip()
        hashtags = [t.strip() for t in re.findall(r"#\w+", hashtag_str)]
        post_body = raw[: hashtag_match.start()].strip()
    else:
        # Fallback: extract inline hashtags and treat rest as body
        hashtags = re.findall(r"#\w+", raw)
        post_body = re.sub(r"#\w+", "", raw).strip()

    return PostGenerateResponse(
        post=post_body,
        hashtags=hashtags,
        platform=req.platform.value,
        tone=req.tone.value,
        character_count=len(post_body),
    )


class PostGeneratorService:
    async def generate(self, req: PostGenerateRequest) -> PostGenerateResponse:
        if not API_KEY:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set.")

        prompt = _build_prompt(req)

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("APP_URL", "http://localhost"),
            "X-Title": "Marketing Post Generator",
        }

        payload = {
            "model": LLM_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert marketing copywriter. Follow all instructions precisely.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.8,
            "max_tokens": 600,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
            response.raise_for_status()

        raw = response.json()["choices"][0]["message"]["content"]
        logger.info(f"Post generated for platform={req.platform.value}")
        return _parse_response(raw, req)
