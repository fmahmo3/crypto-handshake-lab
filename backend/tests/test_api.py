"""Integration tests for the FastAPI endpoints.

Uses FastAPI's synchronous TestClient (backed by httpx) so no async
infrastructure is needed.
"""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from api.main import app

    return TestClient(app)


@pytest.fixture
def session_id(client):
    """Create a fresh session and return its ID."""
    resp = client.post("/handshake/start")
    return resp.json()["session_id"]


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------


def test_root_returns_metadata(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["version"] == "0.1.0"
    assert "endpoints" in data


# ---------------------------------------------------------------------------
# POST /handshake/start
# ---------------------------------------------------------------------------


def test_start_returns_session_id(client):
    resp = client.post("/handshake/start")
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert len(data["session_id"]) == 36  # UUID4 format


def test_start_initial_step_is_zero(client):
    resp = client.post("/handshake/start")
    assert resp.json()["current_step"] == 0


def test_start_reports_nine_total_steps(client):
    resp = client.post("/handshake/start")
    assert resp.json()["total_steps"] == 9


def test_start_tamper_mode_is_false(client):
    resp = client.post("/handshake/start")
    assert resp.json()["tamper_mode"] is False


def test_start_with_custom_plaintext(client):
    resp = client.post("/handshake/start", json={"plaintext": "Custom secret"})
    assert resp.status_code == 200
    assert resp.json()["plaintext"] == "Custom secret"


def test_start_default_plaintext(client):
    from crypto_engine.handshake import DEFAULT_MESSAGE

    resp = client.post("/handshake/start")
    assert resp.json()["plaintext"] == DEFAULT_MESSAGE


def test_each_start_creates_unique_session(client):
    id1 = client.post("/handshake/start").json()["session_id"]
    id2 = client.post("/handshake/start").json()["session_id"]
    assert id1 != id2


# ---------------------------------------------------------------------------
# POST /handshake/{session_id}/advance
# ---------------------------------------------------------------------------


def test_advance_increments_step(client, session_id):
    resp = client.post(f"/handshake/{session_id}/advance")
    assert resp.status_code == 200
    data = resp.json()
    assert data["current_step"] == 1
    assert data["is_complete"] is False


def test_advance_first_step_is_dh_params(client, session_id):
    resp = client.post(f"/handshake/{session_id}/advance")
    step = resp.json()["step"]
    assert step["step"] == 1
    assert step["name"] == "DH Parameter Generation"
    assert "p" in step["values"]
    assert "g" in step["values"]


def test_advance_through_all_steps(client, session_id):
    for expected in range(1, 10):
        resp = client.post(f"/handshake/{session_id}/advance")
        assert resp.status_code == 200
        assert resp.json()["current_step"] == expected
    assert resp.json()["is_complete"] is True


def test_advance_beyond_complete_returns_400(client, session_id):
    for _ in range(9):
        client.post(f"/handshake/{session_id}/advance")
    resp = client.post(f"/handshake/{session_id}/advance")
    assert resp.status_code == 400


def test_advance_unknown_session_returns_404(client):
    resp = client.post("/handshake/does-not-exist/advance")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /handshake/{session_id}/step/{step_number}
# ---------------------------------------------------------------------------


def test_get_step_returns_correct_step(client, session_id):
    client.post(f"/handshake/{session_id}/advance")  # execute step 1
    resp = client.get(f"/handshake/{session_id}/step/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["step"] == 1
    assert data["name"] == "DH Parameter Generation"


def test_get_step_before_execution_returns_404(client, session_id):
    resp = client.get(f"/handshake/{session_id}/step/1")
    assert resp.status_code == 404


def test_get_step_unknown_session_returns_404(client):
    resp = client.get("/handshake/ghost/step/1")
    assert resp.status_code == 404


def test_get_step_includes_session_id(client, session_id):
    client.post(f"/handshake/{session_id}/advance")
    resp = client.get(f"/handshake/{session_id}/step/1")
    assert resp.json()["session_id"] == session_id


# ---------------------------------------------------------------------------
# POST /handshake/{session_id}/tamper
# ---------------------------------------------------------------------------


def test_enable_tamper_sets_flag(client, session_id):
    resp = client.post(f"/handshake/{session_id}/tamper")
    assert resp.status_code == 200
    assert resp.json()["tamper_mode"] is True


def test_tamper_after_complete_returns_400(client, session_id):
    client.get(f"/handshake/{session_id}/full")  # run all steps
    resp = client.post(f"/handshake/{session_id}/tamper")
    assert resp.status_code == 400


def test_tamper_unknown_session_returns_404(client):
    resp = client.post("/handshake/ghost/tamper")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /handshake/{session_id}/full
# ---------------------------------------------------------------------------


def test_full_returns_all_nine_steps(client, session_id):
    resp = client.get(f"/handshake/{session_id}/full")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["steps"]) == 9


def test_full_handshake_succeeds_without_tamper(client, session_id):
    resp = client.get(f"/handshake/{session_id}/full")
    final = resp.json()["steps"][-1]
    assert final["values"]["handshake_success"] is True
    assert final["values"]["error"] is None


def test_full_includes_plaintext(client, session_id):
    from crypto_engine.handshake import DEFAULT_MESSAGE

    resp = client.get(f"/handshake/{session_id}/full")
    assert resp.json()["plaintext"] == DEFAULT_MESSAGE


def test_full_marks_session_complete(client, session_id):
    resp = client.get(f"/handshake/{session_id}/full")
    assert resp.json()["is_complete"] is True


def test_full_unknown_session_returns_404(client):
    resp = client.get("/handshake/ghost/full")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tamper mode end-to-end
# ---------------------------------------------------------------------------


def test_full_tamper_mode_fails_verification(client):
    sid = client.post("/handshake/start").json()["session_id"]
    client.post(f"/handshake/{sid}/tamper")
    resp = client.get(f"/handshake/{sid}/full")
    final = resp.json()["steps"][-1]
    assert final["tampered"] is True
    assert final["values"]["hmac_verified"] is False
    assert final["values"]["handshake_success"] is False
    assert final["values"]["decrypted_message"] is None
    assert final["values"]["error"] is not None


def test_tamper_mode_reflected_in_full_response(client):
    sid = client.post("/handshake/start").json()["session_id"]
    client.post(f"/handshake/{sid}/tamper")
    resp = client.get(f"/handshake/{sid}/full")
    assert resp.json()["tamper_mode"] is True


# ---------------------------------------------------------------------------
# Partial advance then full
# ---------------------------------------------------------------------------


def test_partial_advance_then_full(client):
    sid = client.post("/handshake/start").json()["session_id"]
    client.post(f"/handshake/{sid}/advance")  # step 1
    client.post(f"/handshake/{sid}/advance")  # step 2
    resp = client.get(f"/handshake/{sid}/full")  # steps 3–9
    assert len(resp.json()["steps"]) == 9


def test_full_idempotent_after_complete(client):
    """Calling /full on an already-complete session should return all steps."""
    sid = client.post("/handshake/start").json()["session_id"]
    client.get(f"/handshake/{sid}/full")  # run once
    resp = client.get(f"/handshake/{sid}/full")  # call again
    assert resp.status_code == 200
    assert len(resp.json()["steps"]) == 9
