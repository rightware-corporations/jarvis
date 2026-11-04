"""Private, fail-closed HTTP lab; no real desktop tools.

Run only behind authenticated HTTPS and a single trusted reverse proxy. This is
not a production deployment, tenancy solution, voice server or Windows agent.
"""
from __future__ import annotations

import asyncio
import hmac
import os
import secrets
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from wyzer.brain.provider import ChatProvider
from wyzer.brain.providers import OllamaChatProvider
from .headless import MODEL_FAILURE_SENTINEL, create_headless_assistant


WEB_DIR = Path(__file__).resolve().parent / "web"


class LabConfig(BaseModel):
    token: str = ""
    model: str = ""
    ollama_url: str = "http://127.0.0.1:11434"
    session_ttl_seconds: int = Field(default=900, ge=60, le=3600)
    max_sessions: int = Field(default=32, ge=1, le=200)
    max_requests_per_minute: int = Field(default=24, ge=1, le=120)

    @classmethod
    def from_env(cls) -> "LabConfig":
        return cls(
            token=os.getenv("JARVIS_LAB_TOKEN", ""),
            model=os.getenv("JARVIS_OLLAMA_MODEL", ""),
            ollama_url=os.getenv("JARVIS_OLLAMA_URL", "http://127.0.0.1:11434"),
        )


class ChatBody(BaseModel):
    session_id: str = Field(min_length=20, max_length=128)
    message: str = Field(min_length=1, max_length=2000)


@dataclass
class LabSession:
    assistant: object
    expires_at: float


def create_app(
    config: LabConfig | None = None,
    *,
    provider_factory: Callable[[], ChatProvider] | None = None,
) -> FastAPI:
    """The injected provider_factory is for test cases, never an HTTP argument."""
    settings = config or LabConfig.from_env()
    app = FastAPI(title="VEXEL Jarvis Lab", docs_url=None, redoc_url=None, openapi_url=None)
    sessions: dict[str, LabSession] = {}
    requests_by_host: dict[str, deque[float]] = defaultdict(deque)
    state_lock = asyncio.Lock()

    def provider_ready() -> bool:
        return bool(provider_factory or settings.model.strip())

    def new_provider() -> ChatProvider:
        if provider_factory is not None:
            return provider_factory()
        return OllamaChatProvider(
            endpoint=settings.ollama_url,
            model=settings.model,
            auto_start=False,
            timeout_seconds=30,
            context_length=8192,
            max_output_tokens=500,
            temperature=0.15,
        )

    async def authorize(request: Request, token: str | None) -> None:
        if not settings.token or len(settings.token) < 16:
            raise HTTPException(503, detail="LAB_AUTH_NOT_CONFIGURED")
        if token is None or not hmac.compare_digest(
            token.encode("utf-8"), settings.token.encode("utf-8")
        ):
            raise HTTPException(401, detail="UNAUTHORIZED")
        address = request.client.host if request.client else "unknown"
        now = time.monotonic()
        async with state_lock:
            attempts = requests_by_host[address]
            while attempts and now - attempts[0] > 60:
                attempts.popleft()
            if len(attempts) >= settings.max_requests_per_minute:
                raise HTTPException(429, detail="RATE_LIMITED")
            attempts.append(now)

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self' data:; font-src 'self'; "
            "object-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        return response

    @app.get("/", include_in_schema=False)
    def homepage():
        return FileResponse(WEB_DIR / "index.html", media_type="text/html")

    @app.get("/lab.css", include_in_schema=False)
    def stylesheet():
        return FileResponse(WEB_DIR / "lab.css", media_type="text/css")

    @app.get("/lab.js", include_in_schema=False)
    def javascript():
        return FileResponse(WEB_DIR / "lab.js", media_type="text/javascript")

    @app.get("/api/v1/health")
    def health():
        return {
            "service": "jarvis-lab",
            "inference_configured": bool(settings.model),
            "runtime": "headless",
            "computer_control": False,
            "speech_enabled": False,
            "public_release": False,
        }

    @app.post("/api/v1/sessions")
    async def new_session(request: Request, x_jarvis_lab_token: str | None = Header(default=None)):
        await authorize(request, x_jarvis_lab_token)
        if not provider_ready():
            raise HTTPException(503, detail="MODEL_UNAVAILABLE")
        async with state_lock:
            now = time.monotonic()
            for key, session in list(sessions.items()):
                if session.expires_at <= now:
                    sessions.pop(key, None)
            if len(sessions) >= settings.max_sessions:
                raise HTTPException(429, detail="SESSION_CAPACITY_REACHED")
            session_id = secrets.token_urlsafe(32)
            # Random subject is unique per session. No persisted memory in web lab.
            assistant = create_headless_assistant(new_provider(), subject_id=session_id)
            sessions[session_id] = LabSession(
                assistant=assistant, expires_at=now + settings.session_ttl_seconds
            )
        return {"session_id": session_id, "expires_in": settings.session_ttl_seconds}

    @app.post("/api/v1/chat")
    async def chat(
        body: ChatBody, request: Request, x_jarvis_lab_token: str | None = Header(default=None)
    ):
        await authorize(request, x_jarvis_lab_token)
        async with state_lock:
            session = sessions.get(body.session_id)
            if session is None or session.expires_at <= time.monotonic():
                sessions.pop(body.session_id, None)
                raise HTTPException(404, detail="SESSION_NOT_FOUND")
            assistant = session.assistant
            session.expires_at = time.monotonic() + settings.session_ttl_seconds
        try:
            answer = await assistant.handle(body.message)
        except Exception:
            # Intentionally avoid returning provider errors or internal endpoints.
            raise HTTPException(503, detail="MODEL_REQUEST_FAILED") from None
        if answer.text == MODEL_FAILURE_SENTINEL:
            raise HTTPException(503, detail="MODEL_REQUEST_FAILED")
        return {"reply": answer.text, "mode": "headless", "computer_control": False}

    return app


app = create_app()
