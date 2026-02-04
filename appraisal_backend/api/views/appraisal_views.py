from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import Appraisal
from api.permissions import IsFaculty
from workflow.states import States


class CurrentFacultyAppraisalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        faculty = request.user.faculty_profile

        appraisal = (
            Appraisal.objects
            .filter(
                faculty=faculty,
                status="DRAFT"
            )
            .select_related("formdata", "score")
            .first()
        )

        if not appraisal:
            return Response({}, status=200)

        return Response({
            "status": appraisal.status,
            "form_payload": appraisal.formdata.form_payload,
            "scores": {
                "teaching_percentage": appraisal.score.teaching_percentage,
                "research_score": appraisal.score.research_score,
                "total_score": appraisal.score.total_score
            }
        })


class FacultyAppraisalStatusAPI(APIView):
    permission_classes = [IsAuthenticated, IsFaculty]

    def get(self, request):
        faculty = request.user.facultyprofile

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