from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.models import Appraisal, GeneratedPDF
from django.shortcuts import get_object_or_404
import os


class AppraisalPDFListAPI(APIView):
    """API to get list of generated PDFs for an appraisal"""
    permission_classes = [IsAuthenticated]

    def get(self, request, appraisal_id):
        appraisal = get_object_or_404(Appraisal, appraisal_id=appraisal_id)
        
        # Get all PDFs for this appraisal
        pdfs = GeneratedPDF.objects.filter(appraisal=appraisal).order_by('-generated_at')
        
        pdf_list = []
        for pdf in pdfs:
            # Extract PDF type from filename
            filename = os.path.basename(pdf.pdf_path)
            pdf_type = filename.split('_appraisal_')[0] if '_appraisal_' in filename else 'PDF'
            
            pdf_list.append({
                'pdf_id': pdf.pdf_id,
                'pdf_type': pdf_type,
                'filename': filename,
                'generated_at': pdf.generated_at,
                'download_url': f'/api/appraisal/{appraisal_id}/pdf/download/{pdf.pdf_id}/'
            })
        
        return Response({
            'appraisal_id': appraisal_id,
            'pdfs': pdf_list
        })
