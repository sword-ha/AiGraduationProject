from fastapi import FastAPI, UploadFile, File
import shutil
import uuid
import os
from utils import detect_and_process_id_card

app = FastAPI(title="Egyptian ID AI Service")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/verify-id")
async def verify_id(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4()}.jpg"
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = detect_and_process_id_card(path)
        return result
    finally:
        os.remove(path)
