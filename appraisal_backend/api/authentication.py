import logging
from time import perf_counter

from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

logger = logging.getLogger("api.performance")


class PasswordChangeEnforcedJWTAuthentication(JWTAuthentication):
    ALLOWED_PATHS = {
        "/api/token/",
        "/api/token/refresh/",
        "/api/auth/login/",
        "/api/login/",
        "/api/logout/",
        "/api/auth/change-password/",
        "/api/auth/forgot-password/",
        "/api/auth/reset-password/",
        "/api/me/",
    }

    def authenticate(self, request):
        started = perf_counter()
        result = super().authenticate(request)
        if not result:
            logger.info(
                "auth.jwt_timing path=%s authenticated=false total_ms=%.2f",
                request.path,
                (perf_counter() - started) * 1000,
            )
            return None

        user, validated_token = result
        path = request.path

        if (
            getattr(user, "must_change_password", False)
            and path.startswith("/api/")
            and path not in self.ALLOWED_PATHS
        ):
            logger.info(
                "auth.jwt_timing path=%s user_id=%s role=%s blocked=must_change_password total_ms=%.2f",
                path,
                getattr(user, "id", None),
                getattr(user, "role", None),
                (perf_counter() - started) * 1000,
            )
            raise AuthenticationFailed("Password change required")

        logger.info(
            "auth.jwt_timing path=%s user_id=%s role=%s authenticated=true total_ms=%.2f",
            path,
            getattr(user, "id", None),
            getattr(user, "role", None),
            (perf_counter() - started) * 1000,
        )
        return user, validated_token
