import urllib.request
import json

PASS = "[PASS]"
FAIL = "[FAIL]"
results = []


def test(name, url, data=None):
    try:
        if data:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode(),
                headers={"Content-Type": "application/json"},
            )
        else:
            req = urllib.request.Request(url)
        r = urllib.request.urlopen(req, timeout=15)
        body = json.loads(r.read().decode())
        results.append((PASS, name, body))
        return body
    except Exception as e:
        results.append((FAIL, name, str(e)))
        return None


# ─────────────── Personality (port 8002) ───────────────
test("Personality  /health", "http://localhost:8002/health")
test("Personality  /questions", "http://localhost:8002/api/v1/questions")

answers = [
    True, False, True, True, True, False, True, True, False, False,
    True, False, True, False, True, True, True, False, True, False,
    True, True, True, True, True, False, True, False, True, False,
    True, True, True, False, True, True, True, False, True, False,
]
test(
    "Personality  /analyze-personality",
    "http://localhost:8002/api/v1/analyze-personality",
    data={"answers": answers},
)

# ─────────────── CV Generator (port 8003) ───────────────
test("CV Generator /health", "http://localhost:8003/health")

cv_payload = {
    "personal": {
        "name": "Ahmed Ali",
        "email": "ahmed@example.com",
        "phone": "+20 100 000 0000",
        "location": "Cairo, Egypt",
        "summary": "Python developer with 3 years experience in FastAPI and REST APIs.",
    },
    "experience": [
        {
            "company": "Tech Corp",
            "title": "Backend Developer",
            "start_date": "Jul 2022",
            "end_date": "Present",
            "bullets": [
                "Built REST APIs serving 100K+ daily users",
                "Reduced query latency by 40% via database indexing",
            ],
        }
    ],
    "skills": {
        "technical": ["Python", "FastAPI", "PostgreSQL", "Redis"],
        "tools": ["Docker", "Git", "AWS"],
        "soft": ["Communication", "Problem Solving"],
    },
    "education": [
        {
            "institution": "Cairo University",
            "degree": "BSc",
            "field": "Computer Science",
            "start_date": "Sep 2018",
            "end_date": "Jun 2022",
            "gpa": "3.7",
        }
    ],
    "target_job_title": "Backend Developer",
}
test("CV Generator /generate-cv", "http://localhost:8003/api/v1/generate-cv", data=cv_payload)

# ─────────────── Chatbot (port 8004) ───────────────
test("Chatbot      /health", "http://localhost:8004/health")

# ─────────────── Post Generator (port 8005) ───────────────
test("Post Gen     /health", "http://localhost:8005/health")

# ─────────────── Print Results ───────────────
print()
print("=" * 65)
print("  FULL TEST RESULTS")
print("=" * 65)
for status, name, payload in results:
    print(f"{status}  {name}")
    if status == FAIL:
        print(f"         ERROR: {payload}")
    elif isinstance(payload, dict):
        if "status" in payload and "service" in payload:
            print(f"         -> service={payload['service']} status={payload['status']}")
        elif "mbti_type" in payload:
            cats = payload.get("marketing_categories", [])[:2]
            bf   = payload.get("big_five_mapping", {})
            print(f"         -> MBTI: {payload['mbti_type']}")
            print(f"            Recommended: {cats}")
            print(f"            Big Five: {bf}")
        elif "total" in payload:
            print(f"         -> {payload['total']} questions loaded")
        elif "cv_text" in payload:
            score = payload.get("ats_score")
            grade = payload.get("ats_grade")
            pdf   = payload.get("pdf_url")
            kw    = payload.get("matched_keywords", [])[:4]
            sug   = payload.get("suggestions", [])[:2]
            print(f"         -> ATS Score : {score}/100  Grade: {grade}")
            print(f"            PDF URL   : {pdf}")
            print(f"            Matched KW: {kw}")
            print(f"            Top Suggestions: {sug}")

passed = sum(1 for s, _, _ in results if s == PASS)
failed = len(results) - passed
print()
print(f"  Result: {passed}/{len(results)} passed", "✓" if failed == 0 else f"  ({failed} failed)")
print("=" * 65)
