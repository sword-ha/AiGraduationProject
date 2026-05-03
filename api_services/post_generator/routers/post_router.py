import logging

from fastapi import APIRouter, HTTPException

from schemas.post_schema import PostGenerateRequest, PostGenerateResponse
from services.post_service import PostGeneratorService

router = APIRouter(tags=["Post Generator"])
logger = logging.getLogger(__name__)
_service = PostGeneratorService()


@router.post(
    "/generate-post",
    response_model=PostGenerateResponse,
    summary="Generate a platform-specific marketing post",
)
async def generate_post(request: PostGenerateRequest):
    """
    Generates a marketing post tailored to the specified platform and audience.

    Returns:
    - **post**: The generated post body
    - **hashtags**: List of recommended hashtags
    - **character_count**: Length of the post (useful for Twitter limit checks)

    **Example cURL:**
    ```bash
    curl -X POST http://localhost:8005/api/v1/generate-post \\
         -H "Content-Type: application/json" \\
         -d '{
               "product_type": "كورس Python",
               "target_audience": "شباب 20-30",
               "platform": "Instagram",
               "offer": "خصم 30%"
             }'
    ```
    """
    try:
        logger.info(f"Post generation request — platform={request.platform}, product={request.product_type}")
        return await _service.generate(request)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error(f"Post generation error: {exc}", exc_info=True)
        raise HTTPException(status_code=502, detail="LLM service unavailable.")
