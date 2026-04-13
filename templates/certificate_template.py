from io import BytesIO
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def generate_certificate_pdf(cert_data: dict) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Background and border
    c.setFillColor(colors.white)
    c.rect(0, 0, width, height, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#0B5ED7"))
    c.setLineWidth(3)
    c.rect(15 * mm, 15 * mm, width - 30 * mm, height - 30 * mm, fill=0, stroke=1)

    # Top logo (fallback to text if image not found)
    logo_path = Path(__file__).resolve().parents[1] / "arquivos_do_projeto" / "logos" / "LOGOS_PNG" / "TDS.PNG.png"
    if logo_path.exists():
        c.drawImage(str(logo_path), width / 2 - 20 * mm, height - 45 * mm, width=40 * mm, height=22 * mm, preserveAspectRatio=True, mask='auto')
    else:
        c.setFillColor(colors.HexColor("#003366"))
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width / 2, height - 35 * mm, "TDS")

    # Main body
    c.setFillColor(colors.HexColor("#1F2937"))
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 70 * mm, "CERTIFICADO")

    c.setFont("Helvetica", 13)
    c.drawCentredString(width / 2, height - 86 * mm, "Certificamos que")

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(colors.HexColor("#0F766E"))
    c.drawCentredString(width / 2, height - 102 * mm, cert_data.get("student_name", "Aluno"))

    c.setFillColor(colors.HexColor("#1F2937"))
    c.setFont("Helvetica", 13)
    c.drawCentredString(width / 2, height - 118 * mm, "concluiu com êxito o curso")

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 132 * mm, cert_data.get("course_title") or cert_data.get("course", "Curso"))

    issue_date = cert_data.get("issue_date", "")
    cert_hash = cert_data.get("cert_id", "")
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, 40 * mm, f"Data de emissão: {issue_date}")
    c.drawCentredString(width / 2, 33 * mm, f"Hash de validação: {cert_hash}")

    # QR code in bottom-right corner
    validation_url = cert_data.get("validation_url", "")
    qr = QrCodeWidget(validation_url)
    qr_size = 28 * mm
    bounds = qr.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]
    drawing = Drawing(qr_size, qr_size, transform=[qr_size / qr_width, 0, 0, qr_size / qr_height, 0, 0])
    drawing.add(qr)
    renderPDF.draw(drawing, c, width - 48 * mm, 20 * mm)

    c.setFont("Helvetica", 8)
    c.drawString(width - 48 * mm, 17 * mm, "Validar certificado")

    c.showPage()
    c.save()
    return buffer.getvalue()
