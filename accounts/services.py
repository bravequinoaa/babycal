import logging

import phonenumbers
from django.conf import settings

from sms.services import send_sms

from .models import LoginOTP

logger = logging.getLogger(__name__)


class InvalidPhoneNumber(ValueError):
    pass


def normalize_phone(raw_phone, region="US"):
    """Normalize messy input like '(732) 986-1906' to E.164 (+17329861906)."""
    try:
        parsed = phonenumbers.parse(raw_phone, region)
    except phonenumbers.NumberParseException as exc:
        raise InvalidPhoneNumber(str(exc)) from exc
    if not phonenumbers.is_valid_number(parsed):
        raise InvalidPhoneNumber(f"{raw_phone!r} is not a valid phone number")
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


def start_login(phone):
    """
    Create a LoginOTP for `phone`. If no SMS provider is configured
    (OTP_PROVIDER_ENABLED=False, the v1 default), auto-verify immediately —
    this is the login failover behavior from SPEC.md section 3.
    """
    fallback = not settings.OTP_PROVIDER_ENABLED
    otp = LoginOTP.issue(phone, settings.OTP_CODE_TTL_SECONDS, fallback_used=fallback)
    if not fallback:
        send_sms(phone, f"Your BabyCal login code is {otp.code}")
    else:
        logger.info("OTP fallback (no provider configured): auto-verified login for %s", phone)
    return otp
