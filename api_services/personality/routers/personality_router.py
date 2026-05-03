import logging

from fastapi import APIRouter, HTTPException

from schemas.personality_schema import (
    PersonalityAnalysisResponse,
    PersonalityAnswersRequest,
)
from services.personality_service import PersonalityService, QUESTIONS

router = APIRouter(tags=["Personality Analysis"])
logger = logging.getLogger(__name__)
_service = PersonalityService()


@router.post(
    "/analyze-personality",
    response_model=PersonalityAnalysisResponse,
    summary="Analyze personality and get marketing recommendations",
)
async def analyze_personality(request: PersonalityAnswersRequest):
    """
    Submit 40 yes/no answers to receive:
    - MBTI personality type
    - Big Five trait mapping
    - Recommended marketing categories
    - Explanation

    **Example cURL:**
    ```bash
    curl -X POST http://localhost:8002/api/v1/analyze-personality \\
         -H "Content-Type: application/json" \\
         -d '{"answers": [true, false, true, ...]}'
    ```
    """
    logger.info("Personality analysis request received")
    return _service.analyze(request.answers)


@router.get(
    "/questions",
    summary="Get the list of 40 personality questions",
)
async def get_questions():
    """
    Returns all 40 questions with their index so the frontend can render
    the questionnaire dynamically.
    """
    return {
        "total": len(QUESTIONS),
        "questions": [
            {"index": i, "text": q[0], "axis": q[1]}
            for i, q in enumerate(QUESTIONS)
        ],
    }
