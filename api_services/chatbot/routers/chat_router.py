import logging

from fastapi import APIRouter, HTTPException

from schemas.chat_schema import ChatRequest, ChatResponse
from services.chat_service import ChatService

router = APIRouter(tags=["Chatbot"])
logger = logging.getLogger(__name__)
_service = ChatService()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the marketing chatbot",
)
async def chat(request: ChatRequest):
    """
    Send a message to the AI marketing assistant.

    Supports multi-turn conversation via `history`.
    Optionally provide a `campaign` context to get targeted responses.

    **Example cURL:**
    ```bash
    curl -X POST http://localhost:8004/api/v1/chat \\
         -H "Content-Type: application/json" \\
         -d '{"message": "اكتبلي بوست لكورس برمجة", "platform": "Facebook"}'
    ```
    """
    try:
        logger.info(f"Chat request received — platform={request.platform}")
        return await _service.chat(request)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error(f"Chat error: {exc}", exc_info=True)
        raise HTTPException(status_code=502, detail="LLM service unavailable.")
