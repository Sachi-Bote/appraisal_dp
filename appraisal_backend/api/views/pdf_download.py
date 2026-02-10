from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.http import FileResponse, Http404
from core.models import GeneratedPDF
from django.shortcuts import get_object_or_404
import os


class PDFDownloadAPI(APIView):
    """API to download a specific generated PDF"""
    permission_classes = [IsAuthenticated]

    def get(self, request, appraisal_id, pdf_id):
        pdf = get_object_or_404(GeneratedPDF, pdf_id=pdf_id, appraisal__appraisal_id=appraisal_id)
        
        # Check if file exists
        if not os.path.exists(pdf.pdf_path):
            raise Http404("PDF file not found")
        
        # Get filename for download
        filename = os.path.basename(pdf.pdf_path)
        
        # Open and return file
        response = FileResponse(open(pdf.pdf_path, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
