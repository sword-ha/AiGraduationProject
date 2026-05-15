# AI Graduation Project — API Reference

> **Base URLs (local dev)**
>
> | Service | Base URL | Swagger Docs |
> |---|---|---|
> | ID Verification | `http://localhost:8001` | [/docs](http://localhost:8001/docs) |
> | Personality Analysis | `http://localhost:8002` | [/docs](http://localhost:8002/docs) |
> | CV Generator | `http://localhost:8003` | [/docs](http://localhost:8003/docs) |
> | Chatbot | `http://localhost:8004` | [/docs](http://localhost:8004/docs) |
> | Post Generator | `http://localhost:8005` | [/docs](http://localhost:8005/docs) |

All endpoints return **JSON**. All services support CORS (all origins).

---

## 1. ID Verification — Port 8001

### `GET /health`
Returns service status.

**Response**
```json
{ "status": "ok", "service": "id-verification" }
```

---

### `POST /api/v1/verify-id`
Upload an Egyptian National ID card image and extract personal data.

**Request** — `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | `file` | ✅ | JPEG or PNG image of the ID card |

**Response**
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
  },
  "message": null
}
```

If verification fails:
```json
{ "verified": false, "data": null, "message": "Could not extract ID data" }
```

**Error codes**
| Code | Reason |
|---|---|
| `400` | Empty file |
| `415` | File is not JPEG/PNG |

---

## 2. Personality Analysis — Port 8002

### `GET /health`
Returns service status.

---

### `GET /api/v1/questions`
Fetch the 40 personality questionnaire questions to render dynamically on the frontend.

**Response**
```json
{
  "total": 40,
  "questions": [
    { "index": 0, "text": "Do you enjoy meeting new people?", "axis": "E/I" },
    ...
  ]
}
```

---

### `POST /api/v1/analyze-personality`
Submit 40 yes/no answers and receive an MBTI personality profile with marketing recommendations.

**Request** — `application/json`

| Field | Type | Required | Description |
|---|---|---|---|
| `answers` | `bool[]` | ✅ | Array of exactly 40 booleans (`true` = Yes, `false` = No) |

```json
{
  "answers": [true, false, true, true, false, ...]
}
```

**Response**
```json
{
  "mbti_type": "ENFJ",
  "dimensions": {
    "E/I": "Extrovert",
    "S/N": "Intuitive",
    "T/F": "Feeling",
    "J/P": "Judging"
  },
  "personality_summary": "You are a charismatic leader...",
  "marketing_categories": ["Social Media", "Community Building", "Storytelling"],
  "marketing_explanation": "ENFJs excel at...",
  "big_five_mapping": {
    "openness": "High",
    "conscientiousness": "High",
    "extraversion": "High",
    "agreeableness": "High",
    "neuroticism": "Low"
  }
}
```

---

## 3. CV Generator — Port 8003

### `GET /health`
Returns service status.

---

### `POST /api/v1/generate-cv`
Submit structured CV data and receive an ATS-optimized CV with a score, suggestions, and a PDF download link.

**Request** — `application/json`

```json
{
  "personal": {
    "name": "Ahmed Ali",
    "email": "ahmed@example.com",
    "phone": "+20 100 000 0000",
    "linkedin": "linkedin.com/in/ahmedali",   // optional
    "github": "github.com/ahmedali",           // optional
    "location": "Cairo, Egypt",                // optional
    "website": "ahmedali.dev",                 // optional
    "summary": "Software engineer..."          // optional
  },
  "education": [
    {
      "institution": "Cairo University",
      "degree": "Bachelor",                    // optional
      "field": "Computer Science",             // optional
      "start_date": "2018",                    // optional
      "end_date": "2022",                      // optional
      "gpa": "3.8",                            // optional
      "achievements": ["Dean's List"]          // optional
    }
  ],
  "experience": [
    {
      "company": "Google",
      "title": "Software Engineer",            // optional
      "start_date": "2022-06",                 // optional
      "end_date": "Present",                   // optional
      "location": "Cairo",                     // optional
      "bullets": ["Built X using Y..."]        // optional
    }
  ],
  "skills": {
    "technical": ["Python", "FastAPI"],        // optional
    "soft": ["Leadership"],                    // optional
    "tools": ["Docker", "Git"]                 // optional
  },
  "projects": [
    {
      "name": "My Project",
      "description": "A cool project",         // optional
      "tech_stack": ["React", "Node.js"],      // optional
      "url": "github.com/...",                 // optional
      "bullets": ["Achieved X..."]             // optional
    }
  ],
  "certifications": [
    {
      "name": "AWS Certified",
      "issuer": "Amazon",                      // optional
      "date": "2023",                          // optional
      "url": "credly.com/..."                  // optional
    }
  ],
  "target_job_title": "Backend Engineer"       // optional — improves ATS scoring
}
```

**Response**
```json
{
  "ats_score": 87,
  "ats_grade": "A",
  "cv_text": "Ahmed Ali\nahmed@example.com\n...",
  "score_breakdown": {
    "keywords": 90,
    "formatting": 85,
    "completeness": 88
  },
  "missing_keywords": ["Docker", "CI/CD"],
  "suggestions": ["Add more quantified achievements"],
  "pdf_url": "/api/v1/download-cv/ahmed_ali_cv_20260515_120000.pdf"
}
```

---

### `GET /api/v1/download-cv/{filename}`
Download the generated PDF CV.

**Path param:** `filename` — returned in the `pdf_url` field above.

**Response:** PDF file (`application/pdf`)

**Error codes**
| Code | Reason |
|---|---|
| `404` | File not found or invalid name |

---

## 4. Chatbot — Port 8004

### `GET /health`
Returns service status.

---

### `POST /api/v1/chat`
Send a message to the AI marketing assistant. Supports multi-turn conversations.

**Request** — `application/json`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `message` | `string` | ✅ | — | User message (1–2000 chars) |
| `session_id` | `string` | ❌ | `null` | Pass the same ID across turns to maintain context |
| `experience_level` | `"Junior"` \| `"Mid"` \| `"Senior"` | ❌ | `"Junior"` | User experience level |
| `tone` | `"Casual"` \| `"Professional"` \| `"Persuasive"` | ❌ | `"Casual"` | Response tone |
| `platform` | `"Facebook"` \| `"Instagram"` \| `"LinkedIn"` \| `"Web"` \| `"TikTok"` | ❌ | `"Facebook"` | Target platform |
| `campaign` | `object` | ❌ | `null` | Optional campaign context (see below) |
| `history` | `ChatMessage[]` | ❌ | `[]` | Previous messages for multi-turn context |

**`campaign` object (all optional)**
```json
{
  "product_name": "كورس Python",
  "goal": "Sales",
  "pain_point": "مفيش شغل",
  "main_benefit": "تتعلم مهارة مطلوبة",
  "offer": "خصم 30%",
  "audience": "شباب 20-30"
}
```

**`history` array**
```json
[
  { "role": "user", "content": "اكتبلي بوست" },
  { "role": "assistant", "content": "تمام، هكتبلك..." }
]
```

**Full example**
```json
{
  "message": "اكتبلي بوست تسويقي لكورس برمجة بخصم 30%",
  "experience_level": "Junior",
  "tone": "Casual",
  "platform": "Facebook",
  "campaign": {
    "product_name": "كورس برمجة بايثون",
    "goal": "Sales",
    "audience": "شباب 20-30 سنة",
    "offer": "خصم 30%"
  },
  "history": []
}
```

**Response**
```json
{
  "reply": "🔥 حلم بشغل في IT؟ ...",
  "session_id": "abc123"
}
```

> **Multi-turn tip:** Save `session_id` from the first response and include it + `history` in subsequent requests.

**Error codes**
| Code | Reason |
|---|---|
| `503` | LLM service not configured |
| `502` | LLM service unreachable |

---

## 5. Post Generator — Port 8005

### `GET /health`
Returns service status.

---

### `POST /api/v1/generate-post`
Generate a platform-specific marketing post with hashtags.

**Request** — `application/json`

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `product_type` | `string` | ✅ | — | Product or service name (2–200 chars) |
| `target_audience` | `string` | ✅ | — | Who the post targets (2–200 chars) |
| `platform` | `"Facebook"` \| `"Instagram"` \| `"LinkedIn"` \| `"Twitter"` \| `"TikTok"` \| `"WhatsApp"` | ✅ | — | Target social platform |
| `tone` | `"Casual"` \| `"Professional"` \| `"Persuasive"` \| `"Humorous"` \| `"Inspirational"` | ❌ | `"Casual"` | Post tone |
| `language` | `string` | ❌ | `"Arabic"` | `"Arabic"` or `"English"` |
| `pain_point` | `string` | ❌ | `null` | Customer pain point to address |
| `main_benefit` | `string` | ❌ | `null` | Main benefit of the product |
| `offer` | `string` | ❌ | `null` | Special offer or CTA |
| `include_emojis` | `boolean` | ❌ | `true` | Include emojis in post |
| `hashtag_count` | `integer` | ❌ | `5` | Number of hashtags (1–20) |

**Example**
```json
{
  "product_type": "كورس برمجة Python",
  "target_audience": "شباب من 18 إلى 30 سنة بيدور على شغل في IT",
  "platform": "Facebook",
  "tone": "Casual",
  "language": "Arabic",
  "pain_point": "مفيش شغل وكل باب بيتأخر",
  "main_benefit": "تتعلم مهارة مطلوبة جداً في سوق الشغل",
  "offer": "خصم 40% لأول 50 متسجل",
  "include_emojis": true,
  "hashtag_count": 7
}
```

**Response**
```json
{
  "post": "🔥 تعبت من البحث عن شغل؟ ...",
  "hashtags": ["#Python", "#برمجة", "#تكنولوجيا", "#شغل", "#IT", "#كورس", "#تعليم"],
  "platform": "Facebook",
  "tone": "Casual",
  "character_count": 312
}
```

**Error codes**
| Code | Reason |
|---|---|
| `503` | LLM service not configured |
| `502` | LLM service unreachable |

---

## Common Notes for Frontend

1. **Content-Type** — All JSON endpoints need `Content-Type: application/json` header. The ID verification endpoint uses `multipart/form-data`.
2. **CORS** — All services allow all origins, no special headers needed.
3. **Health checks** — Hit `GET /health` on each service before making calls to confirm it's up.
4. **Interactive docs** — Each service exposes a full Swagger UI at `/docs` where you can test endpoints directly in the browser.
