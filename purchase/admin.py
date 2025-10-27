from django.contrib import admin
from .models import Vendor, PurchaseOrder, PurchaseOrderLineItem, GoodsReceipt, GoodsReceiptLineItem


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'contact_person', 'email', 'phone', 'is_active', 'on_time_delivery_rate', 'quality_rating']
    list_filter = ['is_active', 'created_at']
    search_fields = ['code', 'name', 'contact_person', 'email']
    readonly_fields = ['total_orders', 'on_time_deliveries', 'created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'contact_person', 'email', 'phone', 'address')
        }),
        ('Financial Information', {
            'fields': ('payment_terms', 'credit_limit')
        }),
        ('Performance Tracking', {
            'fields': ('total_orders', 'on_time_deliveries', 'quality_rating'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class PurchaseOrderLineItemInline(admin.TabularInline):
    model = PurchaseOrderLineItem
    extra = 0
    readonly_fields = ['total_price']
    fields = ['material_name', 'description', 'quantity', 'unit_price', 'received_quantity', 'total_price']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'vendor', 'order_date', 'status', 'total_amount', 'expected_delivery_date', 'is_overdue', 'created_by']
    list_filter = ['status', 'order_date', 'expected_delivery_date', 'vendor', 'created_by']
    search_fields = ['po_number', 'vendor__name', 'vendor__code']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    inlines = [PurchaseOrderLineItemInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('po_number', 'vendor', 'order_date', 'expected_delivery_date', 'actual_delivery_date')
        }),
        ('Status & Approval', {
            'fields': ('status', 'created_by', 'approved_by', 'approved_at')
        }),
        ('Financial', {
            'fields': ('total_amount',)
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

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('vendor', 'created_by', 'approved_by')


class GoodsReceiptLineItemInline(admin.TabularInline):
    model = GoodsReceiptLineItem
    extra = 0
    readonly_fields = ['total_value']
    fields = ['purchase_order_item', 'received_quantity', 'unit_price', 'quality_status', 'total_value', 'notes']


@admin.register(GoodsReceipt)
class GoodsReceiptAdmin(admin.ModelAdmin):
    list_display = ['gr_number', 'purchase_order', 'receipt_date', 'received_by', 'total_received_value', 'quality_check_passed']
    list_filter = ['receipt_date', 'quality_check_passed', 'received_by']
    search_fields = ['gr_number', 'purchase_order__po_number', 'purchase_order__vendor__name']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [GoodsReceiptLineItemInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('gr_number', 'purchase_order', 'receipt_date', 'received_by')
        }),
        ('Quality Control', {
            'fields': ('quality_check_passed', 'quality_notes')
        }),
        ('Financial', {
            'fields': ('total_received_value',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PurchaseOrderLineItem)
class PurchaseOrderLineItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'material_name', 'quantity', 'unit_price', 'received_quantity', 'remaining_quantity', 'is_fully_received']
    list_filter = ['purchase_order__status', 'purchase_order__vendor']
    search_fields = ['material_name', 'purchase_order__po_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(GoodsReceiptLineItem)
class GoodsReceiptLineItemAdmin(admin.ModelAdmin):
    list_display = ['goods_receipt', 'purchase_order_item', 'received_quantity', 'unit_price', 'quality_status', 'total_value']
    list_filter = ['quality_status', 'goods_receipt__receipt_date']
    search_fields = ['goods_receipt__gr_number', 'purchase_order_item__material_name']
    readonly_fields = ['created_at']
