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
