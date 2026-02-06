from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import Appraisal
from api.permissions import IsFaculty, IsHOD
from workflow.states import States


class CurrentFacultyAppraisalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        faculty = getattr(request.user, 'faculty_profile', None) or getattr(request.user, 'facultyprofile', None)
        
        if not faculty:
            return Response({"error": "Faculty profile not found"}, status=400)

        is_hod = request.query_params.get("is_hod") == "true"

        from django.db.models import Case, When, Value, IntegerField
        
        appraisal = (
            Appraisal.objects
            .filter(
                faculty=faculty,
                status__in=[
                    States.DRAFT,
                    States.RETURNED_BY_HOD,
                    States.RETURNED_BY_PRINCIPAL,
                ],
                is_hod_appraisal=is_hod
            )
            .order_by(
                Case(
                    When(status=States.RETURNED_BY_HOD, then=Value(0)),
                    When(status=States.RETURNED_BY_PRINCIPAL, then=Value(1)),
                    When(status=States.DRAFT, then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField()
                ),
                '-updated_at'
            )
            .first()
        )

        if not appraisal:
            return Response({}, status=200)

        data = {
            "id": appraisal.appraisal_id,
            "status": appraisal.status,
            "academic_year": appraisal.academic_year,
            "semester": appraisal.semester,
            "form_type": appraisal.form_type,
            "appraisal_data": appraisal.appraisal_data,
            "remarks": appraisal.remarks
        }
        return Response(data)


class FacultyAppraisalStatusAPI(APIView):
    permission_classes = [IsAuthenticated, IsFaculty | IsHOD]

    def get(self, request):
        try:
            faculty = request.user.facultyprofile
        except:
             # Fallback for HOD who might not have a facultyprofile named exactly like that
             # though FacultyProfile objects usually use faculty_profile related_name
             faculty = getattr(request.user, 'facultyprofile', None) or getattr(request.user, 'faculty_profile', None)
             
        if not faculty:
            return Response({"error": "Faculty profile not found"}, status=404)

        appraisals = Appraisal.objects.filter(
            faculty=faculty
        ).order_by("-updated_at")

        under_review = []
        approved = []
        changes_requested = []

        for a in appraisals:
            base_data = {
                "id": a.appraisal_id,
                "academic_year": a.academic_year,
                "submitted_date": a.created_at.strftime("%d %b %Y"),
                "remarks": a.remarks,
            }

            # 🔁 UNDER REVIEW STATES
            if a.status in [
                States.SUBMITTED,
                States.REVIEWED_BY_HOD,
                States.HOD_APPROVED,
                States.REVIEWED_BY_PRINCIPAL,
            ]:
                under_review.append({
                    **base_data,
                    "current_level": self._current_level(a.status),
                    "status": "Under Review",
                })

            # 🔴 RETURNED
            elif a.status in [
                States.RETURNED_BY_HOD,
                States.RETURNED_BY_PRINCIPAL,
            ]:
                changes_requested.append({
                    **base_data,
                    "current_level": self._current_level(a.status),
                    "status": "Changes Requested",
                })

            # 🟢 APPROVED
            elif a.status in [
                States.PRINCIPAL_APPROVED,
                States.FINALIZED,
            ]:
                approved.append({
                    **base_data,
                    "current_level": "Completed",
                    "status": "Approved",
                })

        return Response({
            "under_review": under_review,
            "approved": approved,
            "changes_requested": changes_requested,
        })

    def _current_level(self, state):
        if state in [States.SUBMITTED, States.REVIEWED_BY_HOD]:
            return "HOD"
        if state in [States.HOD_APPROVED, States.REVIEWED_BY_PRINCIPAL]:
            return "Principal"
        return "—"


class AppraisalDetailAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, appraisal_id):
        try:
            appraisal = Appraisal.objects.select_related("faculty__department").get(appraisal_id=appraisal_id)
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        # Basic permission check
        is_owner = appraisal.faculty.user == request.user
        is_principal = request.user.role == "PRINCIPAL"
        
        is_hod = False
        if request.user.role == "HOD":
            from core.models import Department
            try:
                dept = Department.objects.get(hod=request.user)
                if appraisal.faculty.department == dept:
                    is_hod = True
            except Department.DoesNotExist:
                pass

        if not (is_owner or is_principal or is_hod):
            return Response({"error": "Unauthorized access"}, status=403)

        return Response({
            "id": appraisal.appraisal_id,
            "status": appraisal.status,
            "academic_year": appraisal.academic_year,
            "semester": appraisal.semester,
            "appraisal_data": appraisal.appraisal_data,
            "remarks": appraisal.remarks,
            "faculty": {
                "name": appraisal.faculty.full_name,
                "department": appraisal.faculty.department.department_name,
                "designation": appraisal.faculty.designation
            }
        })
