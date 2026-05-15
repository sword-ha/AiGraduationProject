# Build context: api_services/unified_api/ (self-contained)

FROM python:3.11-slim

WORKDIR /app

# System deps for EasyOCR / OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1-mesa-glx libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cache)
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire unified API (includes ocr_project/ and cv_pipeline/)
COPY . .

# Environment
ENV OCR_PROJECT_DIR=/app/ocr_project
ENV CV_GENERATOR_DIR=/app/cv_pipeline
ENV CV_OUTPUT_DIR=/app/output
ENV CORS_ORIGINS=*

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
