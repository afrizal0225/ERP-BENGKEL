from django.db import models
from django.contrib.auth.models import User


class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MaterialCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class RawMaterial(models.Model):
    UNIT_CHOICES = [
        ('kg', 'Kilogram'),
        ('m', 'Meter'),
        ('pcs', 'Pieces'),
        ('roll', 'Roll'),
        ('sheet', 'Sheet'),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(MaterialCategory, on_delete=models.CASCADE)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES)
    description = models.TextField(blank=True)
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def stock_status(self):
        if self.current_stock <= 0:
            return 'Out of Stock'
        elif self.current_stock <= self.minimum_stock:
            return 'Low Stock'
        else:
            return 'In Stock'

    @property
    def total_value(self):
        return self.unit_price * self.current_stock


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class FinishedProduct(models.Model):
    SIZE_CHOICES = [
        ('35', '35'),
        ('36', '36'),
        ('37', '37'),
        ('38', '38'),
        ('39', '39'),
        ('40', '40'),
        ('41', '41'),
        ('42', '42'),
        ('43', '43'),
        ('44', '44'),
        ('45', '45'),
    ]

    COLOR_CHOICES = [
        ('black', 'Black'),
        ('white', 'White'),
        ('brown', 'Brown'),
        ('blue', 'Blue'),
        ('red', 'Red'),
        ('green', 'Green'),
        ('yellow', 'Yellow'),
        ('gray', 'Gray'),
        ('navy', 'Navy'),
        ('beige', 'Beige'),
        ('sands', 'Sands'),
    ]

    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE)
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES)
    description = models.TextField(blank=True)
    current_stock = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name} ({self.size}, {self.color})"

    @property
    def stock_status(self):
        if self.current_stock <= 0:
            return 'Out of Stock'
        elif self.current_stock <= self.minimum_stock:
            return 'Low Stock'
        else:
            return 'In Stock'

    @property
    def total_value(self):
        return self.unit_price * self.current_stock

    @property
    def total_value(self):
        return self.unit_price * self.current_stock

    @property
    def total_value(self):
        return self.unit_price * self.current_stock


class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('IN', 'Stock In'),
        ('OUT', 'Stock Out'),
        ('ADJ', 'Adjustment'),
    ]

    MATERIAL_TYPES = [
        ('raw', 'Raw Material'),
        ('finished', 'Finished Product'),
    ]

    transaction_type = models.CharField(max_length=3, choices=TRANSACTION_TYPES)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPES)
    material_id = models.IntegerField()  # ID of RawMaterial or FinishedProduct
    material_name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reference_number = models.CharField(max_length=50, blank=True)  # PO number, SO number, etc.
    notes = models.TextField(blank=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.material_name} ({self.quantity})"

    def save(self, *args, **kwargs):
        self.total_value = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class StockAlert(models.Model):
    ALERT_TYPES = [
        ('low_stock', 'Low Stock Alert'),
        ('out_of_stock', 'Out of Stock Alert'),
        ('over_stock', 'Over Stock Alert'),
    ]

    MATERIAL_TYPES = [
        ('raw', 'Raw Material'),
        ('finished', 'Finished Product'),
    ]

    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPES)
    material_id = models.IntegerField()
    material_name = models.CharField(max_length=200)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2)
    threshold = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.alert_type} - {self.material_name}"
