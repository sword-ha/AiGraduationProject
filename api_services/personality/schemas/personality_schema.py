from pydantic import BaseModel, Field
from typing import List, Optional


class PersonalityAnswersRequest(BaseModel):
    """
    40 yes/no answers corresponding to the personality questionnaire.
    Each answer must be True (Yes) or False (No).
    """

    answers: List[bool] = Field(
        ...,
        min_length=40,
        max_length=40,
        description="List of 40 boolean answers (True=Yes, False=No)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "answers": [
                    True, False, True, True, True,
                    False, True, True, False, False,
                    True, False, True, False, True,
                    True, True, False, True, False,
                    True, True, True, True, True,
                    False, True, False, True, False,
                    True, True, True, False, True,
                    True, True, False, True, False,
                ]
            }
        }
    }


class MarketingCategory(BaseModel):
    category: str
    description: str


class PersonalityAnalysisResponse(BaseModel):
    mbti_type: str
    dimensions: dict
    personality_summary: str
    marketing_categories: List[str]
    marketing_explanation: str
    big_five_mapping: dict
