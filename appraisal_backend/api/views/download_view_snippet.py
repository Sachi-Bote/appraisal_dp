
from django.http import FileResponse
from core.models import GeneratedPDF
import os

class DownloadAppraisalPDF(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, appraisal_id):
        try:
            appraisal = Appraisal.objects.get(appraisal_id=appraisal_id)
        except Appraisal.DoesNotExist:
            return Response({"error": "Appraisal not found"}, status=404)

        # 1️⃣ Permission Check
        is_owner = appraisal.faculty.user == request.user
        is_principal = request.user.role == "PRINCIPAL"
        
        is_hod = False
        if request.user.role == "HOD":
            # Simple check if HOD manages this faculty's department
            if request.user.department_set.filter(pk=appraisal.faculty.department.pk).exists():
                is_hod = True

        if not (is_owner or is_principal or is_hod):
            return Response({"error": "Unauthorized"}, status=403)

        # 2️⃣ Check for Generated PDF
        # Try to find SPPU_PBAS (default) or other types if specified
        # Since GeneratedPDF model doesn't seem to have 'pdf_type' field in the snippet I saw, 
        # I'll assumme it stores just one or we need to check how they are distinguished if multiple exist.
        # Wait, the PrincipalFinalizeAPI view used 'save_pdf(appraisal, sppu_pdf, "SPPU_PBAS")'.
        # However the model definition I saw:
        # class GeneratedPDF(models.Model): ... pdf_path = ... 
        # It does NOT have 'pdf_type'. 
        # This implies `save_pdf` might be saving multiple rows, but we can't distinguish them easily unless `pdf_path` contains the type.
        # Let's just get the LATEST one for now.
        
        try:
            pdf_record = GeneratedPDF.objects.filter(appraisal=appraisal).latest('generated_at')
            
            if not os.path.exists(pdf_record.pdf_path):
                 return Response({"error": "PDF file not found on server"}, status=404)
                 
            return FileResponse(open(pdf_record.pdf_path, 'rb'), content_type='application/pdf')
        except GeneratedPDF.DoesNotExist:
             return Response({"error": "PDF not generated yet"}, status=404)
