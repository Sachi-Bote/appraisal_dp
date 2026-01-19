from rest_framework.views import APIView
from rest_framework.response import Response

from workflow.engine import perform_action
from rest_framework.permissions import IsAuthenticated
from api.permissions import IsRole

class PrincipalApproveAPI(APIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ["PRINCIPAL"]

    def post(self, request):
        current = request.data["current_state"]
        action = request.data["action"]

        new_state = perform_action("principal", action, current)

        return Response({
            "message": "Principal action processed",
            "new_state": new_state
        })
