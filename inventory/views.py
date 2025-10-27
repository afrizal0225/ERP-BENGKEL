from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, models
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F
from django.utils import timezone
from .models import (
    Warehouse, MaterialCategory, ProductCategory,
    RawMaterial, FinishedProduct, InventoryTransaction, StockAlert
)
from .forms import (
    WarehouseForm, MaterialCategoryForm, ProductCategoryForm,
    RawMaterialForm, FinishedProductForm, InventoryTransactionForm, StockAdjustmentForm
)


@login_required
def inventory_list(request):
    """Main inventory dashboard view"""
    # Get summary statistics
    raw_materials_count = RawMaterial.objects.filter(is_active=True).count()
    finished_products_count = FinishedProduct.objects.filter(is_active=True).count()
    warehouses_count = Warehouse.objects.filter(is_active=True).count()

    # Get low stock alerts
    low_stock_raw = RawMaterial.objects.filter(
        is_active=True,
        current_stock__lte=F('minimum_stock')
    ).count()
    low_stock_finished = FinishedProduct.objects.filter(
        is_active=True,
        current_stock__lte=F('minimum_stock')
    ).count()
    total_low_stock = low_stock_raw + low_stock_finished

    context = {
        'raw_materials_count': raw_materials_count,
        'finished_products_count': finished_products_count,
        'warehouses_count': warehouses_count,
        'total_low_stock': total_low_stock,
    }
    return render(request, 'inventory/dashboard.html', context)


# Warehouse Views
@login_required
def warehouse_list(request):
    warehouses = Warehouse.objects.all().order_by('-created_at')
    paginator = Paginator(warehouses, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Warehouses'
    }
    return render(request, 'inventory/warehouse_list.html', context)


@login_required
def warehouse_create(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Warehouse created successfully.')
            return redirect('warehouse_list')
    else:
        form = WarehouseForm()

    context = {
        'form': form,
        'title': 'Create Warehouse'
    }
    return render(request, 'inventory/warehouse_form.html', context)


@login_required
def warehouse_update(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            messages.success(request, 'Warehouse updated successfully.')
            return redirect('warehouse_list')
    else:
        form = WarehouseForm(instance=warehouse)

    context = {
        'form': form,
        'warehouse': warehouse,
        'title': 'Update Warehouse'
    }
    return render(request, 'inventory/warehouse_form.html', context)


@login_required
def warehouse_delete(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    if request.method == 'POST':
        warehouse.delete()
        messages.success(request, 'Warehouse deleted successfully.')
        return redirect('warehouse_list')

    context = {
        'warehouse': warehouse,
        'title': 'Delete Warehouse'
    }
    return render(request, 'inventory/warehouse_confirm_delete.html', context)


# Raw Material Views
@login_required
def raw_material_list(request):
    raw_materials = RawMaterial.objects.all().order_by('code')
    paginator = Paginator(raw_materials, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Raw Materials'
    }
    return render(request, 'inventory/raw_material_list.html', context)


@login_required
def raw_material_create(request):
    if request.method == 'POST':
        form = RawMaterialForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Raw material created successfully.')
            return redirect('raw_material_list')
    else:
        form = RawMaterialForm()

    context = {
        'form': form,
        'title': 'Create Raw Material'
    }
    return render(request, 'inventory/raw_material_form.html', context)


@login_required
def raw_material_update(request, pk):
    raw_material = get_object_or_404(RawMaterial, pk=pk)
    if request.method == 'POST':
        form = RawMaterialForm(request.POST, instance=raw_material)
        if form.is_valid():
            form.save()
            messages.success(request, 'Raw material updated successfully.')
            return redirect('raw_material_list')
    else:
        form = RawMaterialForm(instance=raw_material)

    context = {
        'form': form,
        'raw_material': raw_material,
        'title': 'Update Raw Material'
    }
    return render(request, 'inventory/raw_material_form.html', context)


@login_required
def raw_material_delete(request, pk):
    raw_material = get_object_or_404(RawMaterial, pk=pk)
    if request.method == 'POST':
        raw_material.delete()
        messages.success(request, 'Raw material deleted successfully.')
        return redirect('raw_material_list')

    context = {
        'raw_material': raw_material,
        'title': 'Delete Raw Material'
    }
    return render(request, 'inventory/raw_material_confirm_delete.html', context)


# Finished Product Views
@login_required
def finished_product_list(request):
    finished_products = FinishedProduct.objects.all().order_by('code')
    paginator = Paginator(finished_products, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Finished Products'
    }
    return render(request, 'inventory/finished_product_list.html', context)


@login_required
def finished_product_create(request):
    if request.method == 'POST':
        form = FinishedProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Finished product created successfully.')
            return redirect('finished_product_list')
    else:
        form = FinishedProductForm()

    context = {
        'form': form,
        'title': 'Create Finished Product'
    }
    return render(request, 'inventory/finished_product_form.html', context)


@login_required
def finished_product_update(request, pk):
    finished_product = get_object_or_404(FinishedProduct, pk=pk)
    if request.method == 'POST':
        form = FinishedProductForm(request.POST, instance=finished_product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Finished product updated successfully.')
            return redirect('finished_product_list')
    else:
        form = FinishedProductForm(instance=finished_product)

    context = {
        'form': form,
        'finished_product': finished_product,
        'title': 'Update Finished Product'
    }
    return render(request, 'inventory/finished_product_form.html', context)


@login_required
def finished_product_delete(request, pk):
    finished_product = get_object_or_404(FinishedProduct, pk=pk)
    if request.method == 'POST':
        finished_product.delete()
        messages.success(request, 'Finished product deleted successfully.')
        return redirect('finished_product_list')

    context = {
        'finished_product': finished_product,
        'title': 'Delete Finished Product'
    }
    return render(request, 'inventory/finished_product_confirm_delete.html', context)


# Stock Adjustment Views
@login_required
def stock_adjustment(request):
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            material_type = form.cleaned_data['material_type']
            material_id = form.cleaned_data['material_id']
            adjustment_type = form.cleaned_data['adjustment_type']
            quantity = form.cleaned_data['quantity']
            reason = form.cleaned_data['reason']
            warehouse = form.cleaned_data['warehouse']

            with transaction.atomic():
                if material_type == 'raw':
                    material = get_object_or_404(RawMaterial, pk=material_id)
                    if adjustment_type == 'add':
                        material.current_stock += quantity
                    else:
                        material.current_stock -= quantity
                    material.save()
                else:
                    material = get_object_or_404(FinishedProduct, pk=material_id)
                    if adjustment_type == 'add':
                        material.current_stock += quantity
                    else:
                        material.current_stock -= quantity
                    material.save()

                # Create transaction record
                transaction_type = 'IN' if adjustment_type == 'add' else 'ADJ'
                InventoryTransaction.objects.create(
                    transaction_type=transaction_type,
                    material_type=material_type,
                    material_id=material_id,
                    material_name=material.name,
                    quantity=quantity,
                    unit_price=material.unit_price,
                    reference_number=f"ADJ-{request.user.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    notes=f"Stock adjustment: {reason}",
                    warehouse=warehouse,
                    created_by=request.user
                )

            messages.success(request, 'Stock adjustment completed successfully.')
            return redirect('stock_adjustment')
    else:
        form = StockAdjustmentForm()

    context = {
        'form': form,
        'title': 'Stock Adjustment'
    }
    return render(request, 'inventory/stock_adjustment.html', context)


@login_required
def get_material_details(request):
    """AJAX view to get material details for stock adjustment"""
    material_type = request.GET.get('material_type')
    material_id = request.GET.get('material_id')

    if material_type == 'raw':
        material = get_object_or_404(RawMaterial, pk=material_id)
    else:
        material = get_object_or_404(FinishedProduct, pk=material_id)

    data = {
        'name': material.name,
        'current_stock': str(material.current_stock),
        'unit': material.unit if hasattr(material, 'unit') else 'pcs'
    }
    return JsonResponse(data)


# Transaction History Views
@login_required
def transaction_list(request):
    transactions = InventoryTransaction.objects.all().order_by('-created_at')
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Transaction History'
    }
    return render(request, 'inventory/transaction_list.html', context)


# Stock Alert Views
@login_required
def stock_alert_list(request):
    alerts = StockAlert.objects.filter(is_resolved=False).order_by('-created_at')
    paginator = Paginator(alerts, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Stock Alerts'
    }
    return render(request, 'inventory/stock_alert_list.html', context)
