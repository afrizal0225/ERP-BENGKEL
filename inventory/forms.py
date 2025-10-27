from django import forms
from .models import (
    Warehouse, MaterialCategory, ProductCategory,
    RawMaterial, FinishedProduct, InventoryTransaction
)


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['name', 'location', 'description', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class MaterialCategoryForm(forms.ModelForm):
    class Meta:
        model = MaterialCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class RawMaterialForm(forms.ModelForm):
    class Meta:
        model = RawMaterial
        fields = [
            'code', 'name', 'category', 'unit', 'description',
            'minimum_stock', 'current_stock', 'unit_price', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
        }


class FinishedProductForm(forms.ModelForm):
    class Meta:
        model = FinishedProduct
        fields = [
            'code', 'name', 'category', 'size', 'color', 'description',
            'current_stock', 'minimum_stock', 'unit_price', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
        }


class InventoryTransactionForm(forms.ModelForm):
    class Meta:
        model = InventoryTransaction
        fields = [
            'transaction_type', 'material_type', 'material_id', 'material_name',
            'quantity', 'unit_price', 'reference_number', 'notes', 'warehouse'
        ]
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make material_id and material_name readonly if editing existing transaction
        if self.instance.pk:
            self.fields['material_id'].disabled = True
            self.fields['material_name'].disabled = True


class StockAdjustmentForm(forms.Form):
    material_type = forms.ChoiceField(
        choices=[('raw', 'Raw Material'), ('finished', 'Finished Product')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    material_id = forms.IntegerField(widget=forms.HiddenInput())
    material_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': True})
    )
    adjustment_type = forms.ChoiceField(
        choices=[('add', 'Add Stock'), ('subtract', 'Subtract Stock')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )
    reason = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )