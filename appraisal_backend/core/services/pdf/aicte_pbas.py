from .helpers import safe_text
import os
from django.conf import settings

def generate_aicte_pbas(appraisal):
    template = os.path.join(
        settings.BASE_DIR,
        "core/static/pdf_templates/aicte_pbas_form_c.pdf"
    )

    def draw(can):
        can.setFont("Helvetica", 10)

        can.drawString(130, 720, safe_text(appraisal.faculty.full_name))
        can.drawString(130, 700, safe_text(appraisal.faculty.designation))
        can.drawString(130, 680, safe_text(appraisal.department.department_name))

        # Teaching Process scores
        can.drawString(480, 610, safe_text(appraisal.teaching_score))

        # Student feedback
        can.drawString(480, 560, safe_text(appraisal.student_feedback_score))

        # Department activities
        can.drawString(480, 510, safe_text(appraisal.department_activity_score))

        # Final 360 score
        can.drawString(480, 450, safe_text(appraisal.final_score))
        
    return overlay_pdf(template, draw)
