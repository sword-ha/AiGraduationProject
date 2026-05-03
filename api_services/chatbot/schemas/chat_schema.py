from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class ExperienceLevel(str, Enum):
    junior = "Junior"
    mid = "Mid"
    senior = "Senior"


class Tone(str, Enum):
    casual = "Casual"
    professional = "Professional"
    persuasive = "Persuasive"


class Platform(str, Enum):
    facebook = "Facebook"
    instagram = "Instagram"
    web = "Web"
    linkedin = "LinkedIn"
    tiktok = "TikTok"


class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str


class CampaignContext(BaseModel):
    product_name: Optional[str] = None
    goal: Optional[str] = None
    pain_point: Optional[str] = None
    main_benefit: Optional[str] = None
    offer: Optional[str] = None
    audience: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(
        None, description="Optional session ID to maintain conversation context"
    )
    experience_level: ExperienceLevel = ExperienceLevel.junior
    tone: Tone = Tone.casual
    platform: Platform = Platform.facebook
    campaign: Optional[CampaignContext] = None
    history: Optional[List[ChatMessage]] = Field(
        default=[], description="Last N chat messages for context"
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "اكتبلي بوست تسويقي لكورس برمجة بخصم 30%",
                "experience_level": "Junior",
                "tone": "Casual",
                "platform": "Facebook",
                "campaign": {
                    "product_name": "كورس برمجة بايثون",
                    "goal": "Sales",
                    "audience": "شباب 20-30 سنة",
                    "offer": "خصم 30%",
                },
                "history": [],
            }
        }
    }


class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None
