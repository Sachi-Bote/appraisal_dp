from core.models import GeneratedPDF
from django.core.files.base import ContentFile


def save_pdf(appraisal, pdf_bytes, pdf_type):
    filename = f"{pdf_type}_appraisal_{appraisal.id}.pdf"

    pdf_obj = GeneratedPDF.objects.create(
        appraisal=appraisal,
        pdf_path=f"media/generated_pdfs/{filename}"
    )

    with open(pdf_obj.pdf_path, "wb") as f:
        f.write(pdf_bytes.read())

    return pdf_obj
