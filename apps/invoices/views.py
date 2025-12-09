from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView, ListView, TemplateView

from apps.core.mixins import AdminRequiredMixin, HTMXMixin

from .models import Invoice, InvoiceStatus
from .pdf_service import pdf_service
from .services import correction_service, invoice_service


class InvoiceListView(LoginRequiredMixin, HTMXMixin, ListView):
    """Display invoice list."""

    template_name = 'invoices/list.html'
    partial_template_name = 'invoices/partials/_invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.select_related('student')

        # Students see only their invoices
        if user.is_student:
            queryset = queryset.filter(student=user)

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by month
        month_year = self.request.GET.get('month_year')
        if month_year:
            queryset = queryset.filter(month_year=month_year)

        return queryset.order_by('-issue_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['statuses'] = InvoiceStatus.choices
        return context


class InvoiceDetailView(LoginRequiredMixin, HTMXMixin, DetailView):
    """Display invoice details."""

    template_name = 'invoices/detail.html'
    partial_template_name = 'invoices/partials/_invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        user = self.request.user
        queryset = Invoice.objects.select_related(
            'student', 'student__student_profile'
        ).prefetch_related('items', 'items__lesson', 'items__lesson__subject')

        if user.is_student:
            queryset = queryset.filter(student=user)

        return queryset


class DownloadInvoicePDFView(LoginRequiredMixin, View):
    """Download invoice PDF."""

    def get(self, request, pk):
        import traceback

        invoice = get_object_or_404(Invoice, id=pk)

        # Permission check
        if request.user.is_student and invoice.student != request.user:
            return HttpResponse("Brak uprawnień", status=403)

        # Get invoice with relations for PDF generation
        invoice = invoice_service.get_by_id(pk)

        try:
            # Generate PDF
            pdf_buffer = pdf_service.generate_pdf(invoice)

            filename = f"{invoice.invoice_number.replace('/', '-')}.pdf"

            return FileResponse(
                pdf_buffer,
                as_attachment=True,
                filename=filename,
                content_type='application/pdf',
            )
        except Exception as e:
            error_msg = f"Błąd generowania PDF: {str(e)}\n\n{traceback.format_exc()}"
            return HttpResponse(f"<pre>{error_msg}</pre>", status=500)


# Admin Views
class AdminInvoiceListView(LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, ListView):
    """Admin invoice list view."""

    template_name = 'admin_panel/invoices/list.html'
    partial_template_name = 'admin_panel/invoices/partials/_invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        queryset = Invoice.objects.select_related('student')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Filter by month
        month_year = self.request.GET.get('month_year')
        if month_year:
            queryset = queryset.filter(month_year=month_year)

        # Search by student name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                student__first_name__icontains=search
            ) | queryset.filter(student__last_name__icontains=search)

        return queryset.order_by('-issue_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', '')
        context['statuses'] = InvoiceStatus.choices
        return context


class AdminInvoiceCreateView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin view to create invoice."""

    template_name = 'admin_panel/invoices/create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from apps.accounts.models import User

        context['students'] = User.objects.filter(role='student', is_active=True)
        return context


class AdminCalculateInvoiceView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Calculate invoice items for student/month."""

    def get(self, request):
        from apps.accounts.models import User

        student_id = request.GET.get('student_id')
        month_year = request.GET.get('month_year')

        if not student_id or not month_year:
            return HttpResponse(
                '<div class="alert alert-error">Wybierz ucznia i miesiąc.</div>',
                status=400,
            )

        student = get_object_or_404(User, id=student_id, role='student')
        items = invoice_service.calculate_items_for_month(student, month_year)

        if not items:
            return HttpResponse(
                '<div class="alert alert-warning">'
                'Brak zajęć do zafakturowania w wybranym miesiącu.'
                '</div>'
            )

        totals = invoice_service.calculate_invoice_totals([
            invoice_service.calculate_item_total(item['quantity'], item['unit_price'])
            for item in items
        ])

        return render(
            request,
            'admin_panel/invoices/partials/_calculated_items.html',
            {
                'items': items,
                'totals': totals,
                'student': student,
                'month_year': month_year,
            },
        )


class AdminCreateInvoiceView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Create invoice from calculated items."""

    def post(self, request):
        from apps.accounts.models import User

        student_id = request.POST.get('student_id')
        month_year = request.POST.get('month_year')

        student = get_object_or_404(User, id=student_id)
        items = invoice_service.calculate_items_for_month(student, month_year)

        if not items:
            return HttpResponse(
                '<div class="alert alert-error">Brak pozycji do zafakturowania.</div>',
                status=400,
            )

        # Calculate due date (14 days from now)
        due_date = timezone.now().date() + timedelta(days=14)

        invoice = invoice_service.create_invoice(
            student=student,
            month_year=month_year,
            items=items,
            due_date=due_date,
        )

        return HttpResponse(
            f'<div class="alert alert-success">'
            f'Faktura {invoice.invoice_number} została utworzona.'
            f'</div>',
            headers={'HX-Trigger': 'invoiceCreated'},
        )


class AdminUpdateStatusView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Update invoice status."""

    def post(self, request, pk):
        invoice = get_object_or_404(Invoice, id=pk)
        status = request.POST.get('status')
        paid_date = request.POST.get('paid_date')

        if status == 'PAID' and paid_date:
            from datetime import datetime

            paid_date = datetime.strptime(paid_date, '%Y-%m-%d').date()
        else:
            paid_date = None

        invoice_service.update_status(pk, status, paid_date)

        return HttpResponse(
            '<div class="alert alert-success">Status faktury zaktualizowany.</div>',
            headers={'HX-Trigger': 'statusUpdated'},
        )


class AdminInvoiceDetailView(
    LoginRequiredMixin, AdminRequiredMixin, HTMXMixin, DetailView
):
    """Admin invoice detail view."""

    template_name = 'admin_panel/invoices/detail.html'
    partial_template_name = 'admin_panel/invoices/partials/_invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        return Invoice.objects.select_related(
            'student', 'student__student_profile'
        ).prefetch_related('items', 'items__lesson', 'items__lesson__subject')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuses'] = InvoiceStatus.choices
        return context


class AdminBillingDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin billing dashboard with statistics."""

    template_name = 'admin_panel/invoices/dashboard.html'

    def get_context_data(self, **kwargs):
        from django.db.models import Sum

        context = super().get_context_data(**kwargs)

        # Invoice statistics
        context['total_invoices'] = Invoice.objects.count()
        context['pending_count'] = Invoice.objects.filter(
            status__in=[InvoiceStatus.GENERATED, InvoiceStatus.SENT]
        ).count()
        context['paid_count'] = Invoice.objects.filter(
            status=InvoiceStatus.PAID
        ).count()
        context['overdue_count'] = Invoice.objects.filter(
            status=InvoiceStatus.OVERDUE
        ).count()

        # Total amounts - include GENERATED, SENT, and OVERDUE for outstanding
        context['total_outstanding'] = Invoice.objects.filter(
            status__in=[InvoiceStatus.GENERATED, InvoiceStatus.SENT, InvoiceStatus.OVERDUE]
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        context['total_paid'] = Invoice.objects.filter(
            status=InvoiceStatus.PAID
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        # Recent invoices
        context['recent_invoices'] = Invoice.objects.select_related(
            'student'
        ).order_by('-created_at')[:10]

        return context


class TriggerMonthlyBillingView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Manually trigger monthly billing."""

    def post(self, request):
        month_year = request.POST.get('month_year')

        if not month_year:
            return HttpResponse(
                '<div class="alert alert-error">Wybierz miesiąc.</div>',
                status=400
            )

        try:
            # Generate invoices synchronously
            from .services import billing_service
            results = billing_service.generate_monthly_invoices(month_year)

            success_count = len(results.get('success', []))
            failed_count = len(results.get('failed', []))
            skipped_count = len(results.get('skipped', []))

            if success_count > 0:
                msg = f'Wygenerowano {success_count} faktur za {month_year}.'
                if skipped_count > 0:
                    msg += f' Pominięto: {skipped_count}.'
                if failed_count > 0:
                    msg += f' Błędy: {failed_count}.'
                return HttpResponse(f'<div class="alert alert-success">{msg}</div>')
            elif skipped_count > 0:
                return HttpResponse(
                    f'''<div class="alert alert-warning">
                        Wszystkie faktury za {month_year} już istnieją lub brak lekcji ({skipped_count} pominiętych).
                    </div>'''
                )
            else:
                return HttpResponse(
                    f'''<div class="alert alert-info">
                        Brak aktywnych uczniów do zafakturowania za {month_year}.
                    </div>'''
                )
        except Exception as e:
            import traceback
            return HttpResponse(
                f'<div class="alert alert-error">Błąd: {str(e)}</div>',
                status=500
            )


class PaymentTrackerView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Admin view for payment tracking."""

    template_name = 'admin_panel/invoices/payment_tracker.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice_id = self.kwargs.get('pk')
        context['invoice'] = get_object_or_404(Invoice, id=invoice_id)
        return context


class MarkAsPaidView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Mark invoice as paid."""

    def post(self, request, pk):
        from datetime import datetime

        invoice = get_object_or_404(Invoice, id=pk)
        paid_date_str = request.POST.get('paid_date')

        if paid_date_str:
            paid_date = datetime.strptime(paid_date_str, '%Y-%m-%d').date()
        else:
            paid_date = timezone.now().date()

        invoice.status = InvoiceStatus.PAID
        invoice.paid_date = paid_date
        invoice.save()

        return HttpResponse(
            '''<div class="alert alert-success">
                Faktura została oznaczona jako opłacona.
            </div>''',
            headers={'HX-Trigger': 'invoiceUpdated'}
        )


class CreateCreditNoteView(LoginRequiredMixin, AdminRequiredMixin, View):
    """Create correction note for invoice."""

    def post(self, request, pk):
        from decimal import Decimal

        invoice = get_object_or_404(Invoice, id=pk)
        amount = request.POST.get('amount')
        reason = request.POST.get('reason')

        if not amount or not reason:
            return HttpResponse(
                '<div class="alert alert-error">Wypełnij wszystkie pola.</div>',
                status=400
            )

        try:
            amount = Decimal(amount)

            credit_note = correction_service.create_credit_note(
                invoice, amount, reason
            )

            return HttpResponse(
                f'''<div class="alert alert-success">
                    Nota korygująca {credit_note.invoice_number} została utworzona.
                </div>''',
                headers={'HX-Trigger': 'creditNoteCreated'}
            )
        except Exception as e:
            return HttpResponse(
                f'<div class="alert alert-error">{str(e)}</div>',
                status=400
            )
