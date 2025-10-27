from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
from .models import Vendor, PurchaseOrder, PurchaseOrderLineItem, GoodsReceipt, GoodsReceiptLineItem
from .forms import (
    VendorForm, PurchaseOrderForm, PurchaseOrderLineItemFormSet,
    GoodsReceiptForm, get_goods_receipt_line_item_formset, VendorPerformanceForm
)


@login_required
def purchase_list(request):
    """Main purchase dashboard view"""
    # Get summary statistics
    vendors_count = Vendor.objects.filter(is_active=True).count()
    active_pos = PurchaseOrder.objects.filter(status__in=['approved', 'ordered', 'partially_received']).count()
    overdue_pos = PurchaseOrder.objects.filter(
        expected_delivery_date__lt=timezone.now().date(),
        status__in=['approved', 'ordered', 'partially_received']
    ).count()

    # Recent POs
    recent_pos = PurchaseOrder.objects.select_related('vendor', 'created_by').order_by('-created_at')[:5]

    context = {
        'vendors_count': vendors_count,
        'active_pos': active_pos,
        'overdue_pos': overdue_pos,
        'recent_pos': recent_pos,
    }
    return render(request, 'purchase/dashboard.html', context)


# Vendor Views
@login_required
def vendor_list(request):
    vendors = Vendor.objects.all().order_by('name')
    paginator = Paginator(vendors, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Vendors'
    }
    return render(request, 'purchase/vendor_list.html', context)


@login_required
def vendor_create(request):
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor created successfully.')
            return redirect('vendor_list')
    else:
        form = VendorForm()

    context = {
        'form': form,
        'title': 'Create Vendor'
    }
    return render(request, 'purchase/vendor_form.html', context)


@login_required
def vendor_update(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vendor updated successfully.')
            return redirect('vendor_list')
    else:
        form = VendorForm(instance=vendor)

    context = {
        'form': form,
        'vendor': vendor,
        'title': 'Update Vendor'
    }
    return render(request, 'purchase/vendor_form.html', context)


@login_required
def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        vendor.delete()
        messages.success(request, 'Vendor deleted successfully.')
        return redirect('vendor_list')

    context = {
        'vendor': vendor,
        'title': 'Delete Vendor'
    }
    return render(request, 'purchase/vendor_confirm_delete.html', context)


@login_required
def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)

    # Get vendor statistics
    total_pos = PurchaseOrder.objects.filter(vendor=vendor).count()
    active_pos = PurchaseOrder.objects.filter(vendor=vendor, status__in=['approved', 'ordered', 'partially_received']).count()
    completed_pos = PurchaseOrder.objects.filter(vendor=vendor, status='received').count()

    # Recent POs
    recent_pos = PurchaseOrder.objects.filter(vendor=vendor).select_related('created_by').order_by('-created_at')[:10]

    context = {
        'vendor': vendor,
        'total_pos': total_pos,
        'active_pos': active_pos,
        'completed_pos': completed_pos,
        'recent_pos': recent_pos,
        'title': f'Vendor: {vendor.name}'
    }
    return render(request, 'purchase/vendor_detail.html', context)


# Purchase Order Views
@login_required
def purchase_order_list(request):
    purchase_orders = PurchaseOrder.objects.select_related('vendor', 'created_by', 'approved_by').order_by('-order_date')
    paginator = Paginator(purchase_orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Purchase Orders'
    }
    return render(request, 'purchase/purchase_order_list.html', context)


@login_required
def purchase_order_create(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        formset = PurchaseOrderLineItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                po = form.save(commit=False)
                po.created_by = request.user
                po.save()

                formset.instance = po
                formset.save()

                # Calculate total
                po.calculate_total()

                messages.success(request, f'Purchase Order {po.po_number} created successfully.')
                return redirect('purchase_order_detail', pk=po.pk)
    else:
        form = PurchaseOrderForm()
        formset = PurchaseOrderLineItemFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Purchase Order'
    }
    return render(request, 'purchase/purchase_order_form.html', context)


@login_required
def purchase_order_update(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)

    # Only allow editing if status is draft or pending_approval
    if po.status not in ['draft', 'pending_approval']:
        messages.error(request, 'Cannot edit purchase order that has been approved or processed.')
        return redirect('purchase_order_detail', pk=pk)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=po)
        formset = PurchaseOrderLineItemFormSet(request.POST, instance=po)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()

                # Recalculate total
                po.calculate_total()

                messages.success(request, f'Purchase Order {po.po_number} updated successfully.')
                return redirect('purchase_order_detail', pk=pk)
    else:
        form = PurchaseOrderForm(instance=po)
        formset = PurchaseOrderLineItemFormSet(instance=po)

    context = {
        'form': form,
        'formset': formset,
        'po': po,
        'title': f'Update Purchase Order: {po.po_number}'
    }
    return render(request, 'purchase/purchase_order_form.html', context)


@login_required
def purchase_order_detail(request, pk):
    po = get_object_or_404(
        PurchaseOrder.objects.select_related('vendor', 'created_by', 'approved_by').prefetch_related('line_items'),
        pk=pk
    )

    context = {
        'po': po,
        'title': f'Purchase Order: {po.po_number}'
    }
    return render(request, 'purchase/purchase_order_detail.html', context)


@login_required
def purchase_order_approve(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)

    if po.status != 'pending_approval':
        messages.error(request, 'Purchase order is not pending approval.')
        return redirect('purchase_order_detail', pk=pk)

    if request.method == 'POST':
        po.status = 'approved'
        po.approved_by = request.user
        po.approved_at = timezone.now()
        po.save()

        messages.success(request, f'Purchase Order {po.po_number} has been approved.')
        return redirect('purchase_order_detail', pk=pk)

    context = {
        'po': po,
        'title': f'Approve Purchase Order: {po.po_number}'
    }
    return render(request, 'purchase/purchase_order_approve.html', context)


@login_required
def purchase_order_delete(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)

    # Only allow deletion if status is draft
    if po.status != 'draft':
        messages.error(request, 'Cannot delete purchase order that has been processed.')
        return redirect('purchase_order_detail', pk=pk)

    if request.method == 'POST':
        po_number = po.po_number
        po.delete()
        messages.success(request, f'Purchase Order {po_number} deleted successfully.')
        return redirect('purchase_order_list')

    context = {
        'po': po,
        'title': 'Delete Purchase Order'
    }
    return render(request, 'purchase/purchase_order_confirm_delete.html', context)


# Goods Receipt Views
@login_required
def goods_receipt_list(request):
    receipts = GoodsReceipt.objects.select_related('purchase_order__vendor', 'received_by').order_by('-receipt_date')
    paginator = Paginator(receipts, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Goods Receipts'
    }
    return render(request, 'purchase/goods_receipt_list.html', context)


@login_required
def goods_receipt_create(request):
    if request.method == 'POST':
        form = GoodsReceiptForm(request.POST)
        if form.is_valid():
            gr = form.save(commit=False)
            gr.received_by = request.user
            gr.save()

            # Create line items for all PO items that aren't fully received
            po = gr.purchase_order
            for po_item in po.line_items.filter(received_quantity__lt=models.F('quantity')):
                GoodsReceiptLineItem.objects.create(
                    goods_receipt=gr,
                    purchase_order_item=po_item,
                    received_quantity=min(po_item.remaining_quantity, po_item.quantity),  # Default to remaining quantity
                    unit_price=po_item.unit_price,
                    quality_status='accepted'
                )

            # Calculate total
            gr.calculate_total()

            messages.success(request, f'Goods Receipt {gr.gr_number} created successfully.')
            return redirect('goods_receipt_detail', pk=gr.pk)
    else:
        form = GoodsReceiptForm()

    context = {
        'form': form,
        'title': 'Create Goods Receipt'
    }
    return render(request, 'purchase/goods_receipt_form.html', context)


@login_required
def goods_receipt_detail(request, pk):
    gr = get_object_or_404(
        GoodsReceipt.objects.select_related('purchase_order__vendor', 'received_by').prefetch_related('line_items'),
        pk=pk
    )

    context = {
        'gr': gr,
        'title': f'Goods Receipt: {gr.gr_number}'
    }
    return render(request, 'purchase/goods_receipt_detail.html', context)


@login_required
def goods_receipt_update(request, pk):
    gr = get_object_or_404(GoodsReceipt, pk=pk)

    if request.method == 'POST':
        form = GoodsReceiptForm(request.POST, instance=gr)
        if form.is_valid():
            form.save()
            # Recalculate total
            gr.calculate_total()
            messages.success(request, f'Goods Receipt {gr.gr_number} updated successfully.')
            return redirect('goods_receipt_detail', pk=pk)
    else:
        form = GoodsReceiptForm(instance=gr)

    context = {
        'form': form,
        'gr': gr,
        'title': f'Update Goods Receipt: {gr.gr_number}'
    }
    return render(request, 'purchase/goods_receipt_form.html', context)


# Vendor Performance Views
@login_required
def vendor_performance(request):
    if request.method == 'POST':
        form = VendorPerformanceForm(request.POST)
        if form.is_valid():
            vendor = form.cleaned_data['vendor']
            on_time_delivery = form.cleaned_data['on_time_delivery']
            quality_rating = form.cleaned_data['quality_rating']

            # Update vendor performance metrics
            vendor.total_orders += 1
            if on_time_delivery:
                vendor.on_time_deliveries += 1

            # Update quality rating (simple average for now)
            if vendor.quality_rating == 0:
                vendor.quality_rating = quality_rating
            else:
                vendor.quality_rating = (vendor.quality_rating + quality_rating) / 2

            vendor.save()

            messages.success(request, f'Performance data updated for {vendor.name}.')
            return redirect('vendor_performance')
    else:
        form = VendorPerformanceForm()

    # Get vendor performance summary
    vendors = Vendor.objects.filter(is_active=True).order_by('-quality_rating')
    paginator = Paginator(vendors, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'page_obj': page_obj,
        'title': 'Vendor Performance'
    }
    return render(request, 'purchase/vendor_performance.html', context)


@login_required
def purchase_reports(request):
    """Purchase reporting and analytics"""
    # Summary statistics
    total_vendors = Vendor.objects.filter(is_active=True).count()
    total_pos = PurchaseOrder.objects.count()
    total_po_value = PurchaseOrder.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    pending_pos = PurchaseOrder.objects.filter(status__in=['pending_approval', 'approved', 'ordered']).count()

    # Monthly PO trends (last 6 months)
    from django.db.models.functions import TruncMonth
    monthly_pos = PurchaseOrder.objects.annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        count=Count('id'),
        total_value=Sum('total_amount')
    ).order_by('-month')[:6]

    context = {
        'total_vendors': total_vendors,
        'total_pos': total_pos,
        'total_po_value': total_po_value,
        'pending_pos': pending_pos,
        'monthly_pos': monthly_pos,
        'title': 'Purchase Reports'
    }
    return render(request, 'purchase/reports.html', context)
