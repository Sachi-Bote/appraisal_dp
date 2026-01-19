from rest_framework.views import APIView
from rest_framework.response import Response

from workflow.engine import perform_action


class WorkflowAPI(APIView):
    def post(self, request):
        role = request.data["role"]
        action = request.data["action"]
        current_state = request.data["current_state"]

        new_state = perform_action(role, action, current_state)

        return Response({"new_state": new_state})
