from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from api.serializers import UserRegistrationSerializer

class LoginAPI(APIView):
    def post(self, request):
        username = request.data.get("username")
        role = request.data.get("role", "faculty")

        return Response({
            "message": "Login successful",
            "access": "DUMMY_ACCESS_TOKEN",
            "refresh": "DUMMY_REFRESH_TOKEN",
            "username": username,
            "role": role
        })


class RegisterAPI(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)