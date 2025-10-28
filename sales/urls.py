from django.urls import path
from . import views

urlpatterns = [
    # Main sales dashboard
    path('', views.sales_list, name='sales_list'),

    # Customer URLs
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:pk>/update/', views.customer_update, name='customer_update'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),

    # Sales Order URLs
    path('orders/', views.sales_order_list, name='sales_order_list'),
    path('orders/create/', views.sales_order_create, name='sales_order_create'),
    path('orders/<int:pk>/', views.sales_order_detail, name='sales_order_detail'),
    path('orders/<int:pk>/update/', views.sales_order_update, name='sales_order_update'),
    path('orders/<int:pk>/update-status/', views.sales_order_update_status, name='sales_order_update_status'),
    path('orders/<int:pk>/delete/', views.sales_order_delete, name='sales_order_delete'),

    # Invoice URLs
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/<int:order_pk>/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/update/', views.invoice_update, name='invoice_update'),

    # Payment URLs
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/<int:invoice_pk>/', views.payment_create, name='payment_create'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),

    # Pricing URLs
    path('pricing/', views.product_pricing_list, name='product_pricing_list'),
    path('pricing/create/', views.product_pricing_create, name='product_pricing_create'),
    path('pricing/<int:pk>/update/', views.product_pricing_update, name='product_pricing_update'),

    # Bulk Operations
    path('bulk-process-orders/', views.bulk_process_orders, name='bulk_process_orders'),

    # Reports
    path('reports/', views.sales_reports, name='sales_reports'),
    path('reports/export/csv/', views.export_sales_report_csv, name='export_sales_report_csv'),
]