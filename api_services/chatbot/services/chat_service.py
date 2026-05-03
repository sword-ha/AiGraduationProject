"""
chat_service.py
---------------
Stateless chatbot service — history is passed in each request.
Uses OpenRouter API (GPT-4o-mini by default, configurable via env).
"""

import logging
import os
import uuid
from typing import List

import httpx

from schemas.chat_schema import (
    CampaignContext,
    ChatMessage,
    ChatRequest,
    ChatResponse,
)

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")
API_KEY = os.getenv("OPENROUTER_API_KEY", "")


def _build_system_prompt(
    experience_level: str,
    tone: str,
    platform: str,
    campaign: CampaignContext | None,
) -> str:
    campaign_block = ""
    if campaign:
        campaign_block = f"""
Campaign details:
- Product: {campaign.product_name or 'N/A'}
- Goal: {campaign.goal or 'N/A'}
- Audience: {campaign.audience or 'N/A'}
- Pain point: {campaign.pain_point or 'N/A'}
- Main benefit: {campaign.main_benefit or 'N/A'}
- Offer: {campaign.offer or 'N/A'}
"""

    return f"""You are an expert marketing copywriter assistant for Egyptian marketers.

Marketer profile:
- Experience level: {experience_level}
- Preferred tone: {tone}
- Primary platform: {platform}
{campaign_block}
Rules:
- Always reply in Egyptian Arabic unless the user writes in English
- Keep responses short, persuasive, and natural
- Adapt dynamically to any new product or offer mentioned
- End posts and copy with a clear call to action
- For off-topic questions, politely redirect to marketing topics
"""


class ChatService:
    async def chat(self, req: ChatRequest) -> ChatResponse:
        if not API_KEY:
            raise ValueError("OPENROUTER_API_KEY environment variable is not set.")

        system_prompt = _build_system_prompt(
            req.experience_level.value,
            req.tone.value,
            req.platform.value,
            req.campaign,
        )

        messages = [{"role": "system", "content": system_prompt}]

        # Append conversation history (last 6 turns max)
        for msg in (req.history or [])[-6:]:
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": req.message})

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("APP_URL", "http://localhost"),
            "X-Title": "Marketing AI Chatbot",
        }

        payload = {
            "model": LLM_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 800,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(OPENROUTER_URL, json=payload, headers=headers)
            response.raise_for_status()

        data = response.json()
        reply = data["choices"][0]["message"]["content"]

        logger.info(f"Chat response generated — model={LLM_MODEL}")
        return ChatResponse(
            reply=reply,
            session_id=req.session_id or str(uuid.uuid4()),
        )
