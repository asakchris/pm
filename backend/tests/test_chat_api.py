from fastapi.testclient import TestClient

from app.main import app
import app.routes.chat as chat_module

client = TestClient(app)


def test_chat_missing_api_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setattr(chat_module, "_check_rate_limit", lambda _username: None)
    response = client.post("/api/chat", json={"message": "2+2"})
    assert response.status_code == 500
    assert response.json() == {"detail": "OPENROUTER_API_KEY not configured"}
