import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fintech_room import PaymentEvent, open_fintech_session


class FakeRealtime:
    def __init__(self):
        self.published = []

    def create_channel(self, channel):
        return {"ok": True}

    def issue_token(self, client_id, channel, can_publish, can_subscribe):
        return {"ok": True, "data": {"token": "scoped"}}

    def publish(self, channel, event, data, account_id):
        self.published.append(data)
        return {"ok": True}


def test_high_risk_payment_requires_manual_review():
    fake = FakeRealtime()
    result = open_fintech_session(fake, "acct-1", PaymentEvent("pay-7", 5000, "USD", 91))
    assert result["action"] == "manual_review"
    assert fake.published[0]["action"] == "manual_review"
