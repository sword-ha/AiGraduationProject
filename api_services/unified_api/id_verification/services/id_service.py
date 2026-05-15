import logging
import os
import sys
import tempfile

from id_verification.schemas.id_schema import ExtractedIDData, IDVerificationResponse

logger = logging.getLogger(__name__)

_OCR_DIR = os.getenv(
    "OCR_PROJECT_DIR",
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "OCR_Egyptian_ID-main"),
)
sys.path.insert(0, os.path.abspath(_OCR_DIR))


class IDVerificationService:
    def __init__(self):
        from utils import detect_and_process_id_card  # noqa: PLC0415

        self._detect = detect_and_process_id_card

    async def verify(self, image_bytes: bytes) -> IDVerificationResponse:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        prev_cwd = os.getcwd()
        try:
            logger.info("Running ID card detection pipeline")
            os.chdir(os.path.abspath(_OCR_DIR))
            result = self._detect(tmp_path)

            if result["verified"]:
                raw = result["data"]
                extracted = ExtractedIDData(
                    first_name=raw[0],
                    last_name=raw[1],
                    full_name=raw[2],
                    national_id=raw[3],
                    address=raw[4],
                    birth_date=raw[5],
                    governorate=raw[6],
                    gender=raw[7],
                )
                logger.info(f"ID verified: national_id={raw[3]}")
                return IDVerificationResponse(verified=True, data=extracted)
            else:
                logger.warning(f"ID not verified: {result['message']}")
                return IDVerificationResponse(verified=False, message=result["message"])

        except Exception as exc:
            logger.error(f"ID verification failed: {exc}", exc_info=True)
            return IDVerificationResponse(
                verified=False, message="Internal error during verification."
            )
        finally:
            os.chdir(prev_cwd)
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
