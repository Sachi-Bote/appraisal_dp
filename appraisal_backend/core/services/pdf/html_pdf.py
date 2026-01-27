from django.template.loader import render_to_string
from xhtml2pdf import pisa
from io import BytesIO


def generate_pdf_from_html(template_name, context):
    html = render_to_string(template_name, context)

    result = BytesIO()
    pisa_status = pisa.CreatePDF(
        src=html,
        dest=result,
        encoding="UTF-8"
    )

    if pisa_status.err:
        raise Exception("PDF generation failed")

    result.seek(0)
    return result

