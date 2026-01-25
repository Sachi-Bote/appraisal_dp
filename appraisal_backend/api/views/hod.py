from dbm import error
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.permissions import IsHOD
from core.models import Appraisal, ApprovalHistory, Department
from workflow.engine import perform_action
from workflow.states import States


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

        # 3️⃣ Ownership check
        if appraisal.faculty.department != department:
            return Response(
                {"error": "You cannot review appraisals outside your department"},
                status=403
            )
        
        if appraisal.status == States.FINALIZED:
            return Response({"error": "Finalized appraisal cannot be modified"},
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
        appraisal.hod = request.user
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

        if appraisal.status == States.FINALIZED:
            return Response({"error": "Finalized appraisal cannot be modified"},
            status=403
        )
        # ✅ Approve
        new_state = perform_action(
            current_state=appraisal.status,
            next_state=States.HOD_APPROVED
        )

        appraisal.status = new_state
        appraisal.hod = request.user
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

        if appraisal.status == States.FINALIZED:
            return Response({"error": "Finalized appraisal cannot be modified"},
            status=403
        )

        
        new_state = perform_action(
            current_state=appraisal.status,
            next_state=States.DRAFT
        )

        appraisal.status = new_state
        appraisal.hod = request.user
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
