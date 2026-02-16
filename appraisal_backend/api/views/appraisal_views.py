from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import Appraisal
from api.permissions import IsFaculty, IsHOD
from workflow.states import States
from django.http import FileResponse
from core.models import GeneratedPDF
import os
from core.services.sppu_verified import extract_verified_grading, TABLE2_VERIFIED_KEYS
from core.services.pdf.enhanced_sppu_mapper import get_enhanced_sppu_pdf_data


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
        except Exception:
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
                "workflow_state": a.status,
            }

            # UNDER REVIEW STATES
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

            # RETURNED
            elif a.status in [
                States.RETURNED_BY_HOD,
                States.RETURNED_BY_PRINCIPAL,
            ]:
                changes_requested.append({
                    **base_data,
                    "current_level": self._current_level(a.status),
                    "status": "Changes Requested",
                })

            # APPROVED
            elif a.status in [
                States.PRINCIPAL_APPROVED,
                States.FINALIZED,
            ]:
                base_download_url = f"/api/appraisal/{a.appraisal_id}"
                approved.append({
                    **base_data,
                    "current_level": "Completed",
                    "status": "Approved",
                    "download_available": True,
                    "download_urls": {
                        "sppu": f"{base_download_url}/pdf/sppu-enhanced/",
                        "pbas": f"{base_download_url}/pdf/pbas-enhanced/",
                    },
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
        return "-"


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

        verified_grade = None
        if hasattr(appraisal, 'appraisalscore'):
            verified_grade = appraisal.appraisalscore.verified_grade
        verified_grading = extract_verified_grading(
            appraisal.appraisal_data,
            appraisal.is_hod_appraisal is True,
        )
        sppu_review_data = None
        try:
            sppu_data = get_enhanced_sppu_pdf_data(appraisal)
            sppu_review_data = {
                "table1_teaching": sppu_data.get("table1_teaching", {}),
                "table1_activities": sppu_data.get("table1_activities", {}),
                "table2_research": sppu_data.get("table2_research", {}),
                "table2_total_score": sppu_data.get("table2_total_score", 0),
            }
        except Exception:
            sppu_review_data = None

        can_verify_grade = False
        verifier_role = None
        if is_hod and (not appraisal.is_hod_appraisal) and appraisal.status == States.REVIEWED_BY_HOD:
            can_verify_grade = True
            verifier_role = "HOD"
        elif is_principal and appraisal.is_hod_appraisal and appraisal.status == States.REVIEWED_BY_PRINCIPAL:
            can_verify_grade = True
            verifier_role = "PRINCIPAL"

        return Response({
            "id": appraisal.appraisal_id,
            "status": appraisal.status,
            "academic_year": appraisal.academic_year,
            "semester": appraisal.semester,
            "appraisal_data": appraisal.appraisal_data,
            "remarks": appraisal.remarks,
            "verified_grade": verified_grade,
            "verified_grading": verified_grading,
            "sppu_review_data": sppu_review_data,
            "can_verify_grade": can_verify_grade,
            "verifier_role": verifier_role,
            "verified_grade_options": ["Good", "Satisfactory", "Not Satisfactory"],
            "table2_verified_keys": TABLE2_VERIFIED_KEYS,
            "faculty": {
                "name": appraisal.faculty.full_name,
                "department": appraisal.faculty.department.department_name,
                "designation": appraisal.faculty.designation
            }
        })


class DownloadAppraisalPDF(APIView):
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _ensure_finalized_pdfs(appraisal):
        if appraisal.status not in [States.PRINCIPAL_APPROVED, States.FINALIZED]:
            return

        has_sppu = GeneratedPDF.objects.filter(
            appraisal=appraisal,
            pdf_path__icontains="SPPU_PBAS_appraisal_"
        ).exists()
        has_pbas = GeneratedPDF.objects.filter(
            appraisal=appraisal,
            pdf_path__icontains="AICTE_PBAS_appraisal_"
        ).exists()

        if not has_sppu:
            from core.services.pdf.sppu_mapper import get_sppu_pdf_data
            from core.services.pdf.html_pdf import generate_pdf_from_html
            from core.services.pdf.save import save_pdf
            sppu_data = get_sppu_pdf_data(appraisal)
            sppu_pdf = generate_pdf_from_html("pdf/sppu_pbas_form.html", sppu_data)
            save_pdf(appraisal, sppu_pdf, "SPPU_PBAS")

        if not has_pbas:
            from core.services.pdf.pbas_mapper import get_pbas_pdf_data
            from core.services.pdf.html_pdf import generate_pdf_from_html
            from core.services.pdf.save import save_pdf
            pbas_data = get_pbas_pdf_data(appraisal)
            pbas_pdf = generate_pdf_from_html("pdf/aicte_pbas_form.html", pbas_data)
            save_pdf(appraisal, pbas_pdf, "AICTE_PBAS")

    def get(self, request, appraisal_id):
        try:
            appraisal = Appraisal.objects.get(appraisal_id=appraisal_id)
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        is_owner = appraisal.faculty.user == request.user
        is_principal = request.user.role == "PRINCIPAL"

        is_hod = False
        if request.user.role == "HOD":
            # Simple check if HOD manages this faculty's department
            if request.user.department_set.filter(pk=appraisal.faculty.department.pk).exists():
                is_hod = True

        if not (is_owner or is_principal or is_hod):
            return Response({"error": "Unauthorized"}, status=403)

        # Default keeps old behavior (SPPU). Caller can request ?pdf_type=PBAS.
        requested_type = (request.query_params.get("pdf_type") or "SPPU").upper()
        pattern = "AICTE_PBAS" if requested_type == "PBAS" else "SPPU_PBAS"

        # Ensure finalized/principal-approved appraisals are downloadable.
        self._ensure_finalized_pdfs(appraisal)

        try:
            pdf_record = GeneratedPDF.objects.filter(
                appraisal=appraisal,
                pdf_path__icontains=pattern
            ).latest("generated_at")

            if not os.path.exists(pdf_record.pdf_path):
                # Retry once for completed appraisals if file is missing.
                self._ensure_finalized_pdfs(appraisal)
                pdf_record = GeneratedPDF.objects.filter(
                    appraisal=appraisal,
                    pdf_path__icontains=pattern
                ).latest("generated_at")
                if not os.path.exists(pdf_record.pdf_path):
                    return Response({"error": "PDF file not found on server"}, status=404)

            return FileResponse(open(pdf_record.pdf_path, "rb"), content_type="application/pdf")
        except GeneratedPDF.DoesNotExist:
            # Backward-compatible fallback to any generated PDF.
            try:
                self._ensure_finalized_pdfs(appraisal)
                pdf_record = GeneratedPDF.objects.filter(appraisal=appraisal).latest("generated_at")
                return FileResponse(open(pdf_record.pdf_path, "rb"), content_type="application/pdf")
            except GeneratedPDF.DoesNotExist:
                return Response({"error": "PDF not generated yet"}, status=404)
