import logging
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from schemas.cv_schema import CVGenerateRequest, CVGenerateResponse
from services.cv_service import CVGeneratorService, OUTPUT_DIR

router = APIRouter(tags=["CV Generator"])
logger = logging.getLogger(__name__)
_service = CVGeneratorService()


@router.post(
    "/generate-cv",
    response_model=CVGenerateResponse,
    summary="Generate an ATS-friendly CV",
)
async def generate_cv(request: CVGenerateRequest):
    """
    Accepts structured CV data and returns:
    - ATS-optimized CV text
    - ATS score (0-100) and grade
    - Breakdown by scoring dimension
    - Missing keywords and improvement suggestions
    - PDF download URL

    **Example cURL:**
    ```bash
    curl -X POST http://localhost:8003/api/v1/generate-cv \\
         -H "Content-Type: application/json" \\
         -d @cv_data.json
    ```
    """
    logger.info(f"CV generation request for: {request.personal.name}")
    return await _service.generate(request)


@router.get(
    "/download-cv/{filename}",
    summary="Download the generated PDF CV",
    response_class=FileResponse,
)
async def download_cv(filename: str):
    """Download a previously generated PDF CV by filename."""
    # Sanitize filename to prevent path traversal
    safe_name = os.path.basename(filename)
    file_path = os.path.join(OUTPUT_DIR, safe_name)

    if not os.path.exists(file_path) or not safe_name.endswith(".pdf"):
        raise HTTPException(status_code=404, detail="CV file not found.")

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=safe_name,
    )
