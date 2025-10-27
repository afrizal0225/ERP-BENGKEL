from django import forms
from django.forms import inlineformset_factory
from .models import Vendor, PurchaseOrder, PurchaseOrderLineItem, GoodsReceipt, GoodsReceiptLineItem


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'code', 'name', 'contact_person', 'email', 'phone', 'address',
            'payment_terms', 'credit_limit', 'is_active', 'notes'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'credit_limit': forms.NumberInput(attrs={'step': '0.01'}),
        }


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            'po_number', 'vendor', 'order_date', 'expected_delivery_date',
            'status', 'notes'
        ]
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default PO number if creating new
        if not self.instance.pk:
            # Generate PO number - you might want to customize this logic
            from django.utils import timezone
            self.fields['po_number'].initial = f"PO-{timezone.now().strftime('%Y%m%d')}-001"


class PurchaseOrderLineItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderLineItem
        fields = ['material_name', 'description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'quantity': forms.NumberInput(attrs={'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
        }


# Formset for PO line items
PurchaseOrderLineItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderLineItem,
    form=PurchaseOrderLineItemForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class GoodsReceiptForm(forms.ModelForm):
    class Meta:
        model = GoodsReceipt
        fields = [
            'gr_number', 'purchase_order', 'receipt_date',
            'quality_check_passed', 'quality_notes'
        ]
        widgets = {
            'receipt_date': forms.DateInput(attrs={'type': 'date'}),
            'quality_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter POs that are approved and not fully received
        self.fields['purchase_order'].queryset = PurchaseOrder.objects.filter(
            status__in=['approved', 'ordered', 'partially_received']
        ).exclude(
            line_items__isnull=True
        ).distinct()

        # Generate GR number if creating new
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['gr_number'].initial = f"GR-{timezone.now().strftime('%Y%m%d')}-001"


class GoodsReceiptLineItemForm(forms.ModelForm):
    class Meta:
        model = GoodsReceiptLineItem
        fields = ['purchase_order_item', 'received_quantity', 'unit_price', 'quality_status', 'notes']
        widgets = {
            'received_quantity': forms.NumberInput(attrs={'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        purchase_order = kwargs.pop('purchase_order', None)
        super().__init__(*args, **kwargs)

        if purchase_order:
            # Filter line items to only show those from the selected PO that aren't fully received
            self.fields['purchase_order_item'].queryset = PurchaseOrderLineItem.objects.filter(
                purchase_order=purchase_order
            ).exclude(
                received_quantity__gte=models.F('quantity')
            )


# Formset for GR line items
def get_goods_receipt_line_item_formset(purchase_order=None):
    return inlineformset_factory(
        GoodsReceipt,
        GoodsReceiptLineItem,
        form=GoodsReceiptLineItemForm,
        extra=0,
        can_delete=False,
        form_kwargs={'purchase_order': purchase_order} if purchase_order else {},
    )


class VendorPerformanceForm(forms.Form):
    """Form for updating vendor performance metrics"""
    vendor = forms.ModelChoiceField(
        queryset=Vendor.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    on_time_delivery = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    quality_rating = forms.DecimalField(
        max_digits=3,
        decimal_places=2,
        min_value=0,
        max_value=5,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )