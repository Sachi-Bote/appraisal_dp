from rest_framework.views import APIView
from rest_framework.response import Response

from validation.master_validator import validate_full_form
from scoring.engine import calculate_full_score
from workflow.engine import perform_action


class FacultySubmitAPI(APIView):
    def post(self, request):
        payload = request.data

        # 1. VALIDATION
        ok, err = validate_full_form(payload)
        if not ok:
            return Response({"error": err}, status=400)

        # 2. SCORING
        score_result = calculate_full_score(payload)

        # 3. WORKFLOW
        new_state = perform_action(
            role=payload["role"],
            action=payload["submit_action"],
            current_state="draft"
        )

        return Response({
            "message": "Form submitted successfully",
            "state": new_state,
            "score": score_result["total_score"],
            "score_details": score_result
        })
from rest_framework.permissions import IsAuthenticated
from api.permissions import IsRole

class FacultySubmitAPI(APIView):
    permission_classes = [IsAuthenticated, IsRole]
    allowed_roles = ["FACULTY", "HOD"]  # HOD can submit own form

    def post(self, request):
        payload = request.data

        # validation
        ok, err = validate_full_form(payload)
        if not ok:
            return Response({"error": err}, status=400)

        score = calculate_full_score(payload)

        new_state = perform_action(
            role=request.user.role.lower(),
            action=payload["submit_action"],
            current_state=payload["current_state"]
        )

        return Response({
            "message": "Form submitted",
            "state": new_state,
            "score": score["total_score"]
        })
