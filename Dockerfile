# Build context: repo root

FROM python:3.11-slim

WORKDIR /app

# System deps for EasyOCR / OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1-mesa-glx libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cache)
COPY api_services/unified_api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the unified API app
COPY api_services/unified_api/ ./

# Copy the OCR project (YOLO models + utils.py)
COPY OCR_Egyptian_ID-main/ /ocr_project/

# Copy the CV generator pipeline (src/ package)
COPY cv_generator/ /cv_pipeline/

# Environment
ENV OCR_PROJECT_DIR=/ocr_project
ENV CV_GENERATOR_DIR=/cv_pipeline
ENV CV_OUTPUT_DIR=/app/output
ENV CORS_ORIGINS=*

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
