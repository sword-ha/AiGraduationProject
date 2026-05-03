FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY ../../../cv_generator /cv_generator
ENV CV_GENERATOR_DIR=/cv_generator
ENV CV_OUTPUT_DIR=/app/output
RUN mkdir -p /app/output
EXPOSE 8003
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
