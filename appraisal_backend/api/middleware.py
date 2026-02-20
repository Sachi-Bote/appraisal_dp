import logging
from time import perf_counter


logger = logging.getLogger("api.performance")


class APIPerformanceLoggingMiddleware:
    """
    Lightweight timing middleware for API endpoints.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        started = perf_counter()
        response = self.get_response(request)
        duration_ms = (perf_counter() - started) * 1000

        user = getattr(request, "user", None)
        user_id = getattr(user, "id", None) if getattr(user, "is_authenticated", False) else None
        role = getattr(user, "role", None) if getattr(user, "is_authenticated", False) else None

        logger.info(
            "api.request_timing method=%s path=%s status=%s duration_ms=%.2f user_id=%s role=%s",
            request.method,
            request.path,
            getattr(response, "status_code", "n/a"),
            duration_ms,
            user_id,
            role,
        )
        return response
