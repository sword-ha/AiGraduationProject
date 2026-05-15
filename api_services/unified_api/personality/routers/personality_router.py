import logging

from fastapi import APIRouter, HTTPException

from personality.schemas.personality_schema import (
    PersonalityAnalysisResponse,
    PersonalityAnswersRequest,
)
from personality.services.personality_service import PersonalityService, QUESTIONS

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
    Submit 40 yes/no answers to receive MBTI type, Big Five mapping,
    and recommended marketing categories.
    """
    logger.info("Personality analysis request received")
    return _service.analyze(request.answers)


@router.get(
    "/questions",
    summary="Get the list of 40 personality questions",
)
async def get_questions():
    """Returns all 40 questions so the frontend can render the questionnaire dynamically."""
    return {
        "total": len(QUESTIONS),
        "questions": [
            {"index": i, "text": q[0], "axis": q[1]}
            for i, q in enumerate(QUESTIONS)
        ],
    }
