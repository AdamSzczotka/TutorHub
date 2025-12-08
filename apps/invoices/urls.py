from django.urls import path

from . import views

app_name = 'invoices'

urlpatterns = [
    # Student/general views
    path('', views.InvoiceListView.as_view(), name='list'),
    path('<uuid:pk>/', views.InvoiceDetailView.as_view(), name='detail'),
    path('<uuid:pk>/download/', views.DownloadInvoicePDFView.as_view(), name='download_pdf'),
]
