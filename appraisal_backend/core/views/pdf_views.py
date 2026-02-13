from django.shortcuts import get_object_or_404
from core.models import Appraisal, GeneratedPDF
from core.services.pdf.sppu_mapper import get_sppu_pdf_data
from core.services.pdf.pbas_mapper import get_pbas_pdf_data
from core.services.pdf.enhanced_sppu_mapper import get_enhanced_sppu_pdf_data
from core.services.pdf.enhanced_pbas_mapper import get_enhanced_pbas_pdf_data
from core.services.pdf.pdf_renderer import render_to_pdf, save_pdf_to_disk
import os
from django.http import HttpResponse


def _save_pdf_and_return_response(appraisal, template_path, context, filename):
    """
    Save rendered PDF to disk + GeneratedPDF table, then return file response.
    Falls back to direct render when save fails.
    """
    try:
        file_path = save_pdf_to_disk(template_path, context, filename)

        GeneratedPDF.objects.create(
            appraisal=appraisal,
            pdf_path=file_path
        )

        with open(file_path, 'rb') as f:
            pdf_content = f.read()

        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception:
        return render_to_pdf(template_path, context)


def generate_sppu_pdf(request, appraisal_id):
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    context = get_sppu_pdf_data(appraisal)
    return render_to_pdf("pdf/sppu.html", context)


def generate_pbas_pdf(request, appraisal_id):
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    context = get_pbas_pdf_data(appraisal)
    return render_to_pdf("pdf/pbas.html", context)


def generate_enhanced_sppu_pdf(request, appraisal_id):
    """Generate enhanced SPPU PDF, SAVE to DB, and return"""
    appraisal = get_object_or_404(Appraisal, appraisal_id=appraisal_id)
    context = get_enhanced_sppu_pdf_data(appraisal)
    
    filename = f"SPPU_Enhanced_appraisal_{appraisal_id}.pdf"
    return _save_pdf_and_return_response(
        appraisal=appraisal,
        template_path="pdf/enhanced_sppu.html",
        context=context,
        filename=filename
    )


def generate_enhanced_pbas_pdf(request, appraisal_id):
    """Generate enhanced AICTE PBAS PDF, save to DB/disk, and return"""
    appraisal = get_object_or_404(Appraisal, appraisal_id=appraisal_id)
    context = get_enhanced_pbas_pdf_data(appraisal)
    filename = f"PBAS_Enhanced_appraisal_{appraisal_id}.pdf"
    return _save_pdf_and_return_response(
        appraisal=appraisal,
        template_path="pdf/enhanced_pbas.html",
        context=context,
        filename=filename
    )
