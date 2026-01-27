import os
from django.conf import settings
from core.models import GeneratedPDF


def save_pdf(appraisal, pdf_bytes, pdf_type):
    pdf_dir = os.path.join(settings.MEDIA_ROOT, "generated_pdfs")
    os.makedirs(pdf_dir, exist_ok=True)

    filename = f"{pdf_type}_appraisal_{appraisal.appraisal_id}.pdf"
    path = os.path.join(pdf_dir, filename)

    with open(path, "wb") as f:
        f.write(pdf_bytes.read())

    return GeneratedPDF.objects.create(
        appraisal=appraisal,
        pdf_path=path
    )
