from django import forms
from django.forms import inlineformset_factory
from .models import (
    ProductionOrder, BillOfMaterials, BOMItem, WorkOrder,
    MaterialConsumption, ProductionProgress
)
from inventory.models import FinishedProduct, RawMaterial


class ProductionOrderForm(forms.ModelForm):
    class Meta:
        model = ProductionOrder
        fields = [
            'po_number', 'product', 'quantity', 'planned_start_date',
            'planned_end_date', 'priority', 'notes'
        ]
        widgets = {
            'planned_start_date': forms.DateInput(attrs={'type': 'date'}),
            'planned_end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate PO number if creating new
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['po_number'].initial = f"PRO-{timezone.now().strftime('%Y%m%d')}-001"


class BillOfMaterialsForm(forms.ModelForm):
    class Meta:
        model = BillOfMaterials
        fields = ['product', 'version', 'labor_cost', 'overhead_cost', 'is_active']
        widgets = {
            'labor_cost': forms.NumberInput(attrs={'step': '0.01'}),
            'overhead_cost': forms.NumberInput(attrs={'step': '0.01'}),
        }


class BOMItemForm(forms.ModelForm):
    class Meta:
        model = BOMItem
        fields = ['material', 'quantity', 'unit_cost']  # Add 'unit_cost' to fields
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01'}),
            'unit_cost': forms.NumberInput(attrs={'step': '0.01'}),  # Add widget for unit_cost
        }


# Formset for BOM items
BOMItemFormSet = inlineformset_factory(
    BillOfMaterials,
    BOMItem,
    form=BOMItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class WorkOrderForm(forms.ModelForm):
    class Meta:
        model = WorkOrder
        fields = [
            'wo_number', 'production_order', 'stage', 'quantity',
            'planned_start_date', 'planned_end_date', 'assigned_to',
            'supervisor', 'notes'
        ]
        widgets = {
            'planned_start_date': forms.DateInput(attrs={'type': 'date'}),
            'planned_end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate WO number if creating new
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['wo_number'].initial = f"WO-{timezone.now().strftime('%Y%m%d')}-001"


class MaterialConsumptionForm(forms.ModelForm):
    class Meta:
        model = MaterialConsumption
        fields = ['material', 'planned_quantity', 'actual_quantity', 'notes']
        widgets = {
            'planned_quantity': forms.NumberInput(attrs={'step': '0.01'}),
            'actual_quantity': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        work_order = kwargs.pop('work_order', None)
        super().__init__(*args, **kwargs)

        if work_order:
            # Filter materials to those in the BOM for this production order
            try:
                bom = work_order.production_order.product.bill_of_materials.filter(is_active=True).first()
                if bom:
                    material_ids = bom.items.values_list('material_id', flat=True)
                    self.fields['material'].queryset = RawMaterial.objects.filter(id__in=material_ids)
            except AttributeError:
                # If bill_of_materials is a single object (OneToOneField), not a manager
                bom = work_order.production_order.product.bill_of_materials
                if bom and bom.is_active:
                    material_ids = bom.items.values_list('material_id', flat=True)
                    self.fields['material'].queryset = RawMaterial.objects.filter(id__in=material_ids)


class ProductionProgressForm(forms.ModelForm):
    class Meta:
        model = ProductionProgress
        fields = ['progress_percentage', 'quantity_completed', 'notes']
        widgets = {
            'progress_percentage': forms.NumberInput(attrs={'min': '0', 'max': '100', 'step': '0.01'}),
            'quantity_completed': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }


class BulkWorkOrderGenerationForm(forms.Form):
    """Form for generating work orders from approved production order"""
    production_order = forms.ModelChoiceField(
        queryset=ProductionOrder.objects.filter(status='approved'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Stage-specific settings
    gurat_quantity = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Quantity for Gurat'})
    )
    assembly_quantity = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Quantity for Assembly'})
    )
    press_quantity = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Quantity for Press'})
    )
    finishing_quantity = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Quantity for Finishing'})
    )

    planned_start_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    duration_days = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    def clean(self):
        cleaned_data = super().clean()
        po = cleaned_data.get('production_order')

        if po:
            total_quantity = sum([
                cleaned_data.get('gurat_quantity', 0),
                cleaned_data.get('assembly_quantity', 0),
                cleaned_data.get('press_quantity', 0),
                cleaned_data.get('finishing_quantity', 0)
            ])

            if total_quantity != po.quantity:
                raise forms.ValidationError(
                    f"Total work order quantities ({total_quantity}) must equal production order quantity ({po.quantity})"
                )

        return cleaned_data