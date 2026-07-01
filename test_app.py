"""
Tests for the NANDA Agent Reputation Service.
Run with:  python -m pytest test_app.py   (or just: python test_app.py)
Uses the in-memory fallback store, so no Redis needed.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))
from index import app, _local_store  # noqa: E402

RITWIK = "agent://nanda/ritwik"
ALICE = "agent://nanda/alice"
RITWIK_ENCODED = "agent%3A%2F%2Fnanda%2Fritwik"


def fresh_client():
    _local_store.clear()
    return app.test_client()


# --- basic endpoints -------------------------------------------------------

def test_root_lists_endpoints():
    c = fresh_client()
    data = c.get("/").get_json()
    assert "endpoints" in data
    assert data["service"].startswith("NANDA")


def test_health_endpoint():
    c = fresh_client()
    r = c.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_new_agent_is_neutral():
    c = fresh_client()
    data = c.get(f"/reputation/{ALICE}").get_json()
    assert data["trust_score"] == 0.5
    assert data["interactions"] == 0
    assert data["vouches"] == 0
    assert data["flags"] == 0


# --- security headers -------------------------------------------------------

def test_security_headers_present():
    c = fresh_client()
    r = c.get("/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Cache-Control"] == "no-store"


# --- encoded ID decoding -----------------------------------------------------

def test_encoded_agent_id_is_decoded_on_get():
    c = fresh_client()
    r = c.get(f"/reputation/{RITWIK_ENCODED}")
    data = r.get_json()
    assert r.status_code == 200
    assert data["agent_id"] == RITWIK


def test_encoded_agent_id_is_decoded_on_vouch():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK_ENCODED}/vouch",
               json={"from": ALICE, "note": "good"})
    assert r.status_code == 200
    data = c.get(f"/reputation/{RITWIK}").get_json()
    assert data["agent_id"] == RITWIK
    assert data["vouches"] == 1


def test_encoded_sender_is_decoded():
    c = fresh_client()
    encoded_alice = "agent%3A%2F%2Fnanda%2Falice"
    c.post(f"/reputation/{RITWIK}/vouch",
           json={"from": encoded_alice, "note": "good"})
    data = c.get(f"/reputation/{RITWIK}").get_json()
    assert data["recent"][-1]["from"] == ALICE


# --- valid vouch / flag ------------------------------------------------------

def test_valid_vouch_raises_score():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK}/vouch",
               json={"from": ALICE, "note": "paid on time"})
    assert r.status_code == 200
    data = c.get(f"/reputation/{RITWIK}").get_json()
    assert data["vouches"] == 1
    assert data["trust_score"] > 0.5


def test_valid_flag_lowers_score():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK}/flag",
               json={"from": ALICE, "reason": "did not deliver"})
    assert r.status_code == 200
    data = c.get(f"/reputation/{RITWIK}").get_json()
    assert data["flags"] == 1
    assert data["trust_score"] < 0.5


def test_recent_history_tracked():
    c = fresh_client()
    c.post(f"/reputation/{RITWIK}/vouch", json={"from": ALICE, "note": "n1"})
    c.post(f"/reputation/{RITWIK}/flag", json={"from": ALICE, "reason": "r1"})
    data = c.get(f"/reputation/{RITWIK}").get_json()
    assert len(data["recent"]) == 2
    assert data["recent"][0]["type"] == "vouch"
    assert data["recent"][1]["type"] == "flag"


# --- invalid IDs --------------------------------------------------------

def test_invalid_target_id_rejected_on_get():
    c = fresh_client()
    r = c.get("/reputation/not-a-valid-id")
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_invalid_target_id_rejected_on_vouch():
    c = fresh_client()
    r = c.post("/reputation/not-a-valid-id/vouch", json={"from": ALICE})
    assert r.status_code == 400


def test_invalid_sender_id_rejected():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK}/vouch", json={"from": "not-a-valid-id"})
    assert r.status_code == 400


def test_missing_from_returns_400():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK}/vouch", json={})
    assert r.status_code == 400
    assert "error" in r.get_json()


# --- self-rating rejection ----------------------------------------------

def test_self_vouch_rejected():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK}/vouch",
               json={"from": RITWIK, "note": "nice"})
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_self_flag_rejected():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK}/flag",
               json={"from": RITWIK, "reason": "nice"})
    assert r.status_code == 400
    assert "error" in r.get_json()


# --- note / reason validation --------------------------------------------

def test_vouch_without_note_is_ok():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK}/vouch", json={"from": ALICE})
    assert r.status_code == 200


def test_vouch_note_too_long_rejected():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK}/vouch",
               json={"from": ALICE, "note": "x" * 501})
    assert r.status_code == 400


def test_flag_missing_reason_rejected():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK}/flag", json={"from": ALICE})
    assert r.status_code == 400


def test_flag_reason_too_long_rejected():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK}/flag",
               json={"from": ALICE, "reason": "x" * 501})
    assert r.status_code == 400


def test_flag_reason_at_limit_is_ok():
    c = fresh_client()
    r = c.post(f"/reputation/{RITWIK}/flag",
               json={"from": ALICE, "reason": "x" * 500})
    assert r.status_code == 200


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("All tests passed.")
