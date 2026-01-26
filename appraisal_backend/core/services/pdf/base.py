from reportlab.pdfgen import canvas
from io import BytesIO
from pypdf import PdfReader, PdfWriter


def overlay_pdf(template_path, draw_callback):
    packet = BytesIO()
    can = canvas.Canvas(packet)
    
    draw_callback(can)  # draw text here
    
    can.save()
    packet.seek(0)

    overlay = PdfReader(packet)
    template = PdfReader(template_path)

    writer = PdfWriter()
    for i, page in enumerate(template.pages):
        page.merge_page(overlay.pages[min(i, len(overlay.pages)-1)])
        writer.add_page(page)

    output = BytesIO()
    writer.write(output)
    output.seek(0)

    return output
