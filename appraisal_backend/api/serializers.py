from rest_framework import serializers
from core.models import User, FacultyProfile

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            role='FACULTY'  # force role for safety
        )
        user.set_password(validated_data['password'])
        user.save()

        # Auto-create faculty profile
        FacultyProfile.objects.create(user=user)

        return user
