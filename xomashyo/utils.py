from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from django.http import HttpResponse
from main.models import Xomashyo, XomashyoHarakat

def generate_xomashyo_pdf(queryset):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="xomashyolar.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # PDF sarlavhasi
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Xomashyolar Ro'yxati", styles['Title']))
    
    # Jadval ma'lumotlari
    data = [["№", "Nomi", "Miqdori", "O'lchov", "Narxi", "Holati"]]
    
    for i, xomashyo in enumerate(queryset, start=1):
        data.append([
            str(i),
            xomashyo.nomi,
            str(xomashyo.miqdori),
            xomashyo.get_olchov_birligi_display(),
            f"{xomashyo.narxi:,} so'm",
            xomashyo.get_holati_display()
        ])
    
    # Jadval yaratish
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response


def generate_xomashyo_harakat_pdf(queryset):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="xomashyo_harakatlari.pdf"'
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Sarlavha va asosiy ma'lumotlar
    styles = getSampleStyleSheet()
    elements.append(Paragraph("Xomashyo Harakatlari Tarixi", styles['Title']))
    
    # Jadval uchun ma'lumotlar tayyorlash
    data = [
        ["№", "Xomashyo", "Harakat Turi", "Miqdori", "Sana", "Foydalanuvchi", "Izoh"]
    ]
    
    for i, harakat in enumerate(queryset, start=1):
        data.append([
            str(i),
            harakat.xomashyo.nomi,
            harakat.get_harakat_turi_display(),
            f"{harakat.miqdori} {harakat.xomashyo.olchov_birligi}",
            harakat.sana.strftime('%d.%m.%Y %H:%M'),
            harakat.foydalanuvchi.username if harakat.foydalanuvchi else "-",
            harakat.izoh or "-"
        ])
    
    # Jadval yaratish va stil berish
    table = Table(data, colWidths=[30, 120, 80, 60, 80, 80, 120])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3A5FCD')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F0F8FF')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#7EC0EE')),
        ('WORDWRAP', (6, 0), (6, -1)),  # Izoh uchun qator o'tkazish
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response