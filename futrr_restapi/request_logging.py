import logging
import time

logger = logging.getLogger("futrr.api")

CATEGORY_MAP = [
    ("/api/users/", "auth"),
    ("/api/auth/", "auth"),
    ("/api/token/", "auth"),
    ("/api/capsules/", "capsules"),
    ("/api/events/", "events"),
    ("/api/discover/", "discover"),
    ("/api/notifications/", "notifications"),
]


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == "/api/health/":
            return self.get_response(request)

        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)

        category = "other"
        for prefix, cat in CATEGORY_MAP:
            if request.path.startswith(prefix):
                category = cat
                break

        user_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = str(request.user.id)

        level = logging.WARNING if response.status_code >= 400 else logging.INFO

        logger.log(level, "request", extra={
            "category": category,
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "ip": request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")),
        })

        return response
