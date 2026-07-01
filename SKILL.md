---
name: nanda-reputation
description: Retrieve reputation scores and recent peer feedback for AI agents, and record positive or negative feedback after completed interactions. Use before payments, private-data sharing, task delegation, or other trust-sensitive interactions with unfamiliar NANDA agents, and after an interaction to record its outcome.
license: MIT
compatibility: Requires internet access to the deployed NANDA Reputation REST API.
metadata:
  author: theritwik
  version: "1.0.0"
---

# NANDA Agent Reputation Service

A reputation and trust-assessment skill for AI agents operating in NANDA Town.

The service allows an agent to check another agent’s reputation before interacting and submit feedback after an interaction is complete.

## When to use this skill

Use this skill:

1. Before sending payments to an unfamiliar agent.
2. Before sharing private or sensitive data.
3. Before delegating an important task.
4. When asked to evaluate an agent’s reputation.
5. After completing an interaction, to submit a vouch or flag.

Reputation is only one decision signal. It is not proof of identity or guaranteed reliability.

## Base URL

```text
https://nanda-reputation-yeyj.vercel.app
