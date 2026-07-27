import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email(to, subject, body):
    """Thin wrapper over Django's SMTP backend for parent claim notifications."""
    if not to:
        logger.info("send_email() skipped: no recipient(s) for subject=%r", subject)
        return
    recipients = [to] if isinstance(to, str) else list(to)
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipients,
        fail_silently=True,
    )
