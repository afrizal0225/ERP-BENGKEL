from django.urls import path
from . import views

urlpatterns = [
    # Main manufacturing dashboard
    path('', views.manufacturing_list, name='manufacturing_list'),

    # Production Order URLs
    path('orders/', views.production_order_list, name='production_order_list'),
    path('orders/create/', views.production_order_create, name='production_order_create'),
    path('orders/<int:pk>/', views.production_order_detail, name='production_order_detail'),
    path('orders/<int:pk>/update/', views.production_order_update, name='production_order_update'),
    path('orders/<int:pk>/submit-approval/', views.production_order_submit_approval, name='production_order_submit_approval'),
    path('orders/<int:pk>/approve/', views.production_order_approve, name='production_order_approve'),
    path('orders/<int:pk>/cancel/', views.production_order_cancel, name='production_order_cancel'),
    path('orders/<int:pk>/delete/', views.production_order_delete, name='production_order_delete'),

    # Bill of Materials URLs
    path('boms/', views.bill_of_materials_list, name='bill_of_materials_list'),
    path('boms/create/', views.bill_of_materials_create, name='bill_of_materials_create'),
    path('boms/<int:pk>/', views.bill_of_materials_detail, name='bill_of_materials_detail'),
    path('boms/<int:pk>/update/', views.bill_of_materials_update, name='bill_of_materials_update'),
    path('boms/<int:pk>/delete/', views.bill_of_materials_delete, name='bill_of_materials_delete'),
    path('boms/bulk-import/', views.bom_bulk_import, name='bom_bulk_import'),
    path('boms/download-template/', views.download_bom_template, name='download_bom_template'),

    # Work Order URLs
    path('work-orders/', views.work_order_list, name='work_order_list'),
    path('work-orders/<int:pk>/', views.work_order_detail, name='work_order_detail'),
    path('work-orders/<int:pk>/cancel/', views.work_order_cancel, name='work_order_cancel'),
    path('generate-work-orders/', views.generate_work_orders, name='generate_work_orders'),

    # Material Consumption and Progress URLs
    path('work-orders/<int:wo_pk>/record-consumption/', views.record_material_consumption, name='record_material_consumption'),
    path('work-orders/<int:wo_pk>/record-progress/', views.record_production_progress, name='record_production_progress'),

    # Reports URLs
    path('reports/', views.manufacturing_reports, name='manufacturing_reports'),

    # API URLs
    path('api/material-price/<int:material_id>/', views.get_material_price, name='get_material_price'),
]