import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from id_verification.schemas.id_schema import IDVerificationResponse
from id_verification.services.id_service import IDVerificationService

router = APIRouter(tags=["ID Verification"])
logger = logging.getLogger(__name__)
_service = IDVerificationService()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/jpg"}


@router.post(
    "/verify-id",
    response_model=IDVerificationResponse,
    summary="Verify an Egyptian National ID card",
    response_description="Extracted ID data and verification status",
)
async def verify_id(file: UploadFile = File(..., description="JPEG/PNG image of the ID card")):
    """
    Upload an image of an Egyptian National ID card.
    Returns the extracted personal data and a **verified** flag.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type '{file.content_type}'. Use JPEG or PNG.",
        )

    logger.info(f"Received verification request — filename={file.filename}")
    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    return await _service.verify(image_bytes)
