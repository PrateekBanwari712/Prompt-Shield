from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_screen_returns_allow_placeholder():
    r = client.post("/screen", json={"prompt": "hello"})
    assert r.status_code == 200
    assert r.json()["verdict"] == "allow"


def test_empty_prompt_rejected():
    r = client.post("/screen", json={"prompt": ""})
    assert r.status_code == 422
