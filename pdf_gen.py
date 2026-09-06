# pdf_gen.py — ReportLab Compliant Vector PDF Generation
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from io import BytesIO

def generate_pdf(data: dict, client_name: str, client_gstin: str, logo_path=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        leftMargin=1.5*cm, 
        rightMargin=1.5*cm, 
        topMargin=1.5*cm, 
        bottomMargin=1.5*cm
    )
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Title'],
        fontSize=22,
        textColor=colors.HexColor('#4F46E5'),
        alignment=0
    )
    story.append(Paragraph("TAX INVOICE", title_style))
    story.append(Spacer(1, 0.4*cm))

    supplier_name = data.get('supplier_name', 'Verified Merchant')
    supplier_gstin = data.get('supplier_gstin', 'N/A')
    invoice_date = data.get('date', 'N/A')
    
    meta_data = [
        [
            Paragraph(f"<b>Supplier / Merchant:</b> {supplier_name}<br/><b>GSTIN:</b> {supplier_gstin}", styles['Normal']),
            Paragraph(f"<b>Bill To:</b> {client_name}<br/><b>GSTIN:</b> {client_gstin}<br/><b>Date:</b> {invoice_date}", styles['Normal'])
        ]
    ]
    meta_table = Table(meta_data, colWidths=[9*cm, 9*cm])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.6*cm))

    items_data = [["Description", "Qty", "Rate (Rs.)", "Amount (Rs.)"]]
    
    for item in data.get('items', []):
        items_data.append([
            str(item.get('desc', 'Item')),
            str(item.get('qty', 1)),
            f"Rs. {item.get('rate', 0):,.2f}",
            f"Rs. {item.get('amt', 0):,.2f}"
        ])

    subtotal = sum(float(item.get('amt', 0)) for item in data.get('items', []))
    if subtotal == 0:
        subtotal = float(data.get('subtotal', 100.00))
        
    cgst = float(data.get('cgst', round(subtotal * 0.09, 2)))
    sgst = float(data.get('sgst', cgst))
    grand_total = float(data.get('grand_total', round(subtotal + cgst + sgst, 2)))

    items_data += [
        ["", "", "Subtotal", f"Rs. {subtotal:,.2f}"],
        ["", "", "CGST (9%)", f"Rs. {cgst:,.2f}"],
        ["", "", "SGST (9%)", f"Rs. {sgst:,.2f}"],
        ["", "", "Grand Total", f"Rs. {grand_total:,.2f}"]
    ]

    table = Table(items_data, colWidths=[9.5*cm, 1.5*cm, 3.5*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F46E5")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT'),
        ('ALIGN', (0,1), (0,-1), 'LEFT'),
        ('GRID', (0,0), (-1,-5), 0.5, colors.HexColor('#E2E8F0')),
        ('SPAN', (0,-4), (1,-4)),
        ('SPAN', (0,-3), (1,-3)),
        ('SPAN', (0,-2), (1,-2)),
        ('SPAN', (0,-1), (1,-1)),
        ('FONTNAME', (2,-1), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (2,-1), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,-4), (-1,-1), 1, colors.HexColor('#4F46E5')),
        ('FONTNAME', (0,1), (-1,-5), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-1), 9),
    ]))
    story.append(table)

    story.append(Spacer(1, 1*cm))
    
    footer_style = ParagraphStyle(
        'InvoiceFooter',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#64748B'),
        alignment=1 
    )
    story.append(Paragraph("This is a computer-generated tax invoice processed and compiled via <b>GenVoicely AI</b>", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()