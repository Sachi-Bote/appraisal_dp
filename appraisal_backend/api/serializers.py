from rest_framework import serializers
from django.contrib.auth import authenticate
from core.models import HODProfile, PrincipalProfile, User, FacultyProfile
from core.models import Appraisal
from django.db import transaction
from rest_framework import serializers
from core.models import User, FacultyProfile, Department, HODProfile


class RegisterSerializer(serializers.Serializer):
    # 🔐 Auth fields
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    # 🔑 Role & scope
    role = serializers.ChoiceField(choices=["FACULTY", "HOD", "PRINCIPAL"])
    department = serializers.CharField(required=False)

    # 👤 Profile fields
    full_name = serializers.CharField()
    designation = serializers.CharField(required=False, allow_blank=True)
    mobile = serializers.CharField()
    date_of_joining = serializers.DateField(required=False)

    @transaction.atomic
    def create(self, validated_data):
        role = validated_data["role"]
        department_name = validated_data.get("department")

        if role in ["FACULTY", "HOD"] and not department_name:
            raise serializers.ValidationError({
                "department": "Department is required for this role"
            })

        if role == "PRINCIPAL" and department_name:
            raise serializers.ValidationError({
                "department": "Principal must not have a department"
            })

        department = None
        if department_name:
            try:
                department = Department.objects.get(
                    department_name__iexact=department_name.strip()
                )
            except Department.DoesNotExist:
                raise serializers.ValidationError({
                    "department": "Invalid department name"
                })

        if role == "HOD" and HODProfile.objects.filter(department=department).exists():
            raise serializers.ValidationError({
                "department": "This department already has an HOD"
            })

<<<<<<< HEAD
        # 1️⃣ CREATE USER
        user = User.objects.create_user(
=======
        # 👤 Create User (EMAIL IS IDENTITY)
        user = User(
>>>>>>> 50cd32651060fcb6fa1e32d653be53f75accc21d
            username=validated_data["email"],
            role=role
        )
        user.set_password(validated_data["password"])
        user.save()

        # 👥 Create role-specific profile
        if role == "FACULTY":
            FacultyProfile.objects.create(
                user=user,
                full_name=validated_data["full_name"],
                designation=validated_data.get("designation"),
                department=department,
                date_of_joining=validated_data.get("date_of_joining"),
                mobile=validated_data["mobile"],
                email=validated_data["email"]
            )

        elif role == "HOD":
            HODProfile.objects.create(
                user=user,
                full_name=validated_data["full_name"],
                department=department,
                mobile=validated_data["mobile"],
                email=validated_data["email"]
            )
            department.hod = user
            department.save()

        elif role == "PRINCIPAL":
            PrincipalProfile.objects.create(
                user=user,
                full_name=validated_data["full_name"],
                mobile=validated_data["mobile"],
                email=validated_data["email"]
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
