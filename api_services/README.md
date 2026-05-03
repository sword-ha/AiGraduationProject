# AI Services — FastAPI Microservices

Five production-ready REST APIs converted from the original GUI-based models.

## Services Overview

| Service | Port | Endpoint | Description |
|---|---|---|---|
| ID Verification | 8001 | `POST /api/v1/verify-id` | Extract data from Egyptian ID cards |
| Personality Analysis | 8002 | `POST /api/v1/analyze-personality` | MBTI + marketing recommendations |
| CV Generator | 8003 | `POST /api/v1/generate-cv` | ATS-optimized CV as text + PDF |
| Chatbot | 8004 | `POST /api/v1/chat` | Marketing assistant chatbot |
| Post Generator | 8005 | `POST /api/v1/generate-post` | Platform-specific marketing posts |

---

## Folder Structure

```
api_services/
├── docker-compose.yml
├── id_verification/
│   ├── main.py
│   ├── routers/id_router.py
│   ├── services/id_service.py
│   ├── schemas/id_schema.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── personality/
│   ├── main.py
│   ├── routers/personality_router.py
│   ├── services/personality_service.py
│   ├── schemas/personality_schema.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── cv_generator/
│   ├── main.py
│   ├── routers/cv_router.py
│   ├── services/cv_service.py
│   ├── schemas/cv_schema.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── chatbot/
│   ├── main.py
│   ├── routers/chat_router.py
│   ├── services/chat_service.py
│   ├── schemas/chat_schema.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
└── post_generator/
    ├── main.py
    ├── routers/post_router.py
    ├── services/post_service.py
    ├── schemas/post_schema.py
    ├── requirements.txt
    ├── Dockerfile
    └── .env.example
```

---

## Quick Start — Run All Services Locally

### Step 1 — Set up environment files

Copy `.env.example` to `.env` in services that need API keys:

```bash
cd chatbot   && cp .env.example .env    # edit OPENROUTER_API_KEY
cd post_generator && cp .env.example .env  # edit OPENROUTER_API_KEY
```

### Step 2 — Install and run each service

**Option A: Run individually (recommended for development)**

```bash
# ID Verification (port 8001)
cd id_verification
pip install -r requirements.txt
uvicorn main:app --reload --port 8001

# Personality Analysis (port 8002)
cd personality
pip install -r requirements.txt
uvicorn main:app --reload --port 8002

# CV Generator (port 8003)
cd cv_generator
pip install -r requirements.txt
uvicorn main:app --reload --port 8003

# Chatbot (port 8004)
cd chatbot
pip install -r requirements.txt
uvicorn main:app --reload --port 8004

# Post Generator (port 8005)
cd post_generator
pip install -r requirements.txt
uvicorn main:app --reload --port 8005
```

**Option B: Docker Compose (all at once)**

```bash
cd api_services
# Create .env files first for chatbot and post_generator
docker-compose up --build
```

---

## Swagger UI (Auto-generated Docs)

| Service | URL |
|---|---|
| ID Verification | http://localhost:8001/docs |
| Personality | http://localhost:8002/docs |
| CV Generator | http://localhost:8003/docs |
| Chatbot | http://localhost:8004/docs |
| Post Generator | http://localhost:8005/docs |

---

## API Reference & Example Calls

### 1. ID Verification — `POST /api/v1/verify-id`

```bash
curl -X POST http://localhost:8001/api/v1/verify-id \
     -F "file=@path/to/id_card.jpg"
```

**Response:**
```json
{
  "verified": true,
  "data": {
    "first_name": "محمد",
    "last_name": "أحمد",
    "full_name": "محمد أحمد",
    "national_id": "29901012401234",
    "address": "القاهرة",
    "birth_date": "1999-01-01",
    "governorate": "Cairo",
    "gender": "Male"
  }
}
```

---

### 2. Personality Analysis — `POST /api/v1/analyze-personality`

Get questions first:
```bash
curl http://localhost:8002/api/v1/questions
```

Submit answers:
```bash
curl -X POST http://localhost:8002/api/v1/analyze-personality \
     -H "Content-Type: application/json" \
     -d '{"answers": [true,false,true,true,true,false,true,true,false,false,true,false,true,false,true,true,true,false,true,false,true,true,true,true,true,false,true,false,true,false,true,true,true,false,true,true,true,false,true,false]}'
```

**Response:**
```json
{
  "mbti_type": "ENTJ",
  "dimensions": {
    "Introversion_Extraversion": "12I / 18E",
    "Intuition_Sensing": "14N / 6S",
    "Thinking_Feeling": "16T / 4F",
    "Judging_Perceiving": "14J / 6P"
  },
  "personality_summary": "Bold, decisive leader who drives results.",
  "marketing_categories": ["Business Tools", "Productivity Software", "Leadership Courses"],
  "marketing_explanation": "Based on your MBTI type (ENTJ)...",
  "big_five_mapping": {
    "Openness": "High",
    "Conscientiousness": "High",
    "Extraversion": "High",
    "Agreeableness": "Low",
    "Neuroticism": "Low"
  }
}
```

---

### 3. CV Generator — `POST /api/v1/generate-cv`

```bash
curl -X POST http://localhost:8003/api/v1/generate-cv \
     -H "Content-Type: application/json" \
     -d '{
       "personal": {
         "name": "Ahmed Ali",
         "email": "ahmed@example.com",
         "phone": "+20 100 000 0000",
         "location": "Cairo, Egypt",
         "summary": "Software engineer with 3 years of Python experience."
       },
       "experience": [{
         "company": "Tech Corp",
         "title": "Backend Developer",
         "start_date": "Jul 2022",
         "end_date": "Present",
         "bullets": ["Built REST APIs serving 100K+ users", "Reduced latency by 40%"]
       }],
       "skills": {
         "technical": ["Python", "FastAPI", "PostgreSQL"],
         "tools": ["Docker", "Git"]
       },
       "target_job_title": "Backend Developer"
     }'
```

Download PDF:
```bash
curl http://localhost:8003/api/v1/download-cv/ahmed_ali_cv_20260503_120000.pdf -o cv.pdf
```

---

### 4. Chatbot — `POST /api/v1/chat`

```bash
curl -X POST http://localhost:8004/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{
       "message": "اكتبلي بوست لكورس Python بخصم 30%",
       "platform": "Facebook",
       "tone": "Casual",
       "campaign": {
         "product_name": "كورس Python",
         "goal": "Sales",
         "audience": "شباب 20-30",
         "offer": "خصم 30%"
       }
     }'
```

Multi-turn conversation:
```bash
curl -X POST http://localhost:8004/api/v1/chat \
     -H "Content-Type: application/json" \
     -d '{
       "message": "عدل الأوفر لخصم 50%",
       "session_id": "abc-123",
       "platform": "Facebook",
       "history": [
         {"role": "user", "content": "اكتبلي بوست لكورس Python"},
         {"role": "assistant", "content": "🚀 هتتعلم Python ..."}
       ]
     }'
```

---

### 5. Post Generator — `POST /api/v1/generate-post`

```bash
curl -X POST http://localhost:8005/api/v1/generate-post \
     -H "Content-Type: application/json" \
     -d '{
       "product_type": "كورس برمجة Python",
       "target_audience": "شباب من 18 إلى 30 سنة",
       "platform": "Instagram",
       "tone": "Casual",
       "offer": "خصم 40% لأول 50 متسجل",
       "include_emojis": true,
       "hashtag_count": 7
     }'
```

**Response:**
```json
{
  "post": "🚀 وقفت كتير وانت بتدور على شغل في IT؟...",
  "hashtags": ["#Python", "#برمجة", "#تعلم_البرمجة", "#وظائف_تقنية", "#كورسات_اون_لاين", "#خصم", "#IT"],
  "platform": "Instagram",
  "tone": "Casual",
  "character_count": 312
}
```

---

## Integration with ASP.NET Core

In your .NET backend, call these services via `HttpClient`:

```csharp
// Program.cs
builder.Services.AddHttpClient("PersonalityApi", c => {
    c.BaseAddress = new Uri("http://localhost:8002");
});
builder.Services.AddHttpClient("ChatbotApi", c => {
    c.BaseAddress = new Uri("http://localhost:8004");
});

// In a controller
public async Task<IActionResult> AnalyzePersonality([FromBody] PersonalityRequest req)
{
    var client = _httpClientFactory.CreateClient("PersonalityApi");
    var response = await client.PostAsJsonAsync("/api/v1/analyze-personality", req);
    var result = await response.Content.ReadFromJsonAsync<PersonalityResponse>();
    return Ok(result);
}
```

---

## Environment Variables Reference

| Variable | Service | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | chatbot, post_generator | Your OpenRouter API key |
| `LLM_MODEL` | chatbot, post_generator | Model name (default: `openai/gpt-4o-mini`) |
| `OCR_PROJECT_DIR` | id_verification | Path to OCR_Egyptian_ID-main folder |
| `CV_GENERATOR_DIR` | cv_generator | Path to cv_generator folder |
| `CV_OUTPUT_DIR` | cv_generator | Where to save generated PDFs |
| `CORS_ORIGINS` | all | Allowed CORS origins (default: `*`) |

---

## Notes

- All services are **stateless** — horizontal scaling is supported
- Swagger UI is enabled on every service at `/docs`
- PDF files are stored temporarily in `cv_generator/output/`
- The ID verification service requires the YOLO model files (`.pt`) from `OCR_Egyptian_ID-main/`
- Services 4 and 5 require a valid `OPENROUTER_API_KEY`
