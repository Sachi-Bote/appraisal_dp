
from core.services.pdf.data_mapper import get_common_pdf_data
from core.services.pdf.sppu_mapper import get_sppu_pdf_data
from core.services.pdf.pbas_mapper import get_pbas_pdf_data
from core.services.pdf.html_pdf import generate_pdf_from_html
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.permissions import IsPrincipal
from core.models import Appraisal
from workflow.states import States
from workflow.engine import perform_action
from core.models import ApprovalHistory
from core.services.pdf.save import save_pdf
from core.utils.audit import log_action
from django.db import transaction
from core.utils.audit import log_action
from django.db import transaction


class PrincipalApproveAPI(APIView):
    permission_classes = [IsAuthenticated, IsPrincipal]

    def post(self, request, appraisal_id):
        try:
            appraisal = Appraisal.objects.get(appraisal_id=appraisal_id)
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        if appraisal.status != States.REVIEWED_BY_PRINCIPAL:
            return Response(
                {"error": "Appraisal not in principal review state"},
                status=400
            )

        new_state = perform_action(
            current_state=appraisal.status,
            next_state=States.PRINCIPAL_APPROVED
        )

        appraisal.status = new_state
        appraisal.principal = request.user
        appraisal.save()

        ApprovalHistory.objects.update_or_create(
            appraisal=appraisal,
            role="PRINCIPAL",
            defaults={
                "approved_by": request.user,
                "action": "APPROVED",
                "from_state": States.REVIEWED_BY_PRINCIPAL,
                "to_state": new_state,
                "remarks": None
            }
        )

        return Response({
            "message": "Approved by Principal",
            "new_state": new_state
        })

    
class PrincipalAppraisalList(APIView):
    permission_classes = [IsAuthenticated, IsPrincipal]

    def get(self, request):
        from django.db.models import Q
        
        appraisals = (
            Appraisal.objects
            .filter(
                Q(status__in=[
                    States.HOD_APPROVED,
                    States.REVIEWED_BY_PRINCIPAL,
                    States.PRINCIPAL_APPROVED,
                    States.FINALIZED,
                ]) |
                Q(status=States.SUBMITTED, is_hod_appraisal=True)
            )
            .select_related("faculty__user")
            .order_by("-updated_at")
        )

        response_data = []

        for a in appraisals:
            faculty = a.faculty
            user = faculty.user if faculty else None

            response_data.append({
                "id": a.appraisal_id,

                # ✅ FACULTY DETAILS
                "faculty_name": faculty.full_name if faculty else None,
                "designation": faculty.designation if faculty else None,
                "department": user.department if user else None,

                # ✅ APPRAISAL DETAILS
                "academic_year": a.academic_year,
                "semester": a.semester,
                "status": a.status,
                "remarks": a.remarks,
                "is_hod_appraisal": a.is_hod_appraisal,
            })


        return Response(response_data)


class PrincipalStartReviewAPI(APIView):
    permission_classes = [IsAuthenticated, IsPrincipal]

    def post(self, request, appraisal_id):
        try:
            appraisal = Appraisal.objects.get(appraisal_id=appraisal_id)
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)
        

        if appraisal.status == States.FINALIZED:
            return Response({"error": "Finalized appraisal cannot be modified"},
            status=403
        )


        try:
            new_state = perform_action(
                current_state=appraisal.status,
                next_state=States.REVIEWED_BY_PRINCIPAL
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

        appraisal.status = new_state
        appraisal.principal = request.user
        appraisal.save()

        return Response({
            "message": "Moved to principal review",
            "current_state": new_state
        })
    
class PrincipalReturnAPI(APIView):
    permission_classes = [IsAuthenticated, IsPrincipal]

    def post(self, request, appraisal_id):
        remarks = request.data.get("remarks", "")

        try:
            appraisal = Appraisal.objects.get(appraisal_id=appraisal_id)
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        if appraisal.status not in [States.SUBMITTED, States.HOD_APPROVED, States.REVIEWED_BY_PRINCIPAL]:
            return Response(
                {"error": "Appraisal not in a state that can be returned by Principal"},
                status=400
            )
        
        if appraisal.status == States.FINALIZED:
            return Response({"error": "Finalized appraisal cannot be modified"},
            status=403
        )

        new_state = perform_action(
            current_state=appraisal.status,
            next_state=States.RETURNED_BY_PRINCIPAL
        )


        appraisal.status = new_state
        appraisal.principal = request.user
        appraisal.remarks = remarks
        appraisal.save()

        ApprovalHistory.objects.update_or_create(
            appraisal=appraisal,
            role="PRINCIPAL",
            defaults={
                "approved_by": request.user,
                "action": "SENT_BACK",
                "from_state": appraisal.status, # Use dynamic state
                "to_state": new_state,
                "remarks": remarks
            }
        )

        return Response({
            "message": "Returned to faculty",
            "new_state": new_state
        })

class PrincipalFinalizeAPI(APIView):
    permission_classes = [IsAuthenticated, IsPrincipal]

    @transaction.atomic
    def post(self, request, appraisal_id):
        try:
            appraisal = Appraisal.objects.get(appraisal_id=appraisal_id)
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        if appraisal.status != States.PRINCIPAL_APPROVED:
            return Response(
                {"error": "Only principal-approved appraisals can be finalized"},
                status=400
            )
        old_state = {
            "status": appraisal.status
        }

        # 1️⃣ Finalize workflow state
        new_state = perform_action(
            current_state=appraisal.status,
            next_state=States.FINALIZED
        )

        appraisal.status = new_state
        appraisal.save()

        # 2️⃣ Generate SPPU PDF (Full)
        sppu_data = get_sppu_pdf_data(appraisal)
        sppu_pdf = generate_pdf_from_html("pdf/sppu_pbas_form.html", sppu_data)
        save_pdf(appraisal, sppu_pdf, "SPPU_PBAS")

        # 3️⃣ Generate AICTE PBAS PDF (Truncated/Partial)
        pbas_data = get_pbas_pdf_data(appraisal)
        aicte_pdf = generate_pdf_from_html("pdf/aicte_pbas_form.html", pbas_data)
        save_pdf(appraisal, aicte_pdf, "AICTE_PBAS")

        # 4️⃣ Audit log
        log_action(
                request=request,
                action="SUBMIT_APPRAISAL",
                entity="Appraisal",
                entity_id=appraisal.appraisal_id,
                old_value=old_state,
                new_value={
                    "status": appraisal.status,
                    "faculty_id": appraisal.faculty.pk

                }
            )

        # 5️⃣ Return response LAST
        return Response({
            "message": "Appraisal finalized successfully",
            "final_state": new_state
        })