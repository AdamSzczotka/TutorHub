from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string

from .company_config import COMPANY_DETAILS
from .utils import amount_to_words, format_currency


class InvoicePDFService:
    """Service for generating invoice PDFs."""

    def _get_weasyprint(self):
        """Lazy import WeasyPrint to avoid import errors when GTK is not installed."""
        try:
            from weasyprint import CSS, HTML
            from weasyprint.text.fonts import FontConfiguration
            return CSS, HTML, FontConfiguration
        except (ImportError, OSError) as e:
            raise ImportError(
                "WeasyPrint is not available. Please install GTK libraries. "
                "See: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"
            ) from e

    def generate_pdf(self, invoice) -> BytesIO:
        """Generate PDF for invoice.

        Args:
            invoice: Invoice instance with related items.

        Returns:
            BytesIO buffer with PDF data.

        Raises:
            ImportError: If WeasyPrint is not installed.
        """
        CSS, HTML, FontConfiguration = self._get_weasyprint()

        # Prepare context
        context = {
            'invoice': invoice,
            'company': COMPANY_DETAILS,
            'amount_in_words': amount_to_words(invoice.total_amount),
            'format_currency': format_currency,
        }

        # Render HTML
        html_content = render_to_string('invoices/pdf/invoice.html', context)

        # CSS styling
        css = CSS(string=self._get_styles())

        # Generate PDF
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        pdf_buffer = BytesIO()
        html.write_pdf(pdf_buffer, stylesheets=[css], font_config=font_config)
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

    def _get_styles(self) -> str:
        """Get CSS styles for PDF.

        Returns:
            CSS string.
        """
        return '''
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: 'DejaVu Sans', sans-serif;
                font-size: 10pt;
                line-height: 1.4;
                color: #333;
            }
            .header {
                border-bottom: 2px solid #3B82F6;
                padding-bottom: 10px;
                margin-bottom: 20px;
            }
            .title {
                font-size: 24pt;
                font-weight: bold;
                color: #1F2937;
                margin: 0;
            }
            .invoice-number {
                font-size: 12pt;
                color: #6B7280;
                margin-top: 5px;
            }
            .parties {
                display: flex;
                justify-content: space-between;
                margin-bottom: 30px;
            }
            .party {
                width: 45%;
            }
            .party-title {
                font-size: 11pt;
                font-weight: bold;
                color: #1F2937;
                margin-bottom: 8px;
                border-bottom: 1px solid #E5E7EB;
                padding-bottom: 5px;
            }
            .party-info {
                font-size: 9pt;
                line-height: 1.6;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th {
                background-color: #3B82F6;
                color: white;
                padding: 10px 8px;
                text-align: left;
                font-size: 9pt;
                font-weight: bold;
            }
            td {
                padding: 10px 8px;
                border-bottom: 1px solid #E5E7EB;
                font-size: 9pt;
            }
            .text-right {
                text-align: right;
            }
            .summary {
                margin-top: 20px;
                text-align: right;
            }
            .summary-row {
                display: flex;
                justify-content: flex-end;
                margin-bottom: 5px;
            }
            .summary-label {
                width: 150px;
                text-align: left;
            }
            .summary-value {
                width: 120px;
                text-align: right;
                font-weight: bold;
            }
            .summary-total {
                border-top: 2px solid #1F2937;
                padding-top: 10px;
                margin-top: 10px;
                font-size: 14pt;
            }
            .amount-words {
                background-color: #F9FAFB;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }
            .payment-info {
                margin-top: 30px;
                padding: 15px;
                background-color: #EFF6FF;
                border-radius: 5px;
            }
            .payment-title {
                font-weight: bold;
                margin-bottom: 10px;
            }
            .footer {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                text-align: center;
                font-size: 8pt;
                color: #9CA3AF;
                border-top: 1px solid #E5E7EB;
                padding-top: 10px;
            }
        '''


pdf_service = InvoicePDFService()
