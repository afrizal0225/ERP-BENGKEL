from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from inventory.models import RawMaterial, FinishedProduct


class ProductionOrder(models.Model):
    """Model for production orders (PO) - different from purchase orders"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    po_number = models.CharField(max_length=20, unique=True, help_text="Production order number")
    product = models.ForeignKey(FinishedProduct, on_delete=models.CASCADE, related_name='production_orders')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity to produce")

    planned_start_date = models.DateField(help_text="Planned production start date")
    planned_end_date = models.DateField(help_text="Planned production completion date")
    actual_start_date = models.DateField(null=True, blank=True, help_text="Actual production start date")
    actual_end_date = models.DateField(null=True, blank=True, help_text="Actual production completion date")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    # Approval workflow
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_production_orders')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_production_orders')
    approved_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True, help_text="Additional notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-planned_start_date', '-created_at']
        verbose_name = 'Production Order'
        verbose_name_plural = 'Production Orders'

    def __str__(self):
        return f"PO-{self.po_number} - {self.product.name}"

    @property
    def progress_percentage(self):
        """Calculate production progress percentage"""
        if self.status == 'completed':
            return 100
        elif self.status == 'in_progress':
            # Calculate based on work orders progress
            work_orders = self.work_orders.all()
            if work_orders.exists():
                completed_orders = work_orders.filter(status='completed').count()
                return round((completed_orders / work_orders.count()) * 100, 2)
        return 0

    @property
    def is_overdue(self):
        """Check if production order is overdue"""
        if self.planned_end_date and self.status in ['approved', 'in_progress']:
            return timezone.now().date() > self.planned_end_date
        return False


class BillOfMaterials(models.Model):
    """Bill of Materials for each product"""
    product = models.OneToOneField(FinishedProduct, on_delete=models.CASCADE, related_name='bill_of_materials')
    version = models.CharField(max_length=10, default='1.0', help_text="BOM version")
    is_active = models.BooleanField(default=True, help_text="Whether this BOM version is active")

    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Total material cost")
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Estimated labor cost")
    overhead_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Overhead cost")

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_boms')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-version']
        verbose_name = 'Bill of Materials'
        verbose_name_plural = 'Bills of Materials'

    def __str__(self):
        return f"BOM for {self.product.name} v{self.version}"

    def calculate_total_cost(self):
        """Calculate total material cost from BOM items"""
        total = self.items.aggregate(
            total=models.Sum(models.F('quantity') * models.F('material__unit_price'))
        )['total'] or Decimal('0')
        self.total_cost = total
        self.save(update_fields=['total_cost'])
        return total


class BOMItem(models.Model):
    """Individual items in a Bill of Materials"""
    STAGE_CHOICES = [
        ('gurat', 'Gurat (Cutting)'),
        ('assembly', 'Assembly'),
        ('press', 'Press'),
        ('finishing', 'Finishing'),
    ]

    bom = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='items')
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, related_name='bom_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity required per unit of finished product")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, help_text="BOM Cost (auto-calculated)", editable=False)

    # Stage allocation - which production stages use this material
    allocated_stages = models.JSONField(default=list, help_text="List of production stages that use this material")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['material__name']
        verbose_name = 'BOM Item'
        verbose_name_plural = 'BOM Items'

    def __str__(self):
        stages = ', '.join([stage.title() for stage in self.allocated_stages]) if self.allocated_stages else 'No stages'
        return f"{self.material.name} - {self.quantity} {self.material.unit} ({stages})"

    def save(self, *args, **kwargs):
        """Auto-calculate unit_cost as quantity * material.unit_price"""
        if self.material:
            self.unit_cost = self.quantity * self.material.unit_price
        super().save(*args, **kwargs)

    @property
    def total_cost(self):
        """Calculate total cost for this BOM item"""
        return self.quantity * self.unit_cost

    def get_allocated_stages_display(self):
        """Return human-readable stage names"""
        stage_names = {
            'gurat': 'Gurat (Cutting)',
            'assembly': 'Assembly',
            'press': 'Press',
            'finishing': 'Finishing'
        }
        return [stage_names.get(stage, stage) for stage in self.allocated_stages]


class WorkOrder(models.Model):
    """Work Orders (SPK) generated from approved Production Orders"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]

    STAGE_CHOICES = [
        ('gurat', 'Gurat (Cutting)'),
        ('assembly', 'Assembly'),
        ('press', 'Press'),
        ('finishing', 'Finishing'),
    ]

    wo_number = models.CharField(max_length=20, unique=True, help_text="Work order number")
    production_order = models.ForeignKey(ProductionOrder, on_delete=models.CASCADE, related_name='work_orders')
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, help_text="Production stage")

    quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity for this work order")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    planned_start_date = models.DateField(help_text="Planned start date for this stage")
    planned_end_date = models.DateField(help_text="Planned completion date for this stage")
    actual_start_date = models.DateField(null=True, blank=True, help_text="Actual start date")
    actual_end_date = models.DateField(null=True, blank=True, help_text="Actual completion date")

    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_work_orders')
    supervisor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='supervised_work_orders')

    notes = models.TextField(blank=True, help_text="Work instructions and notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['production_order', 'stage']
        verbose_name = 'Work Order'
        verbose_name_plural = 'Work Orders'

    def __str__(self):
        return f"WO-{self.wo_number} - {self.production_order.product.name} ({self.get_stage_display()})"

    @property
    def progress_percentage(self):
        """Calculate progress percentage from latest progress entry"""
        latest_progress = self.progress_entries.first()
        if latest_progress:
            return latest_progress.progress_percentage
        return 0


class MaterialConsumption(models.Model):
    """Track material consumption during production"""
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='material_consumptions')
    material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, related_name='consumptions')
    planned_quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Planned quantity to consume")
    actual_quantity = models.DecimalField(max_digits=10, decimal_places=2, help_text="Actual quantity consumed")

    consumption_date = models.DateTimeField(default=timezone.now, help_text="Date of consumption")
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='material_consumptions')

    notes = models.TextField(blank=True, help_text="Consumption notes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-consumption_date']
        verbose_name = 'Material Consumption'
        verbose_name_plural = 'Material Consumptions'

    def __str__(self):
        return f"{self.material.name} - {self.actual_quantity} consumed"

    def save(self, *args, **kwargs):
        """Update inventory when material is consumed"""
        super().save(*args, **kwargs)
        # Reduce inventory stock
        self.material.current_stock -= self.actual_quantity
        self.material.save(update_fields=['current_stock'])


class ProductionProgress(models.Model):
    """Track progress of each work order"""
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='progress_entries')
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Progress percentage (0-100)")
    quantity_completed = models.DecimalField(max_digits=10, decimal_places=2, help_text="Quantity completed")

    progress_date = models.DateTimeField(default=timezone.now, help_text="Date of progress update")
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_entries')

    notes = models.TextField(blank=True, help_text="Progress notes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-progress_date']
        verbose_name = 'Production Progress'
        verbose_name_plural = 'Production Progress'

    def __str__(self):
        return f"{self.work_order.wo_number} - {self.progress_percentage}% complete"

    def save(self, *args, **kwargs):
        """Update work order status based on progress"""
        super().save(*args, **kwargs)

        # Update work order status if 100% complete
        if self.progress_percentage >= 100:
            self.work_order.status = 'completed'
            self.work_order.actual_end_date = self.progress_date.date()
            self.work_order.save(update_fields=['status', 'actual_end_date'])

            # Check if all work orders for production order are complete
            production_order = self.work_order.production_order
            all_complete = production_order.work_orders.filter(status='completed').count() == production_order.work_orders.count()
            if all_complete:
                production_order.status = 'completed'
                production_order.actual_end_date = self.progress_date.date()
                production_order.save(update_fields=['status', 'actual_end_date'])
