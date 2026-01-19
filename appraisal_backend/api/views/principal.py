from rest_framework.views import APIView
from rest_framework.response import Response

from workflow.engine import perform_action


class PrincipalApproveAPI(APIView):
    def post(self, request):
        current = request.data["current_state"]
        action = request.data["action"]

        new_state = perform_action("principal", action, current)

        return Response({
            "message": "Principal action processed",
            "new_state": new_state
        })
