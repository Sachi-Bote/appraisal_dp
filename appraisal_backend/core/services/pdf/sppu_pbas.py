import os
from django.conf import settings

from core.services.pdf.base import overlay_pdf
from core.services.pdf.helpers import safe_text
from core.services.pdf.data_mapper import get_appraisal_pdf_data


def generate_sppu_pbas(appraisal):
    template = os.path.join(
        settings.BASE_DIR,
        "core/static/pdf_templates/sppu_pbas_form.html"
    )

    data = get_appraisal_pdf_data(appraisal)

    def draw(can):
        can.setFont("Helvetica", 10)

        faculty = data["faculty"]

        # ---------- SECTION A ----------
        can.drawString(120, 720, safe_text(faculty["name"]))
        can.drawString(120, 700, safe_text(faculty["designation"]))
        can.drawString(180, 680, safe_text(faculty["department"]))
        can.drawString(180, 660, safe_text(faculty["mobile"]))
        can.drawString(220, 640, safe_text(data["period"]))

        # ---------- SECTION B(A): TEACHING ----------
        teaching = data["teaching"]
        subjects = teaching["subjects"]

        start_y = 520
        row_gap = 18

        for idx, sub in enumerate(subjects):
            y = start_y - (idx * row_gap)

            can.drawString(60, y, str(idx + 1))
            can.drawString(150, y, safe_text(sub.get("name")))
            can.drawString(300, y, safe_text(sub.get("class")))
            can.drawString(420, y, safe_text(sub.get("hours_per_week")))

        # ---------- TOTALS ----------
        y_total = start_y - (len(subjects) * row_gap)

        can.drawString(300, y_total, safe_text(teaching["total_assigned"]))
        can.drawString(360, y_total, safe_text(teaching["total_taught"]))
        can.drawString(420, y_total, safe_text(teaching["points"]))

        # ==================================================
        # REMARKS (IF ANY)
        # ==================================================
        if data.get("remarks"):
            can.drawString(80, 200, safe_text(data["remarks"]))

    return overlay_pdf(template, draw)