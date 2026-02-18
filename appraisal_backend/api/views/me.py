from datetime import date

from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser


from core.models import FacultyProfile, HODProfile, PrincipalProfile


def _parse_optional_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


class MeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        user = request.user

        profile_data = {
            "full_name": user.full_name,
            "designation": user.designation,
            "mobile_number": user.mobile_number,
        }
        date_of_joining = user.date_joined
        profile_image = None

        if user.role == "FACULTY":
            profile = FacultyProfile.objects.filter(user=user).first()
            if profile:
                date_of_joining = profile.date_of_joining or user.date_joined
                profile_image = request.build_absolute_uri(profile.profile_image.url) if profile.profile_image else None
                profile_data = {
                    "full_name": profile.full_name or user.full_name,
                    "designation": profile.designation or user.designation,
                    "email": profile.email or user.email or user.username,
                    "mobile_number": profile.mobile or user.mobile_number,
                    "profile_image": profile_image,
                }

        elif user.role == "HOD":
            profile = HODProfile.objects.filter(user=user).first()
            faculty_profile = FacultyProfile.objects.filter(user=user).first()
            if profile:
                date_of_joining = (
                    (faculty_profile.date_of_joining if faculty_profile else None)
                    or user.date_joined
                )
                profile_image = request.build_absolute_uri(profile.profile_image.url) if profile.profile_image else None
                profile_data = {
                    "full_name": profile.full_name or user.full_name,
                    "designation": user.designation or "HOD",
                    "email": profile.email or user.email or user.username,
                    "mobile_number": profile.mobile or user.mobile_number,
                    "profile_image": profile_image,
                }

        elif user.role == "PRINCIPAL":
            profile = PrincipalProfile.objects.filter(user=user).first()
            if profile:
                profile_data = {
                    "full_name": profile.full_name or user.full_name,
                    "designation": user.designation or "Principal",
                    "email": profile.email or user.email or user.username,
                    "mobile_number": profile.mobile or user.mobile_number,
                }

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email or user.username,
            "role": user.role,
            "must_change_password": user.must_change_password,
            "department": user.department,
            "date_joined": user.date_joined,
            "date_of_joining": date_of_joining,
            "address": user.address,
            "gradePay": user.gradePay,
            "promotion_designation": user.promotion_designation,
            "eligibility_date": user.eligibility_date,
            "assessment_period": user.assessment_period,

            **profile_data
        })
    
    def patch(self, request):
        user = request.user

        profile = None
        if user.role == "FACULTY":
            profile, _ = FacultyProfile.objects.get_or_create(user=user)
        elif user.role == "HOD":
            profile = HODProfile.objects.filter(user=user).first()
            if profile is None:
                return Response({"detail": "HOD profile not found"}, status=400)
        elif user.role == "PRINCIPAL":
            profile, _ = PrincipalProfile.objects.get_or_create(
                user=user,
                defaults={"full_name": user.full_name or user.username},
            )

        full_name = request.data.get("full_name")
        mobile_number = request.data.get("mobile_number")
        email = request.data.get("email")
        designation = request.data.get("designation")
        address = request.data.get("address")
        grade_pay = request.data.get("gradePay")
        promotion_designation = request.data.get("promotion_designation")
        eligibility_date = _parse_optional_date(request.data.get("eligibility_date"))
        assessment_period = _parse_optional_date(request.data.get("assessment_period"))
        date_of_joining = _parse_optional_date(request.data.get("date_of_joining"))

        if profile is not None:
            if full_name is not None:
                profile.full_name = full_name
            if mobile_number is not None:
                profile.mobile = mobile_number
            if email is not None and hasattr(profile, "email"):
                profile.email = email

            remove_image = str(request.data.get("remove_profile_image", "")).lower() in {"1", "true", "yes"}
            if remove_image and getattr(profile, "profile_image", None):
                profile.profile_image.delete(save=False)
                profile.profile_image = None

            uploaded_image = request.FILES.get("profile_image")
            if uploaded_image:
                profile.profile_image = uploaded_image

            if user.role == "FACULTY":
                if designation is not None:
                    profile.designation = designation
                if date_of_joining is not None:
                    profile.date_of_joining = date_of_joining

            profile.save()

        user_fields_to_update = []
        if full_name is not None and user.full_name != full_name:
            user.full_name = full_name
            user_fields_to_update.append("full_name")
        if mobile_number is not None and user.mobile_number != mobile_number:
            user.mobile_number = mobile_number
            user_fields_to_update.append("mobile_number")
        if email is not None and user.email != email:
            user.email = email
            user_fields_to_update.append("email")
        if designation is not None and user.designation != designation:
            user.designation = designation
            user_fields_to_update.append("designation")
        if address is not None and user.address != address:
            user.address = address
            user_fields_to_update.append("address")
        if grade_pay is not None and user.gradePay != grade_pay:
            user.gradePay = grade_pay
            user_fields_to_update.append("gradePay")
        if promotion_designation is not None and user.promotion_designation != promotion_designation:
            user.promotion_designation = promotion_designation
            user_fields_to_update.append("promotion_designation")
        if request.data.get("eligibility_date") is not None and user.eligibility_date != eligibility_date:
            user.eligibility_date = eligibility_date
            user_fields_to_update.append("eligibility_date")
        if request.data.get("assessment_period") is not None and user.assessment_period != assessment_period:
            user.assessment_period = assessment_period
            user_fields_to_update.append("assessment_period")
        if user_fields_to_update:
            user.save(update_fields=user_fields_to_update)

        # Keep the auto-created faculty profile in sync for HOD users.
        if user.role == "HOD":
            faculty_profile, _ = FacultyProfile.objects.get_or_create(user=user)
            profile_fields_to_update = []
            if full_name is not None and faculty_profile.full_name != full_name:
                faculty_profile.full_name = full_name
                profile_fields_to_update.append("full_name")
            if mobile_number is not None and faculty_profile.mobile != mobile_number:
                faculty_profile.mobile = mobile_number
                profile_fields_to_update.append("mobile")
            if email is not None and faculty_profile.email != email:
                faculty_profile.email = email
                profile_fields_to_update.append("email")
            if designation is not None and faculty_profile.designation != designation:
                faculty_profile.designation = designation
                profile_fields_to_update.append("designation")
            if request.data.get("date_of_joining") is not None and faculty_profile.date_of_joining != date_of_joining:
                faculty_profile.date_of_joining = date_of_joining
                profile_fields_to_update.append("date_of_joining")
            if profile_fields_to_update:
                faculty_profile.save(update_fields=profile_fields_to_update)

        return Response({"detail": "Profile updated"})
