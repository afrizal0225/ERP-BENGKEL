from django import forms
from django.forms import inlineformset_factory
from .models import Customer, SalesOrder, SalesOrderItem, Invoice, Payment, ProductPricing
from inventory.models import FinishedProduct


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'name', 'email', 'phone', 'address', 'city', 'state',
            'postal_code', 'country', 'customer_type', 'credit_limit',
            'payment_terms', 'is_active', 'notes'
        ]
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'credit_limit': forms.NumberInput(attrs={'step': '0.01'}),
        }


class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = [
            'customer', 'order_date', 'required_date', 'ship_date',
            'status', 'shipping_address', 'shipping_city', 'shipping_state',
            'shipping_postal_code', 'shipping_country', 'notes'
        ]
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'required_date': forms.DateInput(attrs={'type': 'date'}),
            'ship_date': forms.DateInput(attrs={'type': 'date'}),
            'shipping_address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class SalesOrderItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(
        queryset=FinishedProduct.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = SalesOrderItem
        fields = ['product', 'quantity', 'unit_price', 'discount_percent']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
            'discount_percent': forms.NumberInput(attrs={'step': '0.01', 'max': 100}),
        }


# Formset for sales order items
SalesOrderItemFormSet = inlineformset_factory(
    SalesOrder,
    SalesOrderItem,
    form=SalesOrderItemForm,
    extra=1,
    can_delete=True
)


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'sales_order', 'invoice_date', 'due_date', 'subtotal',
            'tax_amount', 'discount_amount', 'shipping_cost', 'total_amount',
            'payment_status', 'amount_paid', 'payment_date', 'payment_method', 'notes'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'subtotal': forms.NumberInput(attrs={'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'shipping_cost': forms.NumberInput(attrs={'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'amount_paid': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['invoice', 'payment_date', 'amount', 'payment_method', 'reference_number', 'notes']
        widgets = {
            'payment_date': forms.DateInput(attrs={'type': 'date'}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class ProductPricingForm(forms.ModelForm):
    class Meta:
        model = ProductPricing
        fields = [
            'product', 'base_price', 'wholesale_price', 'retail_price',
            'discount_eligible', 'max_discount_percent', 'seasonal_price',
            'seasonal_start_date', 'seasonal_end_date'
        ]
        widgets = {
            'base_price': forms.NumberInput(attrs={'step': '0.01'}),
            'wholesale_price': forms.NumberInput(attrs={'step': '0.01'}),
            'retail_price': forms.NumberInput(attrs={'step': '0.01'}),
            'max_discount_percent': forms.NumberInput(attrs={'step': '0.01', 'max': 100}),
            'seasonal_price': forms.NumberInput(attrs={'step': '0.01'}),
            'seasonal_start_date': forms.DateInput(attrs={'type': 'date'}),
            'seasonal_end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class SalesOrderStatusUpdateForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            ('confirmed', 'Confirmed'),
            ('processing', 'Processing'),
            ('shipped', 'Shipped'),
            ('delivered', 'Delivered'),
            ('cancelled', 'Cancelled'),
        ]
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text="Optional notes about the status change"
    )


class BulkOrderProcessingForm(forms.Form):
    orders = forms.ModelMultipleChoiceField(
        queryset=SalesOrder.objects.filter(status='confirmed'),
        widget=forms.CheckboxSelectMultiple,
        help_text="Select orders to process"
    )
    action = forms.ChoiceField(
        choices=[
            ('process', 'Mark as Processing'),
            ('ship', 'Mark as Shipped'),
            ('deliver', 'Mark as Delivered'),
        ]
    )