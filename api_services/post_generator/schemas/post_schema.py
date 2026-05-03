from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class Platform(str, Enum):
    facebook = "Facebook"
    instagram = "Instagram"
    linkedin = "LinkedIn"
    twitter = "Twitter"
    tiktok = "TikTok"
    whatsapp = "WhatsApp"


class Tone(str, Enum):
    casual = "Casual"
    professional = "Professional"
    persuasive = "Persuasive"
    humorous = "Humorous"
    inspirational = "Inspirational"


class PostGenerateRequest(BaseModel):
    product_type: str = Field(..., min_length=2, max_length=200, description="Type or name of the product/service")
    target_audience: str = Field(..., min_length=2, max_length=200, description="Description of the target audience")
    platform: Platform
    tone: Tone = Tone.casual
    language: str = Field("Arabic", description="Language for the post (Arabic/English)")
    pain_point: Optional[str] = Field(None, description="Customer pain point to address")
    main_benefit: Optional[str] = Field(None, description="Main benefit of the product")
    offer: Optional[str] = Field(None, description="Special offer or CTA (e.g. 30% discount)")
    include_emojis: bool = True
    hashtag_count: int = Field(5, ge=1, le=20, description="Number of hashtags to generate")

    model_config = {
        "json_schema_extra": {
            "example": {
                "product_type": "كورس برمجة Python",
                "target_audience": "شباب من 18 إلى 30 سنة بيدور على شغل في IT",
                "platform": "Facebook",
                "tone": "Casual",
                "language": "Arabic",
                "pain_point": "مفيش شغل وكل باب بيتأخر",
                "main_benefit": "تتعلم مهارة مطلوبة جداً في سوق الشغل",
                "offer": "خصم 40% لأول 50 متسجل",
                "include_emojis": True,
                "hashtag_count": 7,
            }
        }
    }


class PostGenerateResponse(BaseModel):
    post: str
    hashtags: List[str]
    platform: str
    tone: str
    character_count: int
