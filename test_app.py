"""
Tests for the NANDA Agent Reputation Service.
Run with:  python -m pytest test_app.py   (or just: python test_app.py)
Uses the in-memory fallback store, so no Redis needed.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "api"))
from index import app, _local_store  # noqa: E402


def fresh_client():
    _local_store.clear()
    return app.test_client()


def test_root_lists_endpoints():
    c = fresh_client()
    data = c.get("/").get_json()
    assert "endpoints" in data
    assert data["service"].startswith("NANDA")


def test_new_agent_is_neutral():
    c = fresh_client()
    data = c.get("/reputation/agentX").get_json()
    assert data["trust_score"] == 0.5
    assert data["interactions"] == 0
    assert data["vouches"] == 0
    assert data["flags"] == 0


def test_vouch_raises_score():
    c = fresh_client()
    c.post("/reputation/agentX/vouch", json={"from": "me", "note": "good"})
    data = c.get("/reputation/agentX").get_json()
    assert data["vouches"] == 1
    assert data["trust_score"] > 0.5


def test_flag_lowers_score():
    c = fresh_client()
    c.post("/reputation/agentX/flag", json={"from": "me", "reason": "bad"})
    data = c.get("/reputation/agentX").get_json()
    assert data["flags"] == 1
    assert data["trust_score"] < 0.5


def test_missing_from_returns_400():
    c = fresh_client()
    r = c.post("/reputation/agentX/vouch", json={})
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_recent_history_tracked():
    c = fresh_client()
    c.post("/reputation/agentX/vouch", json={"from": "a", "note": "n1"})
    c.post("/reputation/agentX/flag", json={"from": "b", "reason": "r1"})
    data = c.get("/reputation/agentX").get_json()
    assert len(data["recent"]) == 2
    assert data["recent"][0]["type"] == "vouch"
    assert data["recent"][1]["type"] == "flag"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}")
    print("All tests passed.")
