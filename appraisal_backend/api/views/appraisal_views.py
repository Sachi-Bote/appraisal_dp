import logging
from time import perf_counter

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.models import Appraisal
from api.permissions import IsFaculty, IsHOD
from workflow.states import States
from core.services.sppu_verified import extract_verified_grading, TABLE2_VERIFIED_KEYS
from scoring.engine import calculate_full_score
from core.services.pdf.enhanced_sppu_mapper import get_enhanced_sppu_pdf_data
from scoring.activity_selection import get_activity_sections

logger = logging.getLogger("api.performance")


class CurrentFacultyAppraisalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        started = perf_counter()
        faculty = getattr(request.user, 'faculty_profile', None) or getattr(request.user, 'facultyprofile', None)

        if not faculty:
            logger.info(
                "faculty.current_appraisal_timing user_id=%s total_ms=%.2f note=no_faculty_profile",
                getattr(request.user, "id", None),
                (perf_counter() - started) * 1000,
            )
            return Response({"error": "Faculty profile not found"}, status=400)

        is_hod = request.query_params.get("is_hod") == "true"

        from django.db.models import Case, When, Value, IntegerField

        query_started = perf_counter()
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
        query_ms = (perf_counter() - query_started) * 1000

        if not appraisal:
            logger.info(
                "faculty.current_appraisal_timing user_id=%s query_ms=%.2f total_ms=%.2f found=false",
                getattr(request.user, "id", None),
                query_ms,
                (perf_counter() - started) * 1000,
            )
            return Response({}, status=200)

        payload_started = perf_counter()
        data = {
            "id": appraisal.appraisal_id,
            "status": appraisal.status,
            "academic_year": appraisal.academic_year,
            "semester": appraisal.semester,
            "form_type": appraisal.form_type,
            "appraisal_data": appraisal.appraisal_data,
            "remarks": appraisal.remarks,
            "activity_sections": get_activity_sections(),
        }
        payload_ms = (perf_counter() - payload_started) * 1000
        logger.info(
            "faculty.current_appraisal_timing user_id=%s appraisal_id=%s query_ms=%.2f payload_ms=%.2f total_ms=%.2f",
            getattr(request.user, "id", None),
            appraisal.appraisal_id,
            query_ms,
            payload_ms,
            (perf_counter() - started) * 1000,
        )
        return Response(data)


class FacultyAppraisalStatusAPI(APIView):
    permission_classes = [IsAuthenticated, IsFaculty | IsHOD]

    def get(self, request):
        started = perf_counter()
        try:
            faculty = request.user.facultyprofile
        except Exception:
            # Fallback for HOD who might not have a facultyprofile named exactly like that
            # though FacultyProfile objects usually use faculty_profile related_name
            faculty = getattr(request.user, 'facultyprofile', None) or getattr(request.user, 'faculty_profile', None)

        if not faculty:
            logger.info(
                "faculty.status_timing user_id=%s total_ms=%.2f note=no_faculty_profile",
                getattr(request.user, "id", None),
                (perf_counter() - started) * 1000,
            )
            return Response({"error": "Faculty profile not found"}, status=404)

        query_started = perf_counter()
        appraisals = (
            Appraisal.objects
            .filter(faculty=faculty)
            .only("appraisal_id", "academic_year", "created_at", "remarks", "status", "updated_at")
            .order_by("-updated_at")
        )
        query_ms = (perf_counter() - query_started) * 1000

        under_review = []
        approved = []
        changes_requested = []

        classify_started = perf_counter()
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
        classify_ms = (perf_counter() - classify_started) * 1000
        logger.info(
            "faculty.status_timing user_id=%s query_ms=%.2f classify_ms=%.2f total_ms=%.2f counts_under_review=%s counts_approved=%s counts_changes_requested=%s",
            getattr(request.user, "id", None),
            query_ms,
            classify_ms,
            (perf_counter() - started) * 1000,
            len(under_review),
            len(approved),
            len(changes_requested),
        )

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
        started = perf_counter()
        lookup_started = perf_counter()
        try:
            appraisal = Appraisal.objects.select_related("faculty__department").get(appraisal_id=appraisal_id)
        except Appraisal.DoesNotExist:
            logger.info(
                "faculty.detail_timing user_id=%s appraisal_id=%s lookup_ms=%.2f total_ms=%.2f found=false",
                getattr(request.user, "id", None),
                appraisal_id,
                (perf_counter() - lookup_started) * 1000,
                (perf_counter() - started) * 1000,
            )
            return Response({"error": "Appraisal not found"}, status=404)
        lookup_ms = (perf_counter() - lookup_started) * 1000

        # Basic permission check
        perm_started = perf_counter()
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
            logger.info(
                "faculty.detail_timing user_id=%s appraisal_id=%s lookup_ms=%.2f perm_ms=%.2f total_ms=%.2f authorized=false",
                getattr(request.user, "id", None),
                appraisal_id,
                lookup_ms,
                (perf_counter() - perm_started) * 1000,
                (perf_counter() - started) * 1000,
            )
            return Response({"error": "Unauthorized access"}, status=403)
        perm_ms = (perf_counter() - perm_started) * 1000

        include_heavy = request.query_params.get("include_heavy") == "true"

        verified_started = perf_counter()
        verified_grade = None
        appraisal_score = getattr(appraisal, "appraisalscore", None)
        if hasattr(appraisal, 'appraisalscore'):
            verified_grade = appraisal.appraisalscore.verified_grade
        verified_grading = extract_verified_grading(
            appraisal.appraisal_data,
            appraisal.is_hod_appraisal is True,
        )
        verified_ms = (perf_counter() - verified_started) * 1000
        # Provide pre-computed total score from DB by default to avoid expensive recalculation on routine page loads.
        score_started = perf_counter()
        if appraisal_score and appraisal_score.total_score is not None:
            calculated_total_score = float(appraisal_score.total_score)
        elif include_heavy:
            try:
                calculated = calculate_full_score(appraisal.appraisal_data)
                calculated_total_score = float(calculated.get("total_score", 0))
            except Exception:
                calculated_total_score = None
        else:
            calculated_total_score = None
        score_ms = (perf_counter() - score_started) * 1000

        sppu_started = perf_counter()
        sppu_review_data = None
        should_compute_sppu_review = is_hod or is_principal or include_heavy
        if should_compute_sppu_review:
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
        sppu_ms = (perf_counter() - sppu_started) * 1000

        can_verify_grade = False
        verifier_role = None
        if is_hod and (not appraisal.is_hod_appraisal) and appraisal.status == States.REVIEWED_BY_HOD:
            can_verify_grade = True
            verifier_role = "HOD"
        elif is_principal and appraisal.is_hod_appraisal and appraisal.status == States.REVIEWED_BY_PRINCIPAL:
            can_verify_grade = True
            verifier_role = "PRINCIPAL"

        payload_started = perf_counter()
        payload = {
            "id": appraisal.appraisal_id,
            "status": appraisal.status,
            "academic_year": appraisal.academic_year,
            "semester": appraisal.semester,
            "appraisal_data": appraisal.appraisal_data,
            "remarks": appraisal.remarks,
            "verified_grade": verified_grade,
            "verified_grading": verified_grading,
            "calculated_total_score": calculated_total_score,
            "sppu_review_data": sppu_review_data,
            "can_verify_grade": can_verify_grade,
            "verifier_role": verifier_role,
            "verified_grade_options": ["Good", "Satisfactory", "Not Satisfactory"],
            "table2_verified_keys": TABLE2_VERIFIED_KEYS,
            "activity_sections": get_activity_sections(),
            "faculty": {
                "name": appraisal.faculty.full_name,
                "department": appraisal.faculty.department.department_name,
                "designation": appraisal.faculty.designation
            }
        }
        payload_ms = (perf_counter() - payload_started) * 1000
        logger.info(
            "faculty.detail_timing user_id=%s appraisal_id=%s lookup_ms=%.2f perm_ms=%.2f verified_ms=%.2f score_ms=%.2f sppu_mapper_ms=%.2f payload_ms=%.2f include_heavy=%s total_ms=%.2f",
            getattr(request.user, "id", None),
            appraisal_id,
            lookup_ms,
            perm_ms,
            verified_ms,
            score_ms,
            sppu_ms,
            payload_ms,
            include_heavy,
            (perf_counter() - started) * 1000,
        )

        return Response(payload)


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

        # Keep endpoint contract, but route to enhanced renderers so old clients
        # do not receive legacy xhtml2pdf output.
        requested_type = (request.query_params.get("pdf_type") or "SPPU").upper()
        from core.views.pdf_views import generate_enhanced_pbas_pdf, generate_enhanced_sppu_pdf
        if requested_type == "PBAS":
            return generate_enhanced_pbas_pdf(request, appraisal_id)
        return generate_enhanced_sppu_pdf(request, appraisal_id)
