"""
NANDA Agent Reputation Service
A trust layer for the Internet of AI Agents.

Lets one agent check another agent's trust score before transacting,
and submit a vouch (positive) or flag (negative) after an interaction.

Storage: Upstash Redis (free tier) via REST API. Falls back to an
in-memory store if Redis env vars are not set, so it also runs locally.
"""

import os
import json
import time
import urllib.request
import urllib.parse
from flask import Flask, request, jsonify

app = Flask(__name__)

# --- Storage layer -------------------------------------------------------

UPSTASH_URL = os.environ.get("UPSTASH_REDIS_REST_URL")
UPSTASH_TOKEN = os.environ.get("UPSTASH_REDIS_REST_TOKEN")

# In-memory fallback for local testing (resets on restart)
_local_store = {}


def _redis(*command):
    """Run a Redis command via Upstash REST API, or use local store."""
    if not (UPSTASH_URL and UPSTASH_TOKEN):
        return _local_command(*command)
    path = "/".join(urllib.parse.quote(str(c), safe="") for c in command)
    req = urllib.request.Request(
        f"{UPSTASH_URL}/{path}",
        headers={"Authorization": f"Bearer {UPSTASH_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read()).get("result")


def _local_command(*command):
    """Minimal local emulation of the few Redis commands we use."""
    cmd = command[0].upper()
    if cmd == "GET":
        return _local_store.get(command[1])
    if cmd == "SET":
        _local_store[command[1]] = command[2]
        return "OK"
    return None


def _load(agent_id):
    raw = _redis("GET", f"agent:{agent_id}")
    if raw:
        return json.loads(raw)
    return {"agent_id": agent_id, "vouches": 0, "flags": 0, "recent": []}


def _save(agent_id, record):
    _redis("SET", f"agent:{agent_id}", json.dumps(record))


def _score(record):
    """Trust score 0.0-1.0. New agents start neutral-ish, settle with data."""
    v, f = record["vouches"], record["flags"]
    total = v + f
    if total == 0:
        return 0.5
    # Laplace-smoothed ratio so a single vouch/flag isn't extreme.
    return round((v + 1) / (total + 2), 3)


# --- Routes --------------------------------------------------------------

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "NANDA Agent Reputation Service",
        "description": "A trust layer for AI agents. Check an agent before "
                       "you transact; vouch or flag it after.",
        "endpoints": {
            "GET /reputation/<agent_id>": "Get an agent's trust score",
            "POST /reputation/<agent_id>/vouch": "Record positive feedback",
            "POST /reputation/<agent_id>/flag": "Record negative feedback",
        },
        "skill": "See SKILL.md in the repository.",
    })


@app.route("/reputation/<path:agent_id>", methods=["GET"])
def get_reputation(agent_id):
    record = _load(agent_id)
    total = record["vouches"] + record["flags"]
    return jsonify({
        "agent_id": agent_id,
        "trust_score": _score(record),
        "interactions": total,
        "vouches": record["vouches"],
        "flags": record["flags"],
        "recent": record["recent"][-5:],
    })


@app.route("/reputation/<path:agent_id>/vouch", methods=["POST"])
def vouch(agent_id):
    body = request.get_json(silent=True) or {}
    sender = body.get("from")
    if not sender:
        return jsonify({"error": "Missing required field 'from' "
                                 "(your own NANDA ID)."}), 400
    record = _load(agent_id)
    record["vouches"] += 1
    record["recent"].append({
        "from": sender,
        "type": "vouch",
        "note": body.get("note", ""),
        "ts": _now(),
    })
    record["recent"] = record["recent"][-20:]
    _save(agent_id, record)
    return jsonify({"status": "recorded", "new_score": _score(record)})


@app.route("/reputation/<path:agent_id>/flag", methods=["POST"])
def flag(agent_id):
    body = request.get_json(silent=True) or {}
    sender = body.get("from")
    if not sender:
        return jsonify({"error": "Missing required field 'from' "
                                 "(your own NANDA ID)."}), 400
    record = _load(agent_id)
    record["flags"] += 1
    record["recent"].append({
        "from": sender,
        "type": "flag",
        "reason": body.get("reason", ""),
        "ts": _now(),
    })
    record["recent"] = record["recent"][-20:]
    _save(agent_id, record)
    return jsonify({"status": "recorded", "new_score": _score(record)})


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# Vercel looks for `app`. This also lets you run it locally with `python api/index.py`.
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
