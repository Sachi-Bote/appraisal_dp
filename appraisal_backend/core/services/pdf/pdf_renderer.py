from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO


def render_to_pdf(template_path: str, context: dict) -> HttpResponse:
    template = get_template(template_path)
    html = template.render(context)

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)

    if pdf.err:
        return HttpResponse(
            "Error generating PDF",
            status=500
        )

    return HttpResponse(
        result.getvalue(),
        content_type="application/pdf"
    )
