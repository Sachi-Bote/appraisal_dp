from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction

from validation.master_validator import validate_full_form
from scoring.engine import calculate_full_score
from workflow.engine import perform_action
from api.permissions import IsFaculty
from workflow.states import States
from core.models import FacultyProfile, Appraisal, AppraisalScore


class FacultySubmitAPI(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    @transaction.atomic
    def post(self, request):
        user = request.user

        # 1️⃣ Faculty profile
        try:
            faculty = FacultyProfile.objects.select_related("department").get(user=user)
        except FacultyProfile.DoesNotExist:
            return Response({"error": "Faculty profile not found"}, status=400)

        if not faculty.department:
            return Response(
                {"error": "Faculty is not mapped to any department"},
                status=400
            )

        if not faculty.department.hod:
            return Response(
                {"error": "No HOD assigned to your department"},
                status=400
            )

        payload = request.data
        general = payload.get("general", {})
        
        # checking if the appraisal is already finalized
        if appraisal.status == States.FINALIZED:
            return Response({"error": "Finalized appraisal cannot be modified"},
        status=403
        )

        # 2️⃣ VALIDATION
        ok, err = validate_full_form(payload)
        if not ok:
            return Response({"error": err}, status=400)

        # 3️⃣ DUPLICATE CHECK
        if Appraisal.objects.filter(
            faculty=faculty,
            academic_year=general["academic_year"],
            semester=general["semester"],
            form_type=general["form_type"]
        ).exists():
            return Response(
                {"error": "Appraisal already exists for this period"},
                status=400
            )

        # 4️⃣ SCORING
        score_result = calculate_full_score(payload)

        # 5️⃣ CREATE APPRAISAL (INITIAL STATE = DRAFT)
        appraisal = Appraisal.objects.create(
            faculty=faculty,
            form_type=general["form_type"],
            academic_year=general["academic_year"],
            semester=general["semester"],
            appraisal_data=payload,
            status=States.DRAFT
        )

        # 6️⃣ WORKFLOW: FACULTY SUBMIT
        new_state = perform_action(
            role="faculty",
            action="submit",
            current_state=States.DRAFT
        )
        appraisal.status = new_state

        # 7️⃣ ASSIGN HOD
        appraisal.hod = faculty.department.hod
        appraisal.save()

        # 8️⃣ CREATE SCORE
        AppraisalScore.objects.create(
            appraisal=appraisal,
            teaching_score=score_result["teaching"]["score"],
            research_score=score_result["research"]["total"],
            activity_score=score_result["activities"]["score"],
            feedback_score=score_result["pbas"]["total"],
            total_score=score_result["total_score"]
        )

        return Response(
            {
                "message": "Appraisal submitted successfully",
                "appraisal_id": appraisal.appraisal_id,
                "current_state": appraisal.status,
                "total_score": score_result["total_score"]
            },
            status=201
        )
