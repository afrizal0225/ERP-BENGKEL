from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Vendor(models.Model):
    """Model for managing suppliers/vendors"""
    code = models.CharField(max_length=20, unique=True, help_text="Unique vendor code")
    name = models.CharField(max_length=200, help_text="Vendor company name")
    contact_person = models.CharField(max_length=100, blank=True, help_text="Primary contact person")
    email = models.EmailField(blank=True, help_text="Contact email")
    phone = models.CharField(max_length=20, blank=True, help_text="Contact phone number")
    address = models.TextField(blank=True, help_text="Vendor address")
    payment_terms = models.CharField(max_length=100, blank=True, help_text="Payment terms (e.g., Net 30, COD)")
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Credit limit in local currency")

    # Performance tracking
    total_orders = models.PositiveIntegerField(default=0, help_text="Total number of orders")
    on_time_deliveries = models.PositiveIntegerField(default=0, help_text="Number of on-time deliveries")
    quality_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0, help_text="Average quality rating (0-5)")

    is_active = models.BooleanField(default=True, help_text="Whether vendor is active")
    notes = models.TextField(blank=True, help_text="Additional notes")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def on_time_delivery_rate(self):
        """Calculate on-time delivery rate as percentage"""
        if self.total_orders == 0:
            return 0
        return round((self.on_time_deliveries / self.total_orders) * 100, 2)


class PurchaseOrder(models.Model):
    """Model for purchase orders"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('ordered', 'Ordered'),
        ('partially_received', 'Partially Received'),
        ('received', 'Fully Received'),
        ('cancelled', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=20, unique=True, help_text="Purchase order number")
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='purchase_orders')
    order_date = models.DateField(default=timezone.now, help_text="Date when PO was created")
    expected_delivery_date = models.DateField(null=True, blank=True, help_text="Expected delivery date")
    actual_delivery_date = models.DateField(null=True, blank=True, help_text="Actual delivery date")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total PO amount")

    # Approval workflow
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_purchase_orders')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_purchase_orders')
    approved_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date', '-created_at']
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'

    def __str__(self):
        return f"PO-{self.po_number} - {self.vendor.name}"

    def calculate_total(self):
        """Calculate total amount from line items"""
        total = self.line_items.aggregate(
            total=models.Sum(models.F('quantity') * models.F('unit_price'))
        )['total'] or Decimal('0')
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total

    @property
    def is_overdue(self):
        """Check if PO is overdue"""
        if self.expected_delivery_date and self.status in ['approved', 'ordered', 'partially_received']:
            return timezone.now().date() > self.expected_delivery_date
        return False


class PurchaseOrderLineItem(models.Model):
    """Line items for purchase orders"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='line_items')
    material_name = models.CharField(max_length=200, help_text="Name of the material/item")
    description = models.TextField(blank=True, help_text="Item description")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Ordered quantity")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit")
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Quantity received so far")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Purchase Order Line Item'
        verbose_name_plural = 'Purchase Order Line Items'

    def __str__(self):
        return f"{self.material_name} - {self.quantity} units"

    @property
    def total_price(self):
        """Calculate total price for this line item"""
        return self.quantity * self.unit_price

    @property
    def remaining_quantity(self):
        """Calculate remaining quantity to be received"""
        return self.quantity - self.received_quantity

    @property
    def is_fully_received(self):
        """Check if line item is fully received"""
        return self.received_quantity >= self.quantity


class GoodsReceipt(models.Model):
    """Model for goods receipt notes"""
    gr_number = models.CharField(max_length=20, unique=True, help_text="Goods receipt number")
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='goods_receipts')
    receipt_date = models.DateField(default=timezone.now, help_text="Date of goods receipt")
    received_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goods_receipts')

    total_received_value = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total value of received goods")
    quality_check_passed = models.BooleanField(default=True, help_text="Whether quality check passed")
    quality_notes = models.TextField(blank=True, help_text="Quality inspection notes")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-receipt_date', '-created_at']
        verbose_name = 'Goods Receipt'
        verbose_name_plural = 'Goods Receipts'

    def __str__(self):
        return f"GR-{self.gr_number} - {self.purchase_order.po_number}"

    def calculate_total(self):
        """Calculate total received value"""
        total = self.line_items.aggregate(
            total=models.Sum(models.F('received_quantity') * models.F('unit_price'))
        )['total'] or Decimal('0')
        self.total_received_value = total
        self.save(update_fields=['total_received_value'])
        return total


class GoodsReceiptLineItem(models.Model):
    """Line items for goods receipts"""
    goods_receipt = models.ForeignKey(GoodsReceipt, on_delete=models.CASCADE, related_name='line_items')
    purchase_order_item = models.ForeignKey(PurchaseOrderLineItem, on_delete=models.CASCADE, related_name='receipt_items')
    received_quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity received")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Unit price at time of receipt")
    quality_status = models.CharField(max_length=20, choices=[
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending Inspection')
    ], default='accepted')

    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Goods Receipt Line Item'
        verbose_name_plural = 'Goods Receipt Line Items'

    def __str__(self):
        return f"{self.purchase_order_item.material_name} - {self.received_quantity} units"

    @property
    def total_value(self):
        """Calculate total value for this line item"""
        return self.received_quantity * self.unit_price

    def save(self, *args, **kwargs):
        """Update the purchase order line item received quantity"""
        super().save(*args, **kwargs)
        if self.quality_status == 'accepted':
            # Update the PO line item received quantity
            self.purchase_order_item.received_quantity += self.received_quantity
            self.purchase_order_item.save(update_fields=['received_quantity'])
