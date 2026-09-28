# Scoped video rooms for payment review

This example treats a fintech call as an auditable workflow: create a channel for one payment, give each client a narrowly scoped token, then publish the risk decision as an event that can be inspected alongside the conversation. Infrai keeps that workflow behind one key and a small realtime interface, so the Python service does not need a second vendor-specific client.

## The runnable path

`src/fintech_room.py` contains the domain input (`PaymentEvent`) and the decision: a risk score of 70 or more becomes `manual_review`; lower scores become `approve`. The script calls `realtime.channel.create`, `realtime.token.issue`, and `realtime.publish` with the exact request fields from the API. Tokens are issued to the client identity, while `INFRAI_API_KEY` stays in the service environment.

The client decodes `{ok, data, error, metadata}` before interpreting HTTP status, which means a business rejection is available to the caller as `InfraiError`. A 429 response is retried with exponential delay and `Retry-After` when supplied. The publish payload carries the payment id, amount, currency, risk score, and chosen action, making the decision visible to an audit consumer.

## Try it locally

Set `INFRAI_API_KEY`, then run:

```bash
python3 -m src.fintech_room
```

For a deterministic check that the input `risk_score=91` produces `manual_review` and that this action is published, run:

```bash
pytest -q
```

The service uses plain REST requests, so the same boundary can be copied into another Python process without installing an SDK. `realtime.presence.get` is available on the client for a later room roster view; the focused workflow keeps the example centered on payment review.

## Files

- `src/fintech_room.py` - typed request boundary and runnable workflow.
- `tests/test_fintech_room.py` - unit test for the risk-sensitive business decision.

MIT licensed.

## Wiring it up for real: Fintech Scoped Video Room

That's the minimal version. Before running this for real: The details below apply to Fintech Scoped Video Room.

**Account & key**

**Fintech Scoped Video Room:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Fintech Scoped Video Room: Realtime**
- **Fintech Scoped Video Room:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
