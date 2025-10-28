from django.urls import path
from . import views

urlpatterns = [
    # Main inventory dashboard
    path('', views.inventory_list, name='inventory_list'),

    # Warehouse URLs
    path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('warehouses/create/', views.warehouse_create, name='warehouse_create'),
    path('warehouses/<int:pk>/update/', views.warehouse_update, name='warehouse_update'),
    path('warehouses/<int:pk>/delete/', views.warehouse_delete, name='warehouse_delete'),

    # Raw Material URLs
    path('raw-materials/', views.raw_material_list, name='raw_material_list'),
    path('raw-materials/create/', views.raw_material_create, name='raw_material_create'),
    path('raw-materials/<int:pk>/update/', views.raw_material_update, name='raw_material_update'),
    path('raw-materials/<int:pk>/delete/', views.raw_material_delete, name='raw_material_delete'),

    # Finished Product URLs
    path('finished-products/', views.finished_product_list, name='finished_product_list'),
    path('finished-products/create/', views.finished_product_create, name='finished_product_create'),
    path('finished-products/<int:pk>/update/', views.finished_product_update, name='finished_product_update'),
    path('finished-products/<int:pk>/delete/', views.finished_product_delete, name='finished_product_delete'),

    # Stock Management URLs
    path('stock-adjustment/', views.stock_adjustment, name='stock_adjustment'),
    path('get-material-details/', views.get_material_details, name='get_material_details'),

    # Transaction History URLs
    path('transactions/', views.transaction_list, name='transaction_list'),

    # Stock Alert URLs
    path('stock-alerts/', views.stock_alert_list, name='stock_alert_list'),

    # Bulk Import URLs
    path('raw-materials/bulk-import/', views.bulk_import_raw_materials, name='bulk_import_raw_materials'),
    path('finished-products/bulk-import/', views.bulk_import_finished_products, name='bulk_import_finished_products'),
    path('raw-materials/template/', views.download_raw_material_template, name='download_raw_material_template'),
    path('finished-products/template/', views.download_finished_product_template, name='download_finished_product_template'),
]
