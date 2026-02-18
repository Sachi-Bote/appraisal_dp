from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication


class PasswordChangeEnforcedJWTAuthentication(JWTAuthentication):
    ALLOWED_PATHS = {
        "/api/token/",
        "/api/token/refresh/",
        "/api/auth/login/",
        "/api/login/",
        "/api/logout/",
        "/api/auth/change-password/",
        "/api/me/",
    }

    def authenticate(self, request):
        result = super().authenticate(request)
        if not result:
            return None

        user, validated_token = result
        path = request.path

        if (
            getattr(user, "must_change_password", False)
            and path.startswith("/api/")
            and path not in self.ALLOWED_PATHS
        ):
            raise AuthenticationFailed("Password change required")

        return user, validated_token
