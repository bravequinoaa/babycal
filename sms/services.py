import logging
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    ok: bool
    provider: str
    detail: str


def send_sms(phone, message):
    """
    Stub SMS sender shaped after Twilio's client.messages.create(to=, from_=, body=)
    signature so wiring up real Twilio later is just adding credentials and
    replacing the body of this function — call sites never change.

    v1 always logs instead of sending, since no Twilio credentials are
    configured (SPEC.md section 5).
    """
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        # Real Twilio send would go here once credentials are configured.
        logger.warning(
            "Twilio credentials are set but send_sms() is still stubbed; "
            "logging instead of sending to %s", phone,
        )
    logger.info("send_sms() stub -> to=%s body=%r", phone, message)
    return SendResult(ok=True, provider="stub", detail="logged, not sent")
