"""HTTP lab contract tests; no Ollama or Windows execution."""
from fastapi.testclient import TestClient
from jarvis_lab.api import LabConfig, create_app
from wyzer.brain.provider import FakeChatProvider
from wyzer.models import ChatMessage, ProviderChatResponse

TOKEN = "strong-test-only-token-123456"


def mock_provider():
    return FakeChatProvider([
        ProviderChatResponse(message=ChatMessage(role="assistant", content="Resposta do provedor de teste"))
    ])


def test_http_health_reports_no_model_when_not_configured():
    with TestClient(create_app(LabConfig(token=TOKEN))) as client:
        info = client.get("/api/v1/health").json()
        assert info["inference_configured"] is False
        assert info["computer_control"] is False
        assert info["speech_enabled"] is False


def test_html_uses_vexel_font_token_and_no_external_font_resource():
    with TestClient(create_app(LabConfig(token=TOKEN))) as client:
        html = client.get("/")
        css = client.get("/lab.css")
        assert html.status_code == 200
        assert "JARVIS" in html.text
        assert "VEXEL" in html.text
        assert css.status_code == 200
        assert "Inter" in css.text
        assert "fonts.googleapis" not in html.text + css.text


def test_session_and_chat_require_authentication():
    with TestClient(create_app(LabConfig(token=TOKEN), provider_factory=mock_provider)) as client:
        assert client.post("/api/v1/sessions").status_code == 401
        assert client.post("/api/v1/sessions", headers={"X-Jarvis-Lab-Token":"wrong"}).status_code == 401
        auth = {"X-Jarvis-Lab-Token": TOKEN}
        new = client.post("/api/v1/sessions", headers=auth)
        assert new.status_code == 200
        sid = new.json()["session_id"]
        assert len(sid) >= 20
        assert client.post("/api/v1/chat", json={"session_id": sid,"message":"Olá"}).status_code == 401
        reply = client.post("/api/v1/chat", headers=auth, json={"session_id": sid,"message":"Olá"})
        assert reply.status_code == 200
        assert reply.json()["reply"] == "Resposta do provedor de teste"
        assert reply.json()["computer_control"] is False
        assert reply.headers["cache-control"] == "no-store"


def test_no_model_fails_closed_instead_of_fake_chat():
    auth = {"X-Jarvis-Lab-Token": TOKEN}
    with TestClient(create_app(LabConfig(token=TOKEN))) as client:
        res = client.post("/api/v1/sessions", headers=auth)
        assert res.status_code == 503
        assert res.json()["detail"] == "MODEL_UNAVAILABLE"


def test_short_lab_token_not_accepted():
    with TestClient(create_app(LabConfig(token="short"), provider_factory=mock_provider)) as client:
        result = client.post("/api/v1/sessions", headers={"X-Jarvis-Lab-Token":"short"})
        assert result.status_code == 503
        assert result.json()["detail"] == "LAB_AUTH_NOT_CONFIGURED"


def test_unknown_session_denied():
    auth = {"X-Jarvis-Lab-Token": TOKEN}
    with TestClient(create_app(LabConfig(token=TOKEN), provider_factory=mock_provider)) as client:
        res = client.post("/api/v1/chat", headers=auth, json={
            "session_id":"a"*32,"message":"Olá"
        })
        assert res.status_code == 404
        assert res.json()["detail"] == "SESSION_NOT_FOUND"


def test_response_headers_block_inline_scripts_and_frames():
    with TestClient(create_app(LabConfig(token=TOKEN))) as client:
        res = client.get("/")
        assert "script-src 'self'" in res.headers["content-security-policy"]
        assert res.headers["x-frame-options"] == "DENY"


def test_distinct_sessions_do_not_share_conversation_history():
    auth = {"X-Jarvis-Lab-Token": TOKEN}
    providers = []
    def factory():
        provider = FakeChatProvider([
            ProviderChatResponse(message=ChatMessage(role="assistant", content="Concluído"))
        ])
        providers.append(provider)
        return provider

    with TestClient(create_app(LabConfig(token=TOKEN), provider_factory=factory)) as client:
        first = client.post("/api/v1/sessions", headers=auth).json()["session_id"]
        second = client.post("/api/v1/sessions", headers=auth).json()["session_id"]
        assert first != second
        assert client.post("/api/v1/chat", headers=auth, json={
            "session_id": first, "message": "segredo-da-sessao-A"
        }).status_code == 200
        assert client.post("/api/v1/chat", headers=auth, json={
            "session_id": second, "message": "pedido-da-sessao-B"
        }).status_code == 200
        second_context = " ".join(m.content or "" for m in providers[1].requests[0][0])
        assert "pedido-da-sessao-B" in second_context
        assert "segredo-da-sessao-A" not in second_context


def test_rate_limit_is_enforced():
    auth = {"X-Jarvis-Lab-Token": TOKEN}
    with TestClient(create_app(LabConfig(
        token=TOKEN, max_requests_per_minute=2
    ), provider_factory=mock_provider)) as client:
        assert client.post("/api/v1/sessions", headers=auth).status_code == 200
        assert client.post("/api/v1/sessions", headers=auth).status_code == 200
        rejected = client.post("/api/v1/sessions", headers=auth)
        assert rejected.status_code == 429
        assert rejected.json()["detail"] == "RATE_LIMITED"


def test_provider_failure_does_not_expose_server_exception():
    auth = {"X-Jarvis-Lab-Token": TOKEN}
    with TestClient(create_app(
        LabConfig(token=TOKEN), provider_factory=lambda: FakeChatProvider([])
    )) as client:
        session_id = client.post("/api/v1/sessions", headers=auth).json()["session_id"]
        failed = client.post("/api/v1/chat", headers=auth, json={
            "session_id": session_id, "message": "Teste de falha"
        })
        assert failed.status_code == 503
        assert failed.json()["detail"] == "MODEL_REQUEST_FAILED"
        assert "scripted response" not in failed.text


def test_chat_body_limit_is_enforced():
    auth = {"X-Jarvis-Lab-Token": TOKEN}
    with TestClient(create_app(LabConfig(token=TOKEN), provider_factory=mock_provider)) as client:
        session_id = client.post("/api/v1/sessions", headers=auth).json()["session_id"]
        too_long = client.post("/api/v1/chat", headers=auth, json={
            "session_id": session_id, "message": "x" * 2001
        })
        assert too_long.status_code == 422
