from django.shortcuts import get_object_or_404
from core.models import Appraisal, GeneratedPDF
from core.services.pdf.sppu_mapper import get_sppu_pdf_data
from core.services.pdf.pbas_mapper import get_pbas_pdf_data
from core.services.pdf.comprehensive_mapper import get_comprehensive_pdf_data
from core.services.pdf.enhanced_sppu_mapper import get_enhanced_sppu_pdf_data
from core.services.pdf.enhanced_pbas_mapper import get_enhanced_pbas_pdf_data
from core.services.pdf.pdf_renderer import render_to_pdf, save_pdf_to_disk
import os
from django.http import HttpResponse


def generate_sppu_pdf(request, appraisal_id):
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    context = get_sppu_pdf_data(appraisal)
    return render_to_pdf("pdf/sppu.html", context)


def generate_pbas_pdf(request, appraisal_id):
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    context = get_pbas_pdf_data(appraisal)
    return render_to_pdf("pdf/pbas.html", context)


def generate_comprehensive_pdf(request, appraisal_id):
    """Generate comprehensive PDF with all input and calculated data"""
    appraisal = get_object_or_404(Appraisal, appraisal_id=appraisal_id)
    context = get_comprehensive_pdf_data(appraisal)
    return render_to_pdf("pdf/comprehensive_appraisal.html", context)


def generate_enhanced_sppu_pdf(request, appraisal_id):
    """Generate enhanced SPPU PDF, SAVE to DB, and return"""
    appraisal = get_object_or_404(Appraisal, appraisal_id=appraisal_id)
    context = get_enhanced_sppu_pdf_data(appraisal)
    
    # Define filename
    filename = f"SPPU_Enhanced_appraisal_{appraisal_id}.pdf"
    
    # Save to disk
    try:
        file_path = save_pdf_to_disk("pdf/enhanced_sppu.html", context, filename)
        
        # Save to DB (GeneratedPDF model)
        GeneratedPDF.objects.create(
            appraisal=appraisal,
            pdf_path=file_path
        )
        
        # Return the file as response
        with open(file_path, 'rb') as f:
            pdf_content = f.read()
            
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        print(f"Error saving PDF: {e}")
        # Fallback to simple render if save fails
        return render_to_pdf("pdf/enhanced_sppu.html", context)


def generate_enhanced_pbas_pdf(request, appraisal_id):
    """Generate enhanced AICTE PBAS PDF with all fields from sample data"""
    appraisal = get_object_or_404(Appraisal, appraisal_id=appraisal_id)
    context = get_enhanced_pbas_pdf_data(appraisal)
    return render_to_pdf("pdf/enhanced_pbas.html", context)
