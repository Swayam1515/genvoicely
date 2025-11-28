# pdf_gen.py — FINAL VERSION (NO LOGO = NO CRASH, ₹ WORKS)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO
import os

def generate_pdf(data: dict, client_name: str, client_gstin: str, logo_path=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
    styles = getSampleStyleSheet()
    story = []

    # ONLY ADD LOGO IF IT'S A REAL VALID IMAGE
    logo_added = False
    if logo_path and os.path.exists(logo_path):
        try:
            from PIL import Image as PILImage
            img = PILImage.open(logo_path)
            img.verify()  # This catches corrupted files
            from reportlab.platypus.flowables import Image as RLImage
            logo = RLImage(logo_path, width=2*cm, height=2*cm)
            logo.hAlign = 'LEFT'
            story.append(logo)
            story.append(Spacer(1, 0.3*cm))
            logo_added = True
        except:
            pass  # Silently ignore broken/missing logo

    story.append(Paragraph("TAX INVOICE", styles['Title']))
    story.append(Spacer(1, 0.5*cm))

    # Supplier info
    story.append(Paragraph(f"<b>Supplier:</b> Genvoicely AI", styles['Normal']))
    story.append(Paragraph(f"<b>GSTIN:</b> {data.get('supplier_gstin', '')}", styles['Normal']))
    story.append(Paragraph(f"<b>Date:</b> {data.get('date', '')}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Client info
    story.append(Paragraph(f"<b>Bill To:</b> {client_name}", styles['Normal']))
    story.append(Paragraph(f"<b>GSTIN:</b> {client_gstin}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    # Items table
    items_data = [["Description", "Qty", "Rate", "Amount"]]
    for item in data.get('items', []):
        items_data.append([
            item.get('desc', 'Item'),
            str(item.get('qty', 1)),
            f"₹ {item.get('rate', 0):,.2f}",
            f"₹ {item.get('amt', 0):,.2f}"
        ])

    subtotal = data.get('subtotal', 0)
    cgst = data.get('cgst', 0)
    sgst = data.get('sgst', 0)
    total = data.get('grand_total', 0)

    items_data += [
        ["", "Subtotal", "", f"₹ {subtotal:,.2f}"],
        ["", "CGST", "", f"₹ {cgst:,.2f}"],
        ["", "SGST", "", f"₹ {sgst:,.2f}"],
        ["", "Total", "", f"₹ {total:,.2f}"]
    ]

    table = Table(items_data, colWidths=[7*cm, 1.5*cm, 2*cm, 2.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1E3A8A")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
    ]))
    story.append(table)

    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Thank you! Powered by <b>Genvoicely AI</b>", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer