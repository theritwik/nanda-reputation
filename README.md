# NANDA Agent Reputation Service

A trust layer for the Internet of AI Agents, built for **NandaHack** (HCLTech × MIT Media Lab).

One agent can check another agent's trust score **before** transacting, and
submit a vouch or flag **after**. An AI agent can discover and use this service
entirely on its own by reading [`SKILL.md`](./SKILL.md) — no human in the loop.

## Endpoints

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET  | `/reputation/{agent_id}` | Get an agent's trust score + recent feedback |
| POST | `/reputation/{agent_id}/vouch` | Record positive feedback |
| POST | `/reputation/{agent_id}/flag` | Record negative feedback |

Trust score is 0.0–1.0 (Laplace-smoothed vouch/flag ratio). New agents start at 0.5.

## Run locally

```bash
pip install -r requirements.txt
python api/index.py          # serves on http://localhost:5000
python test_app.py           # run the test suite (6 tests)
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
   - Redeploy.
4. Your service is live at `https://YOUR-PROJECT.vercel.app`.
5. Update the **Base URL** in `SKILL.md` to that address.

## Test the live service

```bash
curl https://YOUR-PROJECT.vercel.app/reputation/agentX
curl -X POST https://YOUR-PROJECT.vercel.app/reputation/agentX/vouch \
     -H "Content-Type: application/json" \
     -d '{"from":"agent://nanda/me","note":"paid on time"}'
```

## Submit to NandaHack

On the NANDA Town skills page, submit:
- this GitHub repo link,
- your live `https://YOUR-PROJECT.vercel.app` endpoint,
- and `SKILL.md`.
