import os
from io import BytesIO
from pathlib import Path
from decimal import Decimal

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from .company_config import COMPANY_DETAILS
from .utils import amount_to_words, format_currency


class InvoicePDFService:
    """Service for generating invoice PDFs using ReportLab."""

    _fonts_registered = False

    @classmethod
    def _register_fonts(cls):
        """Register DejaVu fonts for Polish characters support."""
        if cls._fonts_registered:
            return

        font_path = os.path.join(settings.BASE_DIR, 'static', 'fonts')
        dejavu_path = os.path.join(font_path, 'DejaVuSans.ttf')
        dejavu_bold_path = os.path.join(font_path, 'DejaVuSans-Bold.ttf')

        if os.path.exists(dejavu_path):
            pdfmetrics.registerFont(TTFont('DejaVuSans', dejavu_path))

        if os.path.exists(dejavu_bold_path):
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', dejavu_bold_path))

        cls._fonts_registered = True

    def _get_styles(self):
        """Get paragraph styles for PDF."""
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='InvoiceTitle',
            fontName='DejaVuSans-Bold',
            fontSize=20,
            spaceAfter=6,
            textColor=colors.HexColor('#1F2937'),
        ))

        styles.add(ParagraphStyle(
            name='InvoiceSubtitle',
            fontName='DejaVuSans',
            fontSize=10,
            textColor=colors.HexColor('#6B7280'),
        ))

        styles.add(ParagraphStyle(
            name='SectionTitle',
            fontName='DejaVuSans-Bold',
            fontSize=11,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor('#1F2937'),
        ))

        styles.add(ParagraphStyle(
            name='Normal_PL',
            fontName='DejaVuSans',
            fontSize=9,
            leading=14,
        ))

        styles.add(ParagraphStyle(
            name='Bold_PL',
            fontName='DejaVuSans-Bold',
            fontSize=9,
            leading=14,
        ))

        styles.add(ParagraphStyle(
            name='Small_PL',
            fontName='DejaVuSans',
            fontSize=8,
            textColor=colors.HexColor('#6B7280'),
        ))

        return styles

    def generate_pdf(self, invoice) -> BytesIO:
        """Generate PDF for invoice using ReportLab.

        Args:
            invoice: Invoice instance with related items.

        Returns:
            BytesIO buffer with PDF data.
        """
        # Register fonts
        self._register_fonts()

        # Create PDF buffer
        pdf_buffer = BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm,
        )

        # Get styles
        styles = self._get_styles()

        # Build content
        elements = []

        # Header
        elements.append(Paragraph('FAKTURA VAT', styles['InvoiceTitle']))
        elements.append(Paragraph(f'Nr {invoice.invoice_number}', styles['InvoiceSubtitle']))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(
            f'Data wystawienia: {invoice.issue_date.strftime("%d.%m.%Y")}<br/>'
            f'Termin płatności: {invoice.due_date.strftime("%d.%m.%Y")}',
            styles['Normal_PL']
        ))
        elements.append(Spacer(1, 20))

        # Parties table (Seller / Buyer)
        company = COMPANY_DETAILS
        seller_info = f'''<b>{company["name"]}</b><br/>
{company["address"]}<br/>
{company["postal_code"]} {company["city"]}<br/>
NIP: {company["nip"]}<br/>
Tel: {company["phone"]}<br/>
Email: {company["email"]}'''

        # Get buyer info
        student = invoice.student
        if hasattr(student, 'student_profile') and student.student_profile and student.student_profile.parent_name:
            buyer_name = student.student_profile.parent_name
            buyer_email = student.student_profile.parent_email or student.email
        else:
            buyer_name = student.get_full_name()
            buyer_email = student.email

        buyer_info = f'<b>{buyer_name}</b><br/>{buyer_email}'

        parties_data = [
            [Paragraph('<b>Sprzedawca:</b>', styles['SectionTitle']),
             Paragraph('<b>Nabywca:</b>', styles['SectionTitle'])],
            [Paragraph(seller_info, styles['Normal_PL']),
             Paragraph(buyer_info, styles['Normal_PL'])],
        ]

        parties_table = Table(parties_data, colWidths=[8*cm, 8*cm])
        parties_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        elements.append(parties_table)
        elements.append(Spacer(1, 20))

        # Items table
        items_data = [
            ['Lp.', 'Nazwa usługi', 'Ilość (h)', 'Cena netto', 'Wartość netto', 'VAT'],
        ]

        for i, item in enumerate(invoice.items.all(), 1):
            items_data.append([
                str(i),
                item.description,
                f'{item.quantity:.2f}',
                f'{item.unit_price:.2f} zł',
                f'{item.total_price:.2f} zł',
                '23%',
            ])

        items_table = Table(items_data, colWidths=[1*cm, 6*cm, 2*cm, 2.5*cm, 2.5*cm, 1.5*cm])
        items_table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3B82F6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            # Body
            ('FONTNAME', (0, 1), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            # Grid
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 20))

        # Summary
        summary_data = [
            ['Suma netto:', f'{invoice.net_amount:.2f} zł'],
            ['VAT (23%):', f'{invoice.vat_amount:.2f} zł'],
            ['RAZEM BRUTTO:', f'{invoice.total_amount:.2f} zł'],
        ]

        summary_table = Table(summary_data, colWidths=[12*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVuSans'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 2), (-1, 2), 'DejaVuSans-Bold'),
            ('FONTSIZE', (0, 2), (-1, 2), 12),
            ('LINEABOVE', (0, 2), (-1, 2), 1, colors.HexColor('#1F2937')),
            ('TOPPADDING', (0, 2), (-1, 2), 8),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 15))

        # Amount in words
        elements.append(Paragraph(
            f'<b>Słownie:</b> {amount_to_words(invoice.total_amount)}',
            styles['Normal_PL']
        ))
        elements.append(Spacer(1, 20))

        # Payment info
        elements.append(Paragraph('<b>Forma płatności: Przelew bankowy</b>', styles['Normal_PL']))
        elements.append(Paragraph(f'Numer konta: {company["bank_account"]}', styles['Normal_PL']))
        elements.append(Paragraph(f'Bank: {company["bank_name"]}', styles['Normal_PL']))
        elements.append(Paragraph(f'<b>Tytuł przelewu:</b> {invoice.invoice_number}', styles['Normal_PL']))

        # Notes
        if invoice.notes:
            elements.append(Spacer(1, 15))
            elements.append(Paragraph(f'<b>Uwagi:</b> {invoice.notes}', styles['Normal_PL']))

        # Build PDF
        doc.build(elements)
        pdf_buffer.seek(0)

        return pdf_buffer

    def save_pdf(self, invoice, upload_to_cloud: bool = False) -> str:
        """Generate and save PDF to filesystem or cloud.

        Args:
            invoice: Invoice instance.
            upload_to_cloud: Whether to upload to S3.

        Returns:
            URL/path to saved PDF.
        """
        pdf_buffer = self.generate_pdf(invoice)

        filename = f"{invoice.invoice_number.replace('/', '-')}.pdf"

        if upload_to_cloud and hasattr(settings, 'AWS_S3_BUCKET'):
            # S3 upload (optional for production)
            pdf_url = self._upload_to_s3(pdf_buffer, filename)
        else:
            # Local storage
            invoices_dir = Path(settings.MEDIA_ROOT) / 'invoices'
            invoices_dir.mkdir(parents=True, exist_ok=True)

            filepath = invoices_dir / filename
            with open(filepath, 'wb') as f:
                f.write(pdf_buffer.getvalue())

            pdf_url = f"/media/invoices/{filename}"

        # Update invoice with PDF path
        invoice.pdf_path = pdf_url
        invoice.save(update_fields=['pdf_path'])

        return pdf_url

    def _upload_to_s3(self, pdf_buffer: BytesIO, filename: str) -> str:
        """Upload PDF to S3 (optional).

        Args:
            pdf_buffer: BytesIO with PDF data.
            filename: Filename for S3.

        Returns:
            S3 URL.
        """
        import boto3

        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

        bucket = settings.AWS_S3_BUCKET
        key = f"invoices/{filename}"

        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=pdf_buffer.getvalue(),
            ContentType='application/pdf',
        )

        return f"https://{bucket}.s3.amazonaws.com/{key}"


pdf_service = InvoicePDFService()
