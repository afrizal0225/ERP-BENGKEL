from django.contrib import admin
from .models import (
    Warehouse, MaterialCategory, ProductCategory,
    RawMaterial, FinishedProduct, InventoryTransaction, StockAlert
)


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'location']


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']


@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'unit', 'current_stock', 'minimum_stock', 'stock_status', 'is_active']
    list_filter = ['category', 'unit', 'is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']

    def stock_status(self, obj):
        return obj.stock_status
    stock_status.short_description = 'Stock Status'


@admin.register(FinishedProduct)
class FinishedProductAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'size', 'color', 'current_stock', 'minimum_stock', 'stock_status', 'is_active']
    list_filter = ['category', 'size', 'color', 'is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']

    def stock_status(self, obj):
        return obj.stock_status
    stock_status.short_description = 'Stock Status'


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_type', 'material_name', 'quantity', 'unit_price', 'total_value', 'warehouse', 'created_by', 'created_at']
    list_filter = ['transaction_type', 'material_type', 'warehouse', 'created_at']
    search_fields = ['material_name', 'reference_number']
    readonly_fields = ['created_at', 'total_value']


@admin.register(StockAlert)
class StockAlertAdmin(admin.ModelAdmin):
    list_display = ['alert_type', 'material_name', 'current_stock', 'threshold', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'material_type', 'is_resolved', 'created_at']
    search_fields = ['material_name']
    readonly_fields = ['created_at']
