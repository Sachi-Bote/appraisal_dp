from api.serializers import AppraisalSerializer
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

        meta = request.data
        payload = request.data.get("appraisal_data")

        if not payload:
            return Response(
                {"error": "appraisal_data is required"},
                status=400
            )

        def validate_full_form(payload, meta):
            general = payload.get("general", {})

            required_general_fields = [
                "faculty_name",
                "department",
                "designation"
            ]

            missing = [k for k in required_general_fields if k not in general]
            if missing:
                return False, f"Missing general fields: {missing}"

            required_meta_fields = [
                "academic_year",
                "semester",
                "form_type"
            ]

            missing_meta = [k for k in required_meta_fields if k not in meta]
            if missing_meta:
                return False, f"Missing meta fields: {missing_meta}"

            return True, None
        
        # checking if the appraisal is already finalized

        # 2️⃣ VALIDATION
        ok, err = validate_full_form(payload,meta)
        if not ok:
            return Response({"error": err}, status=400)

        # 3️⃣ DUPLICATE CHECK
        if Appraisal.objects.filter(
            faculty=faculty,
            academic_year = meta["academic_year"],
            semester = meta["semester"],
            form_type = meta["form_type"]
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
            form_type=meta["form_type"],
            academic_year=meta["academic_year"],
            semester=meta["semester"],
            appraisal_data=payload,
            status=States.DRAFT,
            is_hod_appraisal = False
        )

        # 6️⃣ WORKFLOW: FACULTY SUBMIT
        new_state = perform_action(
            current_state=appraisal.status,
            next_state=States.SUBMITTED
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


class FacultyAppraisalListAPI(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def get(self, request):
        faculty = FacultyProfile.objects.get(user=request.user)

        appraisals = Appraisal.objects.filter(
            faculty=faculty
        ).order_by("-updated_at")

        serializer = AppraisalSerializer(appraisals, many=True)

        return Response(serializer.data)
    
class FacultyResubmitAPI(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def post(self, request, appraisal_id):
        faculty = FacultyProfile.objects.get(user=request.user)

        appraisal = Appraisal.objects.get(
            appraisal_id=appraisal_id,
            faculty=faculty
        )

        if appraisal.status != States.DRAFT:
            return Response(
                {"error": "Only draft appraisals can be resubmitted"},
                status=400
            )

        # update data
        appraisal.appraisal_data = request.data["appraisal_data"]

        # workflow
        appraisal.status = perform_action(
            current_state=appraisal.status,
            next_state=States.SUBMITTED
        )

        appraisal.save()

        return Response({"message": "Appraisal resubmitted"})
