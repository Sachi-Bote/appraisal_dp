from django.conf import settings
from .base import overlay_pdf
import os
from .helpers import safe_text

def generate_sppu_pbas(appraisal):
    template = os.path.join(
        settings.BASE_DIR,
        "core/static/pdf_templates/sppu_pbas_appendix_ii.pdf"
    )

    def draw(can):
        can.setFont("Helvetica", 10)

        # Page 1 – Section A
        can.drawString(120, 720, safe_text(appraisal.faculty.full_name))
        can.drawString(120, 680, safe_text(appraisal.form_type))
        can.drawString(120, 700, safe_text(appraisal.faculty.designation))
        can.drawString(180, 660, safe_text(appraisal.faculty.mobile))
        can.drawString(220, 640, safe_text(appraisal.academic_year))
        # Teaching data (example)

        # HOD remarks
        if appraisal.hod_remark:
            can.drawString(80, 220, appraisal.hod_remark)

        # Principal remarks
        if appraisal.principal_remark:
            can.drawString(80, 160, appraisal.principal_remark)

    return overlay_pdf(template, draw)
