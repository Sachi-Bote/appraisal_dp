from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response


from core.models import FacultyProfile, HODProfile, PrincipalProfile


class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        profile_data = {}
        date_of_joining = user.date_joined

        if user.role == "FACULTY":
            profile = FacultyProfile.objects.filter(user=user).first()
            if profile:
                date_of_joining = profile.date_of_joining or user.date_joined
                profile_data = {
                    "full_name": profile.full_name,
                    "designation": profile.designation,
                    "mobile_number": profile.mobile,
                }

        elif user.role == "HOD":
            profile = HODProfile.objects.filter(user=user).first()
            faculty_profile = FacultyProfile.objects.filter(user=user).first()
            if profile:
                date_of_joining = (
                    (faculty_profile.date_of_joining if faculty_profile else None)
                    or user.date_joined
                )
                profile_data = {
                    "full_name": profile.full_name,
                    "designation": "HOD",
                    "mobile_number": profile.mobile,
                }

        elif user.role == "PRINCIPAL":
            profile = PrincipalProfile.objects.filter(user=user).first()
            if profile:
                profile_data = {
                    "full_name": profile.full_name,
                    "designation": "Principal",
                    "mobile_number": profile.mobile,
                }

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.username,
            "role": user.role,
            "department": user.department,
            "date_joined": user.date_joined,
            "date_of_joining": date_of_joining,

            **profile_data
        })
    
    def patch(self, request):
        user = request.user

        if user.role == "FACULTY":
            profile = FacultyProfile.objects.get(user=user)
            profile.full_name = request.data.get("full_name", profile.full_name)
            profile.designation = request.data.get("designation", profile.designation)
            profile.mobile = request.data.get("mobile_number", profile.mobile)
            profile.save()

        return Response({"detail": "Profile updated"})
