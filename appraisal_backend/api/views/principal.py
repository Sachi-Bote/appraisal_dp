from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.permissions import IsPrincipal
from core.models import Appraisal
from workflow.states import States
from workflow.engine import perform_action
from core.models import ApprovalHistory

class PrincipalApproveAPI(APIView):
    permission_classes = [IsAuthenticated, IsPrincipal]

    def post(self, request, appraisal_id):
        try:
            appraisal = Appraisal.objects.get(appraisal_id=appraisal_id)
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        if appraisal.status != States.PRINCIPAL_REVIEW:
            return Response(
                {"error": "Appraisal not in principal review state"},
                status=400
            )

        new_state = perform_action(
            role="principal",
            action="principal_approve",
            current_state=appraisal.status
        )

        appraisal.status = new_state
        appraisal.principal = request.user
        appraisal.save()

        ApprovalHistory.objects.create(
            appraisal=appraisal,
            approved_by=request.user,
            role="PRINCIPAL",
            action="APPROVED",
            from_state=States.PRINCIPAL_REVIEW,
            to_state=new_state,
            remarks=None
        )

        return Response({
            "message": "Approved by Principal",
            "new_state": new_state
        })

    
class PrincipalAppraisalList(APIView):
    permission_classes = [IsAuthenticated, IsPrincipal]

    def get(self, request):
        appraisals = Appraisal.objects.filter(
            status__in=[States.HOD_APPROVED, States.PRINCIPAL_REVIEW]
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
                role="principal",
                action="start_principal_review",
                current_state=appraisal.status
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

        if appraisal.status != States.PRINCIPAL_REVIEW:
            return Response(
                {"error": "Appraisal not in principal review state"},
                status=400
            )
        
        if appraisal.status == States.FINALIZED:
            return Response({"error": "Finalized appraisal cannot be modified"},
            status=403
        )

        new_state = perform_action(
            role="principal",
            action="principal_reject",
            current_state=appraisal.status
        )

        appraisal.status = new_state
        appraisal.principal = request.user
        appraisal.remarks = remarks
        appraisal.save()

        ApprovalHistory.objects.create(
            appraisal=appraisal,
            approved_by=request.user,
            role="PRINCIPAL",
            action="SENT_BACK",
            from_state=States.PRINCIPAL_REVIEW,
            to_state=new_state,
            remarks=remarks
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

        new_state = perform_action(
            role="principal",
            action="finalize",
            current_state=appraisal.status
        )

        appraisal.status = new_state
        appraisal.save()

        return Response({
            "message": "Appraisal finalized successfully",
            "final_state": new_state
        })
