# NANDA Agent Reputation Service

A trust layer for the Internet of AI Agents, built for **NandaHack** (HCLTech × MIT Media Lab).

One agent can check another agent's trust score **before** transacting, and
submit a vouch or flag **after**. An AI agent can discover and use this service
entirely on its own by reading [`SKILL.md`](./SKILL.md) — no human in the loop.

Live deployment: **https://nanda-reputation-yeyj.vercel.app**

## Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET  | `/health` | Health check |
| GET  | `/reputation/{agent_id}` | Get an agent's trust score + recent feedback |
| POST | `/reputation/{agent_id}/vouch` | Record positive feedback |
| POST | `/reputation/{agent_id}/flag` | Record negative feedback |

Trust score is 0.0–1.0 (Laplace-smoothed vouch/flag ratio). New agents start at 0.5.

### Agent ID format

Every agent ID (both the `{agent_id}` path segment and the `from` field in
request bodies) must match:

```text
agent://nanda/<non-empty-identifier>
```

where `<non-empty-identifier>` is one or more letters, digits, `.`, `_`, or `-`.

IDs are accepted either raw or percent-encoded — e.g. both
`agent://nanda/ritwik` and `agent%3A%2F%2Fnanda%2Fritwik` resolve to the same
agent, and responses always return the decoded form.

Requests with an invalid `agent_id` or `from` return `400`. An agent may not
vouch for or flag itself (`from` equal to the target `agent_id` also returns
`400`).

### Request bodies

**`POST /reputation/{agent_id}/vouch`**

| Field | Required | Notes |
| ----- | -------- | ----- |
| `from` | yes | Sender's own agent ID, `agent://nanda/<id>` format |
| `note` | no | Free text, max 500 characters |

**`POST /reputation/{agent_id}/flag`**

| Field | Required | Notes |
| ----- | -------- | ----- |
| `from` | yes | Sender's own agent ID, `agent://nanda/<id>` format |
| `reason` | yes | Free text, max 500 characters |

## Run locally

```bash
cp .env.example .env   # optional: only needed for persistent storage
pip install -r requirements.txt
python api/index.py          # serves on http://localhost:5000
python -m pytest test_app.py # run the test suite
```

With no environment variables set, it uses an in-memory store (resets on
restart) — perfect for local testing.

## Deploy to Vercel (free)

1. Push this folder to a GitHub repo.
2. Go to vercel.com → **Add New Project** → import the repo → **Deploy**.
   Vercel auto-detects `vercel.json` and `@vercel/python`.
3. **Add persistent storage** so data survives between requests:
   - Create a free database at [upstash.com](https://upstash.com) → Redis.
   - Copy its `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`.
   - In Vercel → Project → **Settings → Environment Variables**, add both.
     See `.env.example` for the exact variable names.
   - Redeploy.
4. Your service is live at `https://nanda-reputation-yeyj.vercel.app`.

## Test the live service

```bash
curl https://nanda-reputation-yeyj.vercel.app/health

curl https://nanda-reputation-yeyj.vercel.app/reputation/agent://nanda/agentX

curl -X POST https://nanda-reputation-yeyj.vercel.app/reputation/agent://nanda/agentX/vouch \
     -H "Content-Type: application/json" \
     -d '{"from":"agent://nanda/me","note":"paid on time"}'
```

## Submit to NandaHack

On the NANDA Town skills page, submit:
- this GitHub repo link,
- the live `https://nanda-reputation-yeyj.vercel.app` endpoint,
- and `SKILL.md`.

## License

MIT — see [LICENSE](./LICENSE).
