from django.shortcuts import get_object_or_404
from core.models import Appraisal
from core.services.pdf.sppu_mapper import get_sppu_pdf_data
from core.services.pdf.pbas_mapper import get_pbas_pdf_data
from core.services.pdf.pdf_renderer import render_to_pdf


def generate_sppu_pdf(request, appraisal_id):
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    context = get_sppu_pdf_data(appraisal)
    return render_to_pdf("pdf/sppu.html", context)


def generate_pbas_pdf(request, appraisal_id):
    appraisal = get_object_or_404(Appraisal, id=appraisal_id)
    context = get_pbas_pdf_data(appraisal)
    return render_to_pdf("pdf/pbas.html", context)
