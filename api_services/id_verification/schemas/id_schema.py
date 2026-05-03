from pydantic import BaseModel
from typing import Optional


class ExtractedIDData(BaseModel):
    first_name: str
    last_name: str
    full_name: str
    national_id: str
    address: str
    birth_date: str
    governorate: str
    gender: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "first_name": "محمد",
                "last_name": "أحمد",
                "full_name": "محمد أحمد",
                "national_id": "29901012401234",
                "address": "القاهرة",
                "birth_date": "1999-01-01",
                "governorate": "Cairo",
                "gender": "Male",
            }
        }
    }


class IDVerificationResponse(BaseModel):
    verified: bool
    data: Optional[ExtractedIDData] = None
    message: Optional[str] = None
