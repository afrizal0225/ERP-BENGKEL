from django.urls import path
from . import views

urlpatterns = [
    # Main purchase dashboard
    path('', views.purchase_list, name='purchase_list'),

    # Vendor URLs
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/create/', views.vendor_create, name='vendor_create'),
    path('vendors/<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('vendors/<int:pk>/update/', views.vendor_update, name='vendor_update'),
    path('vendors/<int:pk>/delete/', views.vendor_delete, name='vendor_delete'),

    # Purchase Order URLs
    path('orders/', views.purchase_order_list, name='purchase_order_list'),
    path('orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('orders/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('orders/<int:pk>/update/', views.purchase_order_update, name='purchase_order_update'),
    path('orders/<int:pk>/approve/', views.purchase_order_approve, name='purchase_order_approve'),
    path('orders/<int:pk>/delete/', views.purchase_order_delete, name='purchase_order_delete'),

    # Goods Receipt URLs
    path('receipts/', views.goods_receipt_list, name='goods_receipt_list'),
    path('receipts/create/', views.goods_receipt_create, name='goods_receipt_create'),
    path('receipts/<int:pk>/', views.goods_receipt_detail, name='goods_receipt_detail'),
    path('receipts/<int:pk>/update/', views.goods_receipt_update, name='goods_receipt_update'),

    # Vendor Performance URLs
    path('vendor-performance/', views.vendor_performance, name='vendor_performance'),

    # Reports URLs
    path('reports/', views.purchase_reports, name='purchase_reports'),
]