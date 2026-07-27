import logging
import time

logger = logging.getLogger("babycal.request")


class RequestLoggingMiddleware:
    """Logs one line per request: method, path, status, duration, and who (if anyone) is logged in."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        user = getattr(request, "user", None)
        who = user.phone if getattr(user, "is_authenticated", False) else "anon"

        logger.info(
            "%s %s -> %s (%.1fms) user=%s",
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
            who,
        )
        return response
