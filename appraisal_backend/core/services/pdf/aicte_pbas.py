import os
from django.conf import settings

from core.services.pdf.base import overlay_pdf
from core.services.pdf.helpers import safe_text
from core.services.pdf.data_mapper import get_appraisal_pdf_data


def generate_aicte_pbas(appraisal):
    template = os.path.join(
        settings.BASE_DIR,
        "core/static/pdf_templates/aicte_pbas_form.html"
    )

    pdf_data = get_appraisal_pdf_data(appraisal)

    def draw(can):
        can.setFont("Helvetica", 10)

        faculty = pdf_data["faculty"]

        # ---------- FACULTY DETAILS ----------
        can.drawString(130, 720, safe_text(faculty["name"]))
        can.drawString(130, 700, safe_text(faculty["designation"]))
        can.drawString(130, 680, safe_text(faculty["department"]))

        # ---------- SCORES ----------
        teaching = pdf_data["teaching"]

        can.drawString(480, 610, safe_text(teaching.get("points")))
        # Add more fields here as per AICTE format

    return overlay_pdf(template, draw)
