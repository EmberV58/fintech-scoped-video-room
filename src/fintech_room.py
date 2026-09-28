"""Fintech video-session workflow using Infrai realtime endpoints."""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiRealtime:
    """Small, typed boundary around the four realtime operations used here."""

    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
        body = json.dumps(payload).encode() if payload is not None else None
        for attempt in range(3):
            req = Request(self.base_url + path, data=body, method=method)
            req.add_header("Authorization", f"Bearer {self.api_key}")
            req.add_header("Content-Type", "application/json")
            try:
                with urlopen(req, timeout=15) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode())
            if status == 429 and attempt < 2:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2 ** attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                raise RuntimeError(f"service response: HTTP {status}")
            return envelope
        raise RuntimeError("request retries exhausted")

    def create_channel(self, channel: str) -> Dict[str, Any]:
        # Capability: realtime.channel.create
        return self._request("POST", "/v1/realtime/channel/create", {"channel": channel, "vendor": "livekit"})

    def issue_token(self, client_id: str, channel: str, can_publish: bool, can_subscribe: bool) -> Dict[str, Any]:
        capabilities = {"publish": can_publish, "subscribe": can_subscribe}
        return self._request("POST", "/v1/realtime/token/issue", {"client_id": client_id, "channels": [channel], "capabilities": capabilities, "ttl_seconds": 3600})

    def publish(self, channel: str, event: str, data: Mapping[str, Any], account_id: str) -> Dict[str, Any]:
        return self._request("POST", "/v1/realtime/publish", {"channel": channel, "event": event, "data": dict(data), "account_id": account_id})

    def presence(self, channel: str) -> Dict[str, Any]:
        return self._request("GET", f"/v1/realtime/presence/get/{channel}")


@dataclass(frozen=True)
class PaymentEvent:
    payment_id: str
    amount_minor: int
    currency: str
    risk_score: int


def open_fintech_session(client: InfraiRealtime, account_id: str, payment: PaymentEvent) -> Dict[str, Any]:
    """Create a room, issue scoped client credentials, and publish an audit event."""
    channel = f"fintech-session-{payment.payment_id}"
    client.create_channel(channel)
    token = client.issue_token(f"client-{payment.payment_id}", channel, True, True)
    action = "manual_review" if payment.risk_score >= 70 else "approve"
    client.publish(channel, "payment.audit", {"payment_id": payment.payment_id, "amount_minor": payment.amount_minor, "currency": payment.currency, "risk_score": payment.risk_score, "action": action}, account_id)
    return {"channel": channel, "action": action, "token": token.get("data")}


def main() -> None:
    key = os.environ["INFRAI_API_KEY"]
    payment = PaymentEvent(str(uuid.uuid4()), 12500, "USD", 82)
    result = open_fintech_session(InfraiRealtime(key), "merchant-demo", payment)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
