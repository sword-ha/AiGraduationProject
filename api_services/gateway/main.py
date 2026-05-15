import logging
import os

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="AI Graduation Project — Gateway",
    description=(
        "Unified gateway that routes to all AI microservices.\n\n"
        "| Prefix | Service | Local port |\n"
        "|--------|---------|------------|\n"
        "| `/api/v1/id/...` | Egyptian ID Verification | 8001 |\n"
        "| `/api/v1/personality/...` | MBTI Personality Analysis | 8002 |\n"
        "| `/api/v1/cv/...` | CV Generator | 8003 |\n"
        "| `/api/v1/chatbot/...` | Marketing Chatbot | 8004 |\n"
        "| `/api/v1/posts/...` | Social Media Post Generator | 8005 |\n"
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# (prefix, backend_base_url, strip_prefix)
ROUTES = (
    ("/api/v1/id",          "http://localhost:8001", "/api/v1/id"),
    ("/api/v1/personality", "http://localhost:8002", "/api/v1/personality"),
    ("/api/v1/cv",          "http://localhost:8003", "/api/v1/cv"),
    ("/api/v1/chatbot",     "http://localhost:8004", "/api/v1/chatbot"),
    ("/api/v1/posts",       "http://localhost:8005", "/api/v1/posts"),
)


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "gateway"}


@app.get("/services", tags=["Health"])
async def services():
    """List all available services and their endpoints."""
    return {
        "id_verification":  "POST /api/v1/id/verify-id",
        "personality":      "POST /api/v1/personality/analyze-personality  |  GET /api/v1/personality/questions",
        "cv_generator":     "POST /api/v1/cv/generate-cv  |  GET /api/v1/cv/download-cv/{filename}",
        "chatbot":          "POST /api/v1/chatbot/chat",
        "post_generator":   "POST /api/v1/posts/generate-post",
    }


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
async def proxy(request: Request, path: str):
    full_path = "/" + path

    # Match route
    backend_url = None
    for prefix, backend, strip_prefix in ROUTES:
        if full_path.startswith(prefix):
            remainder = full_path[len(strip_prefix):]
            backend_url = backend + prefix.replace("/api/v1/", "/api/v1/") + remainder
            # rebuild: backend keeps its own /api/v1/xxx prefix
            backend_url = backend + full_path
            break

    if backend_url is None:
        return JSONResponse(
            status_code=404,
            content={"detail": "Route not found. See /services for available endpoints."},
        )

    # Forward query string
    qs = request.url.query
    if qs:
        backend_url = backend_url + "?" + qs

    # Strip hop-by-hop headers
    _HOP_BY_HOP = frozenset({"connection", "transfer-encoding", "host", "content-length"})
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP_BY_HOP}

    body = await request.body()

    logging.getLogger(__name__).info(f"Proxying {request.method} /{path} → {backend_url}")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.request(
                method=request.method,
                url=backend_url,
                headers=headers,
                content=body,
            )
        resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in _HOP_BY_HOP}
        return Response(content=resp.content, status_code=resp.status_code, headers=resp_headers)

    except httpx.ConnectError:
        logging.getLogger(__name__).warning(f"Service at {backend_url} is not running")
        return JSONResponse(
            status_code=503,
            content={"detail": "Service is not running. Make sure all services are started."},
        )
