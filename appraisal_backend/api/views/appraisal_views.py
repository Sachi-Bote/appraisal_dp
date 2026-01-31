from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import Appraisal


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
