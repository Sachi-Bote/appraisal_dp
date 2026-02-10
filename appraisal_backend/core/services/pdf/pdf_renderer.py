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


def save_pdf_to_disk(template_path: str, context: dict, filename: str) -> str:
    """
    Render PDF and save to disk, returning the file path.
    """
    template = get_template(template_path)
    html = template.render(context)
    
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    
    if pdf.err:
        raise Exception("Error generating PDF")
        
    # Define save directory
    import os
    from django.conf import settings
    
    # Use MEDIA_ROOT if available, else formatted 'generated_pdfs' in base dir
    if hasattr(settings, 'MEDIA_ROOT') and settings.MEDIA_ROOT:
        output_dir = os.path.join(settings.MEDIA_ROOT, 'pdfs')
    else:
        output_dir = os.path.join(settings.BASE_DIR, 'generated_pdfs')
        
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, filename)
    
    with open(file_path, 'wb') as f:
        f.write(result.getvalue())
        
    return file_path
