from django.template.loader import render_to_string
from io import BytesIO
from .pdf_renderer import _render_pdf_bytes


def generate_pdf_from_html(template_name, context):
    html = render_to_string(template_name, context)
    pdf_bytes, _ = _render_pdf_bytes(html)
    return BytesIO(pdf_bytes)

