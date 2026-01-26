
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.permissions import IsPrincipal
from core.models import Appraisal
from workflow.states import States
from workflow.engine import perform_action
from core.models import ApprovalHistory

from core.services.pdf.sppu_pbas import generate_sppu_pbas
from core.services.pdf.aicte_pbas import generate_aicte_pbas
from core.services.pdf.save import save_pdf


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
        appraisals = Appraisal.objects.filter(
            status__in=[States.SUBMITTED, States.HOD_APPROVED, States.REVIEWED_BY_PRINCIPAL]
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

        if appraisal.status != States.REVIEWED_BY_PRINCIPAL:
            return Response(
                {"error": "Appraisal not in principal review state"},
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
        appraisal.principal = request.user
        appraisal.remarks = remarks
        appraisal.save()

        ApprovalHistory.objects.update_or_create(
            appraisal=appraisal,
            role="PRINCIPAL",
            defaults={
                "approved_by": request.user,
                "action": "SENT_BACK",
                "from_state": States.REVIEWED_BY_PRINCIPAL,
                "to_state": new_state,
                "remarks": None
            }
        )

        return Response({
            "message": "Returned to faculty",
            "new_state": new_state
        })

class PrincipalFinalizeAPI(APIView):
    permission_classes = [IsAuthenticated, IsPrincipal]

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

        # 1️⃣ Finalize workflow state
        new_state = perform_action(
            current_state=appraisal.status,
            next_state=States.FINALIZED
        )

        appraisal.status = new_state
        appraisal.save()

        # 2️⃣ Generate SPPU PBAS PDF
        sppu_pdf = generate_sppu_pbas(appraisal)
        save_pdf(appraisal, sppu_pdf, "SPPU_PBAS")

        # 3️⃣ Generate AICTE PBAS PDF
        aicte_pdf = generate_aicte_pbas(appraisal)
        save_pdf(appraisal, aicte_pdf, "AICTE_PBAS")

        # 4️⃣ Audit log
        log_action(
            user=request.user,
            action="Finalized appraisal and generated PDFs",
            entity="Appraisal",
            entity_id=appraisal.appraisal_id
        )

        # 5️⃣ Return response LAST
        return Response({
            "message": "Appraisal finalized successfully",
            "final_state": new_state
        })