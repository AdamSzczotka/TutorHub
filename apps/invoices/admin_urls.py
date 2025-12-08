from django.urls import path

from . import views

app_name = 'invoices'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.AdminBillingDashboardView.as_view(), name='dashboard'),
    path('trigger-billing/', views.TriggerMonthlyBillingView.as_view(), name='trigger_billing'),

    # Invoice list & create
    path('', views.AdminInvoiceListView.as_view(), name='list'),
    path('create/', views.AdminInvoiceCreateView.as_view(), name='create'),
    path('calculate/', views.AdminCalculateInvoiceView.as_view(), name='calculate'),
    path('create/submit/', views.AdminCreateInvoiceView.as_view(), name='create_submit'),

    # Invoice detail & actions
    path('<uuid:pk>/', views.AdminInvoiceDetailView.as_view(), name='detail'),
    path('<uuid:pk>/status/', views.AdminUpdateStatusView.as_view(), name='update_status'),
    path('<uuid:pk>/download/', views.DownloadInvoicePDFView.as_view(), name='download_pdf'),
    path('<uuid:pk>/payment/', views.PaymentTrackerView.as_view(), name='payment_tracker'),
    path('<uuid:pk>/mark-paid/', views.MarkAsPaidView.as_view(), name='mark_paid'),
    path('<uuid:pk>/credit-note/', views.CreateCreditNoteView.as_view(), name='create_credit_note'),
]
