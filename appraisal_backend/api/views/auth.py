import os

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from api.serializers import RegisterSerializer
from api.permissions import IsAdmin
from core.models import User


# =========================
# REGISTER
# =========================
class RegisterAPI(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "User account created successfully"},
            status=status.HTTP_201_CREATED
        )


# =========================
# LOGIN (JWT)
# =========================
class LoginSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Custom claims
        token["username"] = user.username
        token["role"] = user.role

        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # Expose profile-relevant fields so frontend can map them immediately after login.
        date_of_joining = None
        faculty_profile = getattr(user, "facultyprofile", None)
        if faculty_profile and faculty_profile.date_of_joining:
            date_of_joining = faculty_profile.date_of_joining
        else:
            date_of_joining = user.date_joined

        data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email or user.username,
            "role": user.role,
            "department": user.department,
            "date_of_joining": date_of_joining,
            "date_joined": user.date_joined,
            "must_change_password": user.must_change_password,
        }
        return data


class LoginAPI(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer


# =========================
# LOGOUT    
# =========================
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"detail": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"detail": "Logged out successfully"},
                status=status.HTTP_205_RESET_CONTENT
            )

        except Exception:
            return Response(
                {"detail": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class ChangePasswordAPI(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {"detail": "old_password and new_password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(old_password):
            return Response(
                {"detail": "Old password is incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])

        return Response({"detail": "Password changed successfully"}, status=status.HTTP_200_OK)


class ForgotPasswordRequestAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip()
        if not email:
            return Response(
                {"detail": "email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            user = User.objects.filter(username__iexact=email).first()

        debug_payload = {}
        if user and user.is_active:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            frontend_base_url = (
                os.getenv("FRONTEND_BASE_URL")
                or getattr(settings, "FRONTEND_BASE_URL", "")
                or "http://localhost:5173"
            )
            reset_link = f"{frontend_base_url.rstrip('/')}/reset-password?uid={uid}&token={token}"

            send_mail(
                subject="Password reset request",
                message=f"Use this link to reset your password: {reset_link}",
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
                recipient_list=[user.email or user.username],
                fail_silently=True,
            )

            if settings.DEBUG:
                debug_payload = {
                    "uid": uid,
                    "token": token,
                    "reset_link": reset_link,
                }

        response = {
            "detail": "If an account with this email exists, a reset link has been sent.",
        }
        if debug_payload:
            response["debug"] = debug_payload

        return Response(response, status=status.HTTP_200_OK)


class ResetPasswordConfirmAPI(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not uid or not token or not new_password:
            return Response(
                {"detail": "uid, token, and new_password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except Exception:
            return Response(
                {"detail": "Invalid or expired reset token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "Invalid or expired reset token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            return Response(
                {"detail": exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])

        return Response({"detail": "Password reset successfully"}, status=status.HTTP_200_OK)
