from rest_framework.views import APIView
from rest_framework.response import Response

from validation.master_validator import validate_full_form
from scoring.engine import calculate_full_score
from workflow.engine import perform_action

from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from core.models import User, FacultyProfile, Appraisal, AppraisalScore
from workflow.states import States
from api.permissions import IsRole


class FacultySubmitAPI(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        # 1️⃣ Get faculty profile
        try:
            faculty = FacultyProfile.objects.get(user=user)
        except FacultyProfile.DoesNotExist:
            return Response({"error": "Faculty profile not found"}, status=400)

        payload = request.data

        # 2️⃣ VALIDATION
        ok, err = validate_full_form(payload)
        if not ok:
            return Response({"error": err}, status=400)

        # 3️⃣ SCORING
        score_result = calculate_full_score(payload)

        # 4️⃣ WORKFLOW (Faculty submit)
        new_state = perform_action(
            role="faculty",
            action="submit",
            current_state = States.DRAFT
        )

        # 5️⃣ CREATE APPRAISAL
        appraisal = Appraisal.objects.create(
            faculty=faculty,
            form_type=payload["general"]["form_type"],
            academic_year=payload["general"]["academic_year"],
            semester=payload["general"]["semester"],
            appraisal_data=payload,
            status=new_state
        )

        # 6️⃣ CREATE APPRAISAL SCORE
        AppraisalScore.objects.create(
            appraisal=appraisal,
            teaching_score=score_result["teaching"]["score"],
            research_score=score_result["research"]["total"],
            activity_score=score_result["activities"]["score"],
            feedback_score=score_result["pbas"]["total"],
            total_score=score_result["total_score"]
        )

        return Response({
            "message": "Appraisal submitted successfully",
            "appraisal_id": appraisal.appraisal_id,
            "current_state": new_state,
            "total_score": score_result["total_score"]
        }, status=201)
