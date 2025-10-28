from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
import csv
from decimal import Decimal
from .models import Customer, SalesOrder, SalesOrderItem, Invoice, Payment, ProductPricing
from .forms import (
    CustomerForm, SalesOrderForm, SalesOrderItemFormSet, InvoiceForm,
    PaymentForm, ProductPricingForm, SalesOrderStatusUpdateForm, BulkOrderProcessingForm
)
from inventory.models import FinishedProduct


@login_required
def sales_list(request):
    """Main sales dashboard view"""
    # Get summary statistics
    total_customers = Customer.objects.filter(is_active=True).count()
    total_orders = SalesOrder.objects.count()
    pending_orders = SalesOrder.objects.filter(status__in=['draft', 'confirmed']).count()
    completed_orders = SalesOrder.objects.filter(status='delivered').count()
    total_revenue = SalesOrder.objects.filter(status='delivered').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')

    # Recent orders
    recent_orders = SalesOrder.objects.select_related('customer').order_by('-created_at')[:5]

    # Top customers by order value
    top_customers = Customer.objects.annotate(
        order_value=Sum('sales_orders__total_amount')
    ).filter(order_value__isnull=False).order_by('-order_value')[:5]

    context = {
        'total_customers': total_customers,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'top_customers': top_customers,
    }
    return render(request, 'sales/dashboard.html', context)


# Customer Views
@login_required
def customer_list(request):
    customers = Customer.objects.all().order_by('name')
    paginator = Paginator(customers, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Customers'
    }
    return render(request, 'sales/customer_list.html', context)


@login_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_by = request.user
            customer.save()
            messages.success(request, f'Customer {customer.name} created successfully.')
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = CustomerForm()

    context = {
        'form': form,
        'title': 'Create Customer'
    }
    return render(request, 'sales/customer_form.html', context)


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    orders = customer.sales_orders.select_related().order_by('-order_date')[:10]

    context = {
        'customer': customer,
        'recent_orders': orders,
        'title': f'Customer: {customer.name}'
    }
    return render(request, 'sales/customer_detail.html', context)


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f'Customer {customer.name} updated successfully.')
            return redirect('customer_detail', pk=customer.pk)
    else:
        form = CustomerForm(instance=customer)

    context = {
        'form': form,
        'customer': customer,
        'title': 'Update Customer'
    }
    return render(request, 'sales/customer_form.html', context)


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        name = customer.name
        customer.delete()
        messages.success(request, f'Customer {name} deleted successfully.')
        return redirect('customer_list')

    context = {
        'customer': customer,
        'title': 'Delete Customer'
    }
    return render(request, 'sales/customer_confirm_delete.html', context)


# Sales Order Views
@login_required
def sales_order_list(request):
    orders = SalesOrder.objects.select_related('customer').order_by('-order_date')
    paginator = Paginator(orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Sales Orders'
    }
    return render(request, 'sales/sales_order_list.html', context)


@login_required
def sales_order_create(request):
    if request.method == 'POST':
        form = SalesOrderForm(request.POST)
        formset = SalesOrderItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.created_by = request.user
                order.save()

                formset.instance = order
                formset.save()

                # Calculate totals
                order.subtotal = sum(item.line_total for item in order.items.all())
                order.total_amount = order.subtotal + order.tax_amount - order.discount_amount + order.shipping_cost
                order.save()

                messages.success(request, f'Sales Order {order.order_number} created successfully.')
                return redirect('sales_order_detail', pk=order.pk)
    else:
        form = SalesOrderForm()
        formset = SalesOrderItemFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Sales Order'
    }
    return render(request, 'sales/sales_order_form.html', context)


@login_required
def sales_order_detail(request, pk):
    order = get_object_or_404(
        SalesOrder.objects.select_related('customer', 'created_by'),
        pk=pk
    )
    items = order.items.select_related('product').all()

    context = {
        'order': order,
        'items': items,
        'title': f'Sales Order: {order.order_number}'
    }
    return render(request, 'sales/sales_order_detail.html', context)


@login_required
def sales_order_update(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)
    if request.method == 'POST':
        form = SalesOrderForm(request.POST, instance=order)
        formset = SalesOrderItemFormSet(request.POST, instance=order)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                order = form.save()
                formset.save()

                # Recalculate totals
                order.subtotal = sum(item.line_total for item in order.items.all())
                order.total_amount = order.subtotal + order.tax_amount - order.discount_amount + order.shipping_cost
                order.save()

                messages.success(request, f'Sales Order {order.order_number} updated successfully.')
                return redirect('sales_order_detail', pk=order.pk)
    else:
        form = SalesOrderForm(instance=order)
        formset = SalesOrderItemFormSet(instance=order)

    context = {
        'form': form,
        'formset': formset,
        'order': order,
        'title': 'Update Sales Order'
    }
    return render(request, 'sales/sales_order_form.html', context)


@login_required
def sales_order_update_status(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)

    if request.method == 'POST':
        form = SalesOrderStatusUpdateForm(request.POST)
        if form.is_valid():
            new_status = form.cleaned_data['status']
            notes = form.cleaned_data['notes']

            # Update order status
            order.status = new_status
            if new_status == 'shipped' and not order.ship_date:
                order.ship_date = timezone.now().date()
            order.save()

            messages.success(request, f'Order status updated to {new_status}.')
            return redirect('sales_order_detail', pk=order.pk)
    else:
        form = SalesOrderStatusUpdateForm(initial={'status': order.status})

    context = {
        'form': form,
        'order': order,
        'title': f'Update Status: {order.order_number}'
    }
    return render(request, 'sales/sales_order_update_status.html', context)


@login_required
def sales_order_delete(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk)
    if request.method == 'POST':
        order_number = order.order_number
        order.delete()
        messages.success(request, f'Sales Order {order_number} deleted successfully.')
        return redirect('sales_order_list')

    context = {
        'order': order,
        'title': 'Delete Sales Order'
    }
    return render(request, 'sales/sales_order_confirm_delete.html', context)


# Invoice Views
@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('sales_order__customer').order_by('-invoice_date')
    paginator = Paginator(invoices, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Invoices'
    }
    return render(request, 'sales/invoice_list.html', context)


@login_required
def invoice_create(request, order_pk):
    order = get_object_or_404(SalesOrder, pk=order_pk)

    if hasattr(order, 'invoice'):
        messages.error(request, 'Invoice already exists for this order.')
        return redirect('invoice_detail', pk=order.invoice.pk)

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.sales_order = order
            invoice.created_by = request.user
            invoice.save()
            messages.success(request, f'Invoice {invoice.invoice_number} created successfully.')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(initial={
            'sales_order': order,
            'subtotal': order.subtotal,
            'tax_amount': order.tax_amount,
            'discount_amount': order.discount_amount,
            'shipping_cost': order.shipping_cost,
            'total_amount': order.total_amount,
        })

    context = {
        'form': form,
        'order': order,
        'title': 'Create Invoice'
    }
    return render(request, 'sales/invoice_form.html', context)


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related('sales_order__customer'),
        pk=pk
    )
    payments = invoice.payments.all()

    context = {
        'invoice': invoice,
        'payments': payments,
        'title': f'Invoice: {invoice.invoice_number}'
    }
    return render(request, 'sales/invoice_detail.html', context)


@login_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, f'Invoice {invoice.invoice_number} updated successfully.')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)

    context = {
        'form': form,
        'invoice': invoice,
        'title': 'Update Invoice'
    }
    return render(request, 'sales/invoice_form.html', context)


# Payment Views
@login_required
def payment_list(request):
    payments = Payment.objects.select_related('invoice__sales_order__customer').order_by('-payment_date')
    paginator = Paginator(payments, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Payments'
    }
    return render(request, 'sales/payment_list.html', context)


@login_required
def payment_create(request, invoice_pk):
    invoice = get_object_or_404(Invoice, pk=invoice_pk)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.created_by = request.user
            payment.save()

            # Update invoice payment status
            invoice.amount_paid += payment.amount
            if invoice.amount_paid >= invoice.total_amount:
                invoice.payment_status = 'paid'
            elif invoice.amount_paid > 0:
                invoice.payment_status = 'partial'
            invoice.save()

            messages.success(request, f'Payment of {payment.amount} recorded successfully.')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = PaymentForm(initial={'invoice': invoice})

    context = {
        'form': form,
        'invoice': invoice,
        'title': 'Record Payment'
    }
    return render(request, 'sales/payment_form.html', context)


@login_required
def payment_detail(request, pk):
    payment = get_object_or_404(
        Payment.objects.select_related('invoice__sales_order__customer'),
        pk=pk
    )

    context = {
        'payment': payment,
        'title': f'Payment: {payment.amount}'
    }
    return render(request, 'sales/payment_detail.html', context)


# Product Pricing Views
@login_required
def product_pricing_list(request):
    pricing = ProductPricing.objects.select_related('product').order_by('product__name')
    paginator = Paginator(pricing, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Product Pricing'
    }
    return render(request, 'sales/pricing_list.html', context)


@login_required
def product_pricing_create(request):
    if request.method == 'POST':
        form = ProductPricingForm(request.POST)
        if form.is_valid():
            pricing = form.save(commit=False)
            pricing.updated_by = request.user
            pricing.save()
            messages.success(request, f'Pricing for {pricing.product.name} created successfully.')
            return redirect('product_pricing_list')
    else:
        form = ProductPricingForm()

    context = {
        'form': form,
        'title': 'Create Product Pricing'
    }
    return render(request, 'sales/pricing_form.html', context)


@login_required
def product_pricing_update(request, pk):
    pricing = get_object_or_404(ProductPricing, pk=pk)
    if request.method == 'POST':
        form = ProductPricingForm(request.POST, instance=pricing)
        if form.is_valid():
            pricing = form.save(commit=False)
            pricing.updated_by = request.user
            pricing.save()
            messages.success(request, f'Pricing for {pricing.product.name} updated successfully.')
            return redirect('product_pricing_list')
    else:
        form = ProductPricingForm(instance=pricing)

    context = {
        'form': form,
        'pricing': pricing,
        'title': 'Update Product Pricing'
    }
    return render(request, 'sales/pricing_form.html', context)


# Bulk Operations
@login_required
def bulk_process_orders(request):
    if request.method == 'POST':
        form = BulkOrderProcessingForm(request.POST)
        if form.is_valid():
            orders = form.cleaned_data['orders']
            action = form.cleaned_data['action']

            status_map = {
                'process': 'processing',
                'ship': 'shipped',
                'deliver': 'delivered'
            }

            new_status = status_map[action]
            count = orders.update(status=new_status)

            messages.success(request, f'{count} orders updated to {new_status}.')
            return redirect('sales_order_list')
    else:
        form = BulkOrderProcessingForm()

    context = {
        'form': form,
        'title': 'Bulk Process Orders'
    }
    return render(request, 'sales/bulk_process_orders.html', context)


# Reports
@login_required
def sales_reports(request):
    """Sales reporting and analytics"""
    # Summary statistics
    total_customers = Customer.objects.filter(is_active=True).count()
    total_orders = SalesOrder.objects.count()
    total_revenue = SalesOrder.objects.filter(status='delivered').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')

    # Monthly sales trend (last 12 months)
    monthly_sales = SalesOrder.objects.filter(
        status='delivered',
        order_date__gte=timezone.now().date() - timezone.timedelta(days=365)
    ).extra(
        select={'month': "strftime('%%Y-%%m', order_date)"}
    ).values('month').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('month')

    # Top products by sales
    top_products = SalesOrderItem.objects.values(
        'product__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('line_total')
    ).order_by('-total_revenue')[:10]

    # Customer sales summary
    customer_sales = Customer.objects.annotate(
        order_count=Count('sales_orders'),
        total_spent=Sum('sales_orders__total_amount')
    ).filter(order_count__gt=0).order_by('-total_spent')[:10]

    # Sales by customer type
    sales_by_type = Customer.objects.values('customer_type').annotate(
        customer_count=Count('id'),
        total_orders=Count('sales_orders'),
        total_revenue=Sum('sales_orders__total_amount')
    ).order_by('-total_revenue')

    # Outstanding invoices
    outstanding_invoices = Invoice.objects.filter(
        payment_status__in=['unpaid', 'partial']
    ).select_related('sales_order__customer').order_by('due_date')[:10]

    # Payment status summary
    payment_summary = Invoice.objects.values('payment_status').annotate(
        count=Count('id'),
        total_amount=Sum('total_amount'),
        paid_amount=Sum('amount_paid')
    )

    context = {
        'total_customers': total_customers,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'monthly_sales': monthly_sales,
        'top_products': top_products,
        'customer_sales': customer_sales,
        'sales_by_type': sales_by_type,
        'outstanding_invoices': outstanding_invoices,
        'payment_summary': payment_summary,
        'title': 'Sales Reports'
    }
    return render(request, 'sales/reports.html', context)


@login_required
def export_sales_report_csv(request):
    """Export sales report to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Month', 'Orders', 'Revenue'])

    monthly_sales = SalesOrder.objects.filter(
        status='delivered',
        order_date__gte=timezone.now().date() - timezone.timedelta(days=365)
    ).extra(
        select={'month': "strftime('%%Y-%%m', order_date)"}
    ).values('month').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('month')

    for data in monthly_sales:
        writer.writerow([data['month'], data['count'], f"{data['total']:.2f}"])

    return response
