from dbm import error
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.permissions import IsHOD
from core.models import Appraisal, ApprovalHistory, Department
from workflow.engine import perform_action
from workflow.states import States
from scoring.engine import calculate_full_score
from validation.master_validator import validate_full_form
from django.db import transaction
from api.serializers import AppraisalSerializer
from core.models import FacultyProfile, Appraisal, AppraisalScore, User


class HODSubmitAPI(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    @transaction.atomic
    def post(self, request):
        user = request.user

        # 1️⃣ HOD must have FacultyProfile
        try:
            faculty = FacultyProfile.objects.select_related("department").get(user=user)
        except FacultyProfile.DoesNotExist:
            return Response(
                {"error": "Faculty profile not found for HOD"},
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
# 2️⃣ VALIDATION
        ok, err = validate_full_form(payload, meta)
        if not ok:
            return Response({"error": err}, status=400)

        # 3️⃣ DUPLICATE CHECK
        if Appraisal.objects.filter(
            faculty=faculty,
            academic_year=meta["academic_year"],
            semester=meta["semester"],
            form_type=meta["form_type"]
        ).exists():
            return Response(
                {"error": "Appraisal already exists for this period"},
                status=400
            )

        # 4️⃣ SCORING
        score_result = calculate_full_score(payload)

        # 5️⃣ CREATE APPRAISAL (MARK AS HOD)
        appraisal = Appraisal.objects.create(
            faculty=faculty,
            form_type=meta["form_type"],
            academic_year=meta["academic_year"],
            semester=meta["semester"],
            appraisal_data=payload,
            status=States.DRAFT,
            is_hod_appraisal=True,
            principal=User.objects.filter(role="PRINCIPAL").first()
        )

        # 6️⃣ WORKFLOW → SUBMIT
        appraisal.status = perform_action(
            current_state=appraisal.status,
            next_state=States.SUBMITTED,
            appraisal=appraisal
        )
        appraisal.save()

        # 7️⃣ CREATE SCORE
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
                "message": "HOD appraisal submitted successfully",
                "appraisal_id": appraisal.appraisal_id,
                "current_state": appraisal.status,
                "total_score": score_result["total_score"]
            },
            status=201
        )
    


class HODAppraisalListAPI(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    def get(self, request):
        faculty = FacultyProfile.objects.get(user=request.user)

        appraisals = Appraisal.objects.filter(
            faculty=faculty,
            is_hod_appraisal=True
        ).order_by("-updated_at")

        # 🚫 HOD cannot act on own appraisal
        if Appraisal.is_hod_appraisal:
            return Response(
                {"error": "HOD cannot review own appraisal"},
                status=403
        )

        return Response(
            AppraisalSerializer(appraisals, many=True).data
        )


class HODResubmitAPI(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    def post(self, request, appraisal_id):
        faculty = FacultyProfile.objects.get(user=request.user)

        appraisal = Appraisal.objects.get(
            appraisal_id=appraisal_id,
            faculty=faculty,
            is_hod_appraisal=True
        )

        if appraisal.status != States.DRAFT:
            return Response(
                {"error": "Only draft appraisals can be resubmitted"},
                status=400
            )

        appraisal.appraisal_data = request.data["appraisal_data"]
        appraisal.status = perform_action(
            current_state=appraisal.status,
            next_state=States.SUBMITTED
        )
        appraisal.save()

        return Response({"message": "HOD appraisal resubmitted"})
    

# =========================
# START HOD REVIEW
# =========================
class HODStartReviewAppraisal(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    def post(self, request, appraisal_id):
        # 1️⃣ Fetch appraisal
        
        try:
            appraisal = Appraisal.objects.select_related(
                "faculty__department"
            ).get(appraisal_id=appraisal_id)
            
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        # 2️⃣ Fetch HOD department
        try:
            department = Department.objects.get(hod=request.user)
        except Department.DoesNotExist:
            return Response(
                {"error": "HOD is not assigned to any department"},
                status=400
            )
        if appraisal.is_hod_appraisal:
                return Response(
                    {"error": "HOD cannot review own appraisal"},
                status=403
                )
        
        # 3️⃣ Ownership check
        if appraisal.faculty.department != department:
            return Response(
                {"error": "You cannot review appraisals outside your department"},
                status=403
            )

        # 4️⃣ Workflow transition
        try:
            new_state = perform_action(
                current_state=appraisal.status,
                next_state=States.REVIEWED_BY_HOD
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

        # 5️⃣ Save
        appraisal.status = new_state
  
        appraisal.save()

        
        return Response({
            "message": "Appraisal moved to HOD review",
            "current_state": new_state
        })


# =========================
# LIST FOR HOD
# =========================
class HODAppraisalList(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    def get(self, request):
        try:
            department = Department.objects.get(hod=request.user)
        except Department.DoesNotExist:
            return Response(
                {"error": "HOD is not assigned to any department"},
                status=400
            )

        appraisals = Appraisal.objects.filter(
            faculty__department=department,
            is_hod_appraisal=False,
            status__in=[States.SUBMITTED, States.REVIEWED_BY_HOD]
        )

        return Response([
            {
                "appraisal_id": a.appraisal_id,
                "faculty_id": a.faculty.faculty_id,
                "academic_year": a.academic_year,
                "semester": a.semester,
                "status": a.status,
            }
            for a in appraisals
        ])


# =========================
# HOD APPROVE
# =========================
class HODApproveAppraisal(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    def post(self, request, appraisal_id):
        try:
            appraisal = Appraisal.objects.select_related(
                "faculty__department"
            ).get(appraisal_id=appraisal_id)

            if appraisal.is_hod_appraisal:
                return Response(
                    {"error": "HOD cannot review own appraisal"},
                    status=403
                )
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        # 🔒 Department check
        try:
            department = Department.objects.get(hod=request.user)
        except Department.DoesNotExist:
            return Response(
                {"error": "HOD is not assigned to any department"},
                status=400
            )

        if appraisal.faculty.department != department:
            return Response(
                {"error": "You cannot act on appraisals outside your department"},
                status=403
            )

        # ❌ Invalid state
        if appraisal.status != States.REVIEWED_BY_HOD:
            return Response(
                {"error": "Appraisal not in HOD review state"},
                status=400
            )

        # ✅ Approve
        new_state = perform_action(
            current_state=appraisal.status,
            next_state=States.HOD_APPROVED
        )

        appraisal.status = new_state
        appraisal.save()

        ApprovalHistory.objects.update_or_create(
            appraisal=appraisal,
            role="HOD",
            defaults={
                "approved_by": request.user,
                "action": "APPROVED",
                "from_state": States.REVIEWED_BY_HOD,
                "to_state": new_state,
                "remarks": None
            }
        )

        return Response({
            "message": "Approved by HOD",
            "new_state": new_state
        })


# =========================
# HOD RETURN
# =========================
class HODReturnAppraisal(APIView):
    permission_classes = [IsAuthenticated, IsHOD]

    def post(self, request, appraisal_id):
        remarks = request.data.get("remarks", "")

        try:
            appraisal = Appraisal.objects.select_related(
                "faculty__department"
            ).get(appraisal_id=appraisal_id)
            if appraisal.is_hod_appraisal:
                return Response(
                    {"error": "HOD cannot review own appraisal"},
                status=403
                )
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        try:
            department = Department.objects.get(hod=request.user)
        except Department.DoesNotExist:
            return Response(
                {"error": "HOD is not assigned to any department"},
                status=400
            )

        if appraisal.faculty.department != department:
            return Response(
                {"error": "You cannot act on appraisals outside your department"},
                status=403
            )

        if appraisal.status != States.REVIEWED_BY_HOD:
            return Response(
                {"error": "Appraisal not in HOD review state"},
                status=400
            )


        
        new_state = perform_action(
            current_state=appraisal.status,
            next_state=States.DRAFT
        )

        appraisal.status = new_state

        appraisal.remarks = remarks
        appraisal.save()

        ApprovalHistory.objects.update_or_create(
            appraisal=appraisal,
            role="HOD",
            defaults={
                "approved_by": request.user,
                "action": "REJECTED",
                "from_state": States.REVIEWED_BY_HOD,
                "to_state": new_state,
                "remarks": None
            }
        )

        return Response({
            "message": "Returned to faculty",
            "new_state": new_state
        })


