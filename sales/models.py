from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Customer(models.Model):
    """Customer model for managing customer information"""
    name = models.CharField(max_length=200, help_text="Customer full name or company name")
    email = models.EmailField(unique=True, help_text="Primary contact email")
    phone = models.CharField(max_length=20, blank=True, help_text="Contact phone number")
    address = models.TextField(blank=True, help_text="Customer address")
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Customer classification
    customer_type = models.CharField(
        max_length=20,
        choices=[
            ('retail', 'Retail Customer'),
            ('wholesale', 'Wholesale Customer'),
            ('distributor', 'Distributor'),
            ('online', 'Online Customer'),
        ],
        default='retail'
    )

    # Credit and payment info
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Credit limit in local currency")
    payment_terms = models.CharField(
        max_length=50,
        choices=[
            ('cod', 'Cash on Delivery'),
            ('net_15', 'Net 15 days'),
            ('net_30', 'Net 30 days'),
            ('net_60', 'Net 60 days'),
            ('net_90', 'Net 90 days'),
        ],
        default='cod'
    )

    # Status and metadata
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_customers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'

    def __str__(self):
        return f"{self.name} ({self.customer_type})"

    @property
    def total_orders(self):
        return self.sales_orders.count()

    @property
    def total_order_value(self):
        return self.sales_orders.aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')


class SalesOrder(models.Model):
    """Sales Order model for managing customer orders"""
    order_number = models.CharField(max_length=50, unique=True, help_text="Unique sales order number")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='sales_orders')

    # Order details
    order_date = models.DateField(default=timezone.now)
    required_date = models.DateField(help_text="Date when customer needs the order")
    ship_date = models.DateField(null=True, blank=True, help_text="Actual shipping date")

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
        ],
        default='draft'
    )

    # Financial details
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Shipping information
    shipping_address = models.TextField(blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)

    # Notes and metadata
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sales_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date', '-created_at']
        verbose_name = 'Sales Order'
        verbose_name_plural = 'Sales Orders'

    def __str__(self):
        return f"SO-{self.order_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        # Auto-generate order number if not provided
        if not self.order_number:
            self.order_number = f"SO-{timezone.now().strftime('%Y%m%d')}-{self.pk or '000'}"
        super().save(*args, **kwargs)

    @property
    def total_items(self):
        return self.items.count()


class SalesOrderItem(models.Model):
    """Individual items in a sales order"""
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('inventory.FinishedProduct', on_delete=models.CASCADE, related_name='sales_order_items')

    quantity = models.PositiveIntegerField(help_text="Ordered quantity")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per unit")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text="Discount percentage")

    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2, help_text="Total for this line item")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sales Order Item'
        verbose_name_plural = 'Sales Order Items'

    def __str__(self):
        return f"{self.product.name} - {self.quantity} units"

    def save(self, *args, **kwargs):
        # Calculate line total
        discount_amount = (self.unit_price * self.quantity) * (self.discount_percent / 100)
        self.line_total = (self.unit_price * self.quantity) - discount_amount
        super().save(*args, **kwargs)


class Invoice(models.Model):
    """Invoice model for billing customers"""
    invoice_number = models.CharField(max_length=50, unique=True)
    sales_order = models.OneToOneField(SalesOrder, on_delete=models.CASCADE, related_name='invoice')

    invoice_date = models.DateField(default=timezone.now)
    due_date = models.DateField(help_text="Payment due date")

    # Financial details (same as sales order)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Payment status
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('unpaid', 'Unpaid'),
            ('partial', 'Partially Paid'),
            ('paid', 'Paid'),
            ('overdue', 'Overdue'),
        ],
        default='unpaid'
    )

    # Payment details
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'Cash'),
            ('bank_transfer', 'Bank Transfer'),
            ('credit_card', 'Credit Card'),
            ('check', 'Check'),
        ],
        blank=True
    )

    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-invoice_date']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'

    def __str__(self):
        return f"INV-{self.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = f"INV-{timezone.now().strftime('%Y%m%d')}-{self.pk or '000'}"
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        return self.total_amount - self.amount_paid


class Payment(models.Model):
    """Payment records for invoices"""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(default=timezone.now)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('cash', 'Cash'),
            ('bank_transfer', 'Bank Transfer'),
            ('credit_card', 'Credit Card'),
            ('check', 'Check'),
        ]
    )
    reference_number = models.CharField(max_length=100, blank=True, help_text="Check number, transaction ID, etc.")
    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_payments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment of {self.amount} for {self.invoice}"


class ProductPricing(models.Model):
    """Product pricing management"""
    product = models.OneToOneField('inventory.FinishedProduct', on_delete=models.CASCADE, related_name='pricing')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Standard selling price")
    wholesale_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for wholesale customers")
    retail_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price for retail customers")

    # Pricing rules
    discount_eligible = models.BooleanField(default=True)
    max_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=20, help_text="Maximum discount allowed")

    # Seasonal pricing
    seasonal_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    seasonal_start_date = models.DateField(null=True, blank=True)
    seasonal_end_date = models.DateField(null=True, blank=True)

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='updated_pricing')

    class Meta:
        verbose_name = 'Product Pricing'
        verbose_name_plural = 'Product Pricing'

    def __str__(self):
        return f"Pricing for {self.product.name}"

    @property
    def current_price(self):
        """Return current applicable price based on date"""
        today = timezone.now().date()
        if (self.seasonal_price and
            self.seasonal_start_date and
            self.seasonal_end_date and
            self.seasonal_start_date <= today <= self.seasonal_end_date):
            return self.seasonal_price
        return self.base_price
