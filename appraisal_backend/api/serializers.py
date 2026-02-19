from django.db import transaction
from rest_framework import serializers

from core.models import (
    Appraisal,
    Department,
    FacultyProfile,
    HODProfile,
    PrincipalProfile,
    User,
)


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)

    role = serializers.ChoiceField(choices=["FACULTY", "HOD", "PRINCIPAL", "ADMIN"])
    department = serializers.CharField(required=False, allow_blank=True)

    full_name = serializers.CharField(required=True)
    designation = serializers.CharField(required=True)
    mobile = serializers.CharField(required=False, allow_blank=True)
    date_of_joining = serializers.DateField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True)
    gradePay = serializers.CharField(required=False, allow_blank=True)
    promotion_designation = serializers.CharField(required=False, allow_blank=True)
    eligibility_date = serializers.DateField(required=False, allow_null=True)
    assessment_period = serializers.DateField(required=False, allow_null=True)

    @transaction.atomic
    def create(self, validated_data):
        role = validated_data["role"]
        department_name = (validated_data.get("department") or "").strip()

        if role in ["FACULTY", "HOD"] and not department_name:
            raise serializers.ValidationError(
                {"department": "Department is required for this role"}
            )

        department = None
        if department_name and role not in ["PRINCIPAL", "ADMIN"]:
            department = Department.objects.filter(
                department_name__iexact=department_name
            ).first()
            if not department:
                raise serializers.ValidationError(
                    {
                        "department": (
                            f"Department '{department_name}' does not exist. "
                            "Use an existing department name configured by admin."
                        )
                    }
                )

        if role == "HOD" and HODProfile.objects.filter(department=department).exists():
            raise serializers.ValidationError(
                {"department": "This department already has an HOD"}
            )

        user = User.objects.create_user(
            username=validated_data["email"],
            password=validated_data["password"],
            role=role,
            department=department,
            full_name=validated_data["full_name"],
            designation=validated_data.get("designation"),
            date_of_joining=validated_data.get("date_of_joining"),
            email=validated_data["email"],
            mobile=validated_data.get("mobile"),
            must_change_password=True,
        )

        if role == "FACULTY":
            FacultyProfile.objects.create(
                user=user,
                full_name=validated_data["full_name"],
                designation=validated_data.get("designation"),
                department=department,
                date_of_joining=validated_data.get("date_of_joining"),
                mobile=validated_data.get("mobile"),
                email=validated_data["email"],
            )
        elif role == "HOD":
            FacultyProfile.objects.create(
                user=user,
                full_name=validated_data["full_name"],
                designation=validated_data.get("designation"),
                department=department,
                date_of_joining=validated_data.get("date_of_joining"),
                mobile=validated_data.get("mobile"),
                email=validated_data["email"],
            )
            HODProfile.objects.create(
                user=user,
                full_name=validated_data["full_name"],
                department=department,
                mobile=validated_data.get("mobile"),
                email=validated_data["email"],
            )
            department.hod = user
            department.save(update_fields=["hod"])
        elif role == "PRINCIPAL":
            PrincipalProfile.objects.create(
                user=user,
                full_name=validated_data["full_name"],
                mobile=validated_data.get("mobile"),
                email=validated_data["email"],
            )

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            user = User.objects.get(username=data["username"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid username or password")

        if not user.check_password(data["password"]):
            raise serializers.ValidationError("Invalid username or password")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")

        data["user"] = user
        return data


class AppraisalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appraisal
        fields = "__all__"
