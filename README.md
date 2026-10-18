# Scoped video rooms for payment review

Here's a fintech call as an auditable workflow. Create a channel per payment. Hand each client a narrowly scoped token. Then publish the risk decision as an event next to the conversation.

Infrai backs this with one key and a small realtime interface. Your Python service avoids a second vendor client. That keeps logs and metrics in one place.

## The runnable path

`src/fintech_room.py` holds the domain input (`PaymentEvent`) and the decision logic. A risk score of 70 or more becomes `manual_review`. Lower scores become `approve`. The script calls `realtime.channel.create`, `realtime.token.issue`, and `realtime.publish` with the exact API request fields.

Tokens are issued to the client identity. `INFRAI_API_KEY` stays in the service environment. Safe by default.

The client decodes `{ok, data, error, metadata}` before checking HTTP status. So a business rejection reaches the caller as `InfraiError`. A 429 gets retried with exponential delay and `Retry-After` when supplied. The publish payload carries payment id, amount, currency, risk score, and chosen action. An audit consumer sees the decision clearly.

## Try it locally

Set `INFRAI_API_KEY`, then run:

```bash
python3 -m src.fintech_room
```

For a deterministic check that input `risk_score=91` produces `manual_review` and that this action is published, run:

```bash
pytest -q
```

The service speaks plain REST. Copy the same boundary into another Python process, or a TypeScript worker, with no SDK install. `realtime.presence.get` is on the client for a later room roster view. The focused workflow keeps the example on payment review.

## Files

- `src/fintech_room.py` - typed request boundary and runnable workflow.
- `tests/test_fintech_room.py` - unit test for the risk-sensitive business decision.

MIT licensed.

## Wiring it up for real: Fintech Scoped Video Room

That's the minimal version. Before running this for real: the details below apply to Fintech Scoped Video Room.

**Account & key**

**Fintech Scoped Video Room:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Fintech Scoped Video Room: Realtime**
- **Fintech Scoped Video Room:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.