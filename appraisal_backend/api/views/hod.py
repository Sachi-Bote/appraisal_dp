from rest_framework.views import APIView
from rest_framework.response import Response

from workflow.engine import perform_action


class HODReviewAPI(APIView):
    def post(self, request):
        current = request.data["current_state"]
        action = request.data["action"]

        new_state = perform_action("hod", action, current)

        return Response({
            "message": "HOD action processed",
            "new_state": new_state
        })
