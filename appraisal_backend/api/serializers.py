from rest_framework import serializers
from django.contrib.auth import authenticate
from core.models import HODProfile, PrincipalProfile, User, FacultyProfile
from core.models import Appraisal

from rest_framework import serializers
from core.models import User, FacultyProfile, Department


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    department = serializers.CharField(required=False, write_only=True)

    class Meta:
        model = User
        fields = ("username", "password", "role", "department")

    def create(self, validated_data):
        password = validated_data.pop("password")
        role = validated_data.get("role")
        department_name = validated_data.pop("department", None)

        # ✅ Create user first
        user = User(
            username=validated_data["username"],
            role=role
        )
        user.set_password(password)
        user.save()

        # ✅ Create FacultyProfile ONLY for faculty
        if role == "FACULTY":
            if not department_name:
                raise serializers.ValidationError(
                    {"department": "Department is required for faculty"}
                )

            department = Department.objects.get(
                department_name=department_name
            )

            FacultyProfile.objects.create(
                user=user,
                department=department
            )

        elif role == "HOD":
            if not department_name:
                raise serializers.ValidationError(
                    {"department": "Department is required for HOD"}
                )

            department = Department.objects.get(
                department_name=department_name
            )

            HODProfile.objects.create(
                user=user,
                department=department
            )
        
        elif role == "PRINCIPAL":
            if department_name:
                raise serializers.ValidationError(
                    {"department": "Department is not required for principal"}
                )

            PrincipalProfile.objects.create(
                user=user
            )

        # 🚫 HOD / PRINCIPAL must NOT get FacultyProfile
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
