from django.contrib import admin
from .models import Customer, SalesOrder, SalesOrderItem, Invoice, Payment, ProductPricing


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'customer_type', 'is_active', 'total_orders', 'total_order_value']
    list_filter = ['customer_type', 'is_active', 'created_at']
    search_fields = ['name', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at', 'total_orders', 'total_order_value']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Customer Classification', {
            'fields': ('customer_type', 'credit_limit', 'payment_terms')
        }),
        ('Status & Notes', {
            'fields': ('is_active', 'notes', 'created_by')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 0
    readonly_fields = ['line_total']


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'status', 'order_date', 'total_amount', 'created_by']
    list_filter = ['status', 'order_date', 'customer__customer_type']
    search_fields = ['order_number', 'customer__name', 'customer__email']
    readonly_fields = ['created_at', 'updated_at', 'subtotal', 'total_amount']
    inlines = [SalesOrderItemInline]
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'status')
        }),
        ('Dates', {
            'fields': ('order_date', 'required_date', 'ship_date')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'shipping_cost', 'total_amount'),
            'classes': ('collapse',)
        }),
        ('Shipping Information', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_state', 'shipping_postal_code', 'shipping_country'),
            'classes': ('collapse',)
        }),
        ('Notes & Metadata', {
            'fields': ('notes', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    list_display = ['sales_order', 'product', 'quantity', 'unit_price', 'line_total']
    list_filter = ['sales_order__status', 'product__category']
    search_fields = ['sales_order__order_number', 'product__name']
    readonly_fields = ['line_total']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'sales_order', 'invoice_date', 'total_amount', 'payment_status', 'balance_due']
    list_filter = ['payment_status', 'invoice_date']
    search_fields = ['invoice_number', 'sales_order__order_number', 'sales_order__customer__name']
    readonly_fields = ['created_at', 'balance_due']
    inlines = [PaymentInline]
    fieldsets = (
        ('Invoice Information', {
            'fields': ('invoice_number', 'sales_order', 'invoice_date', 'due_date')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'tax_amount', 'discount_amount', 'shipping_cost', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('payment_status', 'amount_paid', 'payment_date', 'payment_method')
        }),
        ('Notes & Metadata', {
            'fields': ('notes', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'payment_date', 'amount', 'payment_method', 'created_by']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['invoice__invoice_number', 'reference_number']
    readonly_fields = ['created_at']


@admin.register(ProductPricing)
class ProductPricingAdmin(admin.ModelAdmin):
    list_display = ['product', 'base_price', 'wholesale_price', 'retail_price', 'current_price', 'last_updated']
    list_filter = ['discount_eligible', 'last_updated']
    search_fields = ['product__name', 'product__code']
    readonly_fields = ['last_updated', 'current_price']
    fieldsets = (
        ('Product Information', {
            'fields': ('product',)
        }),
        ('Pricing', {
            'fields': ('base_price', 'wholesale_price', 'retail_price')
        }),
        ('Discount Settings', {
            'fields': ('discount_eligible', 'max_discount_percent')
        }),
        ('Seasonal Pricing', {
            'fields': ('seasonal_price', 'seasonal_start_date', 'seasonal_end_date'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('last_updated', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
