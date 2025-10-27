from django.contrib import admin
from .models import (
    ProductionOrder, BillOfMaterials, BOMItem, WorkOrder,
    MaterialConsumption, ProductionProgress
)


class BOMItemInline(admin.TabularInline):
    model = BOMItem
    extra = 1
    fields = ['material', 'quantity', 'unit_cost']


@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(admin.ModelAdmin):
    list_display = ['product', 'version', 'is_active', 'total_cost', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at', 'created_by']
    search_fields = ['product__name', 'product__code']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [BOMItemInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('product', 'version', 'is_active')
        }),
        ('Cost Information', {
            'fields': ('total_cost', 'labor_cost', 'overhead_cost')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BOMItem)
class BOMItemAdmin(admin.ModelAdmin):
    list_display = ['bom', 'material', 'quantity', 'unit_cost', 'total_cost']
    list_filter = ['bom__product', 'material']
    search_fields = ['bom__product__name', 'material__name']
    readonly_fields = ['created_at']


class WorkOrderInline(admin.StackedInline):
    model = WorkOrder
    extra = 0
    readonly_fields = ['wo_number', 'created_at']
    fields = ['wo_number', 'stage', 'quantity', 'status', 'planned_start_date', 'planned_end_date', 'assigned_to']


@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'product', 'quantity', 'status', 'priority', 'planned_start_date', 'progress_percentage', 'created_by']
    list_filter = ['status', 'priority', 'planned_start_date', 'created_by']
    search_fields = ['po_number', 'product__name', 'product__code']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    inlines = [WorkOrderInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('po_number', 'product', 'quantity')
        }),
        ('Schedule', {
            'fields': ('planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date')
        }),
        ('Status & Approval', {
            'fields': ('status', 'priority', 'created_by', 'approved_by', 'approved_at')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class MaterialConsumptionInline(admin.TabularInline):
    model = MaterialConsumption
    extra = 0
    readonly_fields = ['created_at']
    fields = ['material', 'planned_quantity', 'actual_quantity', 'consumption_date', 'recorded_by']


class ProductionProgressInline(admin.TabularInline):
    model = ProductionProgress
    extra = 0
    readonly_fields = ['created_at']
    fields = ['progress_percentage', 'quantity_completed', 'progress_date', 'recorded_by', 'notes']


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ['wo_number', 'production_order', 'stage', 'quantity', 'status', 'assigned_to', 'planned_start_date']
    list_filter = ['status', 'stage', 'planned_start_date', 'assigned_to']
    search_fields = ['wo_number', 'production_order__po_number', 'production_order__product__name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [MaterialConsumptionInline, ProductionProgressInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('wo_number', 'production_order', 'stage', 'quantity')
        }),
        ('Schedule', {
            'fields': ('planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date')
        }),
        ('Assignment', {
            'fields': ('status', 'assigned_to', 'supervisor')
        }),
        ('Instructions', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(MaterialConsumption)
class MaterialConsumptionAdmin(admin.ModelAdmin):
    list_display = ['work_order', 'material', 'planned_quantity', 'actual_quantity', 'consumption_date', 'recorded_by']
    list_filter = ['consumption_date', 'recorded_by', 'material']
    search_fields = ['work_order__wo_number', 'material__name']
    readonly_fields = ['created_at']


@admin.register(ProductionProgress)
class ProductionProgressAdmin(admin.ModelAdmin):
    list_display = ['work_order', 'progress_percentage', 'quantity_completed', 'progress_date', 'recorded_by']
    list_filter = ['progress_date', 'recorded_by']
    search_fields = ['work_order__wo_number', 'work_order__production_order__po_number']
    readonly_fields = ['created_at']
