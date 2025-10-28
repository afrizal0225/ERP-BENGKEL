from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
from datetime import timedelta
from .models import (
    ProductionOrder, BillOfMaterials, BOMItem, WorkOrder,
    MaterialConsumption, ProductionProgress
)
from .forms import (
    ProductionOrderForm, BillOfMaterialsForm, BOMItemFormSet,
    WorkOrderForm, MaterialConsumptionForm, ProductionProgressForm,
    BulkWorkOrderGenerationForm
)
from inventory.models import FinishedProduct, RawMaterial


@login_required
def manufacturing_list(request):
    """Main manufacturing dashboard view"""
    # Get summary statistics
    active_pos = ProductionOrder.objects.filter(status__in=['approved', 'in_progress']).count()
    completed_pos = ProductionOrder.objects.filter(status='completed').count()
    overdue_pos = ProductionOrder.objects.filter(
        planned_end_date__lt=timezone.now().date(),
        status__in=['approved', 'in_progress']
    ).count()
    active_work_orders = WorkOrder.objects.filter(status__in=['pending', 'in_progress']).count()

    # Recent production orders
    recent_pos = ProductionOrder.objects.select_related('product', 'created_by').order_by('-created_at')[:5]

    # Work orders by stage
    stage_stats = WorkOrder.objects.values('stage').annotate(
        count=Count('id'),
        completed=Count('id', filter=Q(status='completed'))
    ).order_by('stage')

    context = {
        'active_pos': active_pos,
        'completed_pos': completed_pos,
        'overdue_pos': overdue_pos,
        'active_work_orders': active_work_orders,
        'recent_pos': recent_pos,
        'stage_stats': stage_stats,
    }
    return render(request, 'manufacturing/dashboard.html', context)


# Production Order Views
@login_required
def production_order_list(request):
    production_orders = ProductionOrder.objects.select_related('product', 'created_by', 'approved_by').order_by('-planned_start_date')
    paginator = Paginator(production_orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get status counts for summary cards
    status_counts = ProductionOrder.objects.aggregate(
        draft=Count('id', filter=Q(status='draft')),
        pending_approval=Count('id', filter=Q(status='pending_approval')),
        approved=Count('id', filter=Q(status='approved')),
        in_progress=Count('id', filter=Q(status='in_progress')),
        completed=Count('id', filter=Q(status='completed')),
        cancelled=Count('id', filter=Q(status='cancelled')),
    )

    context = {
        'page_obj': page_obj,
        'status_counts': status_counts,
        'title': 'Production Orders'
    }
    return render(request, 'manufacturing/production_order_list.html', context)


@login_required
def production_order_create(request):
    if request.method == 'POST':
        form = ProductionOrderForm(request.POST)
        if form.is_valid():
            po = form.save(commit=False)
            po.created_by = request.user
            po.save()

            messages.success(request, f'Production Order {po.po_number} created successfully.')
            return redirect('production_order_detail', pk=po.pk)
    else:
        form = ProductionOrderForm()

    context = {
        'form': form,
        'title': 'Create Production Order'
    }
    return render(request, 'manufacturing/production_order_form.html', context)


@login_required
def production_order_detail(request, pk):
    po = get_object_or_404(
        ProductionOrder.objects.select_related('product', 'created_by', 'approved_by').prefetch_related('work_orders'),
        pk=pk
    )

    # Get work orders for this PO
    work_orders = po.work_orders.select_related('assigned_to').order_by('stage')

    context = {
        'po': po,
        'work_orders': work_orders,
        'title': f'Production Order: {po.po_number}'
    }
    return render(request, 'manufacturing/production_order_detail.html', context)


@login_required
def production_order_update(request, pk):
    po = get_object_or_404(ProductionOrder, pk=pk)

    # Only allow editing if status is draft or pending_approval
    if po.status not in ['draft', 'pending_approval']:
        messages.error(request, 'Cannot edit production order that has been processed.')
        return redirect('production_order_detail', pk=pk)

    if request.method == 'POST':
        form = ProductionOrderForm(request.POST, instance=po)
        if form.is_valid():
            po = form.save()
            messages.success(request, f'Production Order {po.po_number} updated successfully.')
            return redirect('production_order_detail', pk=po.pk)
    else:
        form = ProductionOrderForm(instance=po)

    context = {
        'form': form,
        'po': po,
        'title': f'Update Production Order: {po.po_number}'
    }
    return render(request, 'manufacturing/production_order_form.html', context)


@login_required
def production_order_submit_approval(request, pk):
    """Submit production order for approval (change status from draft to pending_approval)"""
    po = get_object_or_404(ProductionOrder, pk=pk)

    # Check user permissions (admin or production_manager)
    if not (request.user.is_superuser or hasattr(request.user, 'userprofile') and
            request.user.userprofile.role in ['admin', 'production_manager']):
        messages.error(request, 'You do not have permission to submit production orders for approval.')
        return redirect('production_order_detail', pk=pk)

    # Only allow submission if status is draft
    if po.status != 'draft':
        messages.error(request, 'Only draft production orders can be submitted for approval.')
        return redirect('production_order_detail', pk=pk)

    if request.method == 'POST':
        po.status = 'pending_approval'
        po.save()
        messages.success(request, f'Production Order {po.po_number} has been submitted for approval.')
        return redirect('production_order_detail', pk=pk)

    context = {
        'po': po,
        'title': f'Submit for Approval: {po.po_number}'
    }
    return render(request, 'manufacturing/production_order_submit_approval.html', context)


@login_required
def production_order_approve(request, pk):
    po = get_object_or_404(ProductionOrder, pk=pk)

    if po.status != 'pending_approval':
        messages.error(request, 'Production order is not pending approval.')
        return redirect('production_order_detail', pk=pk)

    if request.method == 'POST':
        po.status = 'approved'
        po.approved_by = request.user
        po.approved_at = timezone.now()
        po.save()

        messages.success(request, f'Production Order {po.po_number} has been approved.')
        return redirect('production_order_detail', pk=pk)

    context = {
        'po': po,
        'title': f'Approve Production Order: {po.po_number}'
    }
    return render(request, 'manufacturing/production_order_approve.html', context)


@login_required
def production_order_delete(request, pk):
    po = get_object_or_404(ProductionOrder, pk=pk)

    # Only allow deletion if status is draft
    if po.status != 'draft':
        messages.error(request, 'Cannot delete production order that has been processed.')
        return redirect('production_order_detail', pk=pk)

    if request.method == 'POST':
        po_number = po.po_number
        po.delete()
        messages.success(request, f'Production Order {po_number} deleted successfully.')
        return redirect('production_order_list')

    context = {
        'po': po,
        'title': 'Delete Production Order'
    }
    return render(request, 'manufacturing/production_order_confirm_delete.html', context)


# Bill of Materials Views
@login_required
def bill_of_materials_list(request):
    boms = BillOfMaterials.objects.select_related('product', 'created_by').filter(is_active=True).order_by('-created_at')
    paginator = Paginator(boms, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Bills of Materials'
    }
    return render(request, 'manufacturing/bom_list.html', context)


@login_required
def bill_of_materials_create(request):
    if request.method == 'POST':
        form = BillOfMaterialsForm(request.POST)
        formset = BOMItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                bom = form.save(commit=False)
                bom.created_by = request.user
                bom.save()

                formset.instance = bom
                formset.save()

                # Calculate total cost
                bom.calculate_total_cost()

                messages.success(request, f'BOM for {bom.product.name} created successfully.')
                return redirect('bill_of_materials_detail', pk=bom.pk)
    else:
        form = BillOfMaterialsForm()
        formset = BOMItemFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Bill of Materials'
    }
    return render(request, 'manufacturing/bom_form.html', context)


@login_required
def bill_of_materials_detail(request, pk):
    bom = get_object_or_404(
        BillOfMaterials.objects.select_related('product', 'created_by').prefetch_related('items__material'),
        pk=pk
    )

    context = {
        'bom': bom,
        'title': f'BOM: {bom.product.name} v{bom.version}'
    }
    return render(request, 'manufacturing/bom_detail.html', context)


@login_required
def bill_of_materials_update(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk)

    if request.method == 'POST':
        form = BillOfMaterialsForm(request.POST, instance=bom)
        formset = BOMItemFormSet(request.POST, instance=bom)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                bom = form.save()
                formset.save()

                # Calculate total cost
                bom.calculate_total_cost()

                messages.success(request, f'BOM for {bom.product.name} updated successfully.')
                return redirect('bill_of_materials_detail', pk=bom.pk)
    else:
        form = BillOfMaterialsForm(instance=bom)
        formset = BOMItemFormSet(instance=bom)

    context = {
        'form': form,
        'formset': formset,
        'bom': bom,
        'title': f'Update BOM: {bom.product.name} v{bom.version}'
    }
    return render(request, 'manufacturing/bom_form.html', context)


@login_required
def bill_of_materials_delete(request, pk):
    bom = get_object_or_404(BillOfMaterials, pk=pk)

    if request.method == 'POST':
        product_name = bom.product.name
        bom.delete()
        messages.success(request, f'BOM for {product_name} deleted successfully.')
        return redirect('bill_of_materials_list')

    context = {
        'bom': bom,
        'title': f'Delete BOM: {bom.product.name} v{bom.version}'
    }
    return render(request, 'manufacturing/bom_confirm_delete.html', context)


# Work Order Views
@login_required
def work_order_list(request):
    work_orders = WorkOrder.objects.select_related(
        'production_order__product', 'assigned_to', 'supervisor'
    ).order_by('-planned_start_date')
    paginator = Paginator(work_orders, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Work Orders'
    }
    return render(request, 'manufacturing/work_order_list.html', context)


@login_required
def work_order_detail(request, pk):
    wo = get_object_or_404(
        WorkOrder.objects.select_related('production_order__product', 'assigned_to', 'supervisor'),
        pk=pk
    )

    # Get material consumption and progress records
    consumptions = wo.material_consumptions.select_related('material', 'recorded_by').order_by('-consumption_date')
    progress_entries = wo.progress_entries.select_related('recorded_by').order_by('-progress_date')

    context = {
        'wo': wo,
        'consumptions': consumptions,
        'progress_entries': progress_entries,
        'title': f'Work Order: {wo.wo_number}'
    }
    return render(request, 'manufacturing/work_order_detail.html', context)


@login_required
def generate_work_orders(request):
    """Generate work orders from approved production order"""
    if request.method == 'POST':
        form = BulkWorkOrderGenerationForm(request.POST)
        if form.is_valid():
            po = form.cleaned_data['production_order']
            start_date = form.cleaned_data['planned_start_date']
            duration_days = form.cleaned_data['duration_days']

            stages_data = [
                ('gurat', form.cleaned_data.get('gurat_quantity')),
                ('assembly', form.cleaned_data.get('assembly_quantity')),
                ('press', form.cleaned_data.get('press_quantity')),
                ('finishing', form.cleaned_data.get('finishing_quantity')),
            ]

            with transaction.atomic():
                # Generate work orders for each stage with quantity > 0
                current_date = start_date
                for stage, quantity in stages_data:
                    if quantity and quantity > 0:
                        end_date = current_date + timedelta(days=duration_days - 1)

                        WorkOrder.objects.create(
                            wo_number=f"WO-{po.po_number}-{stage.upper()[:3]}-{timezone.now().strftime('%H%M%S')}",
                            production_order=po,
                            stage=stage,
                            quantity=quantity,
                            planned_start_date=current_date,
                            planned_end_date=end_date,
                        )

                        current_date = end_date + timedelta(days=1)

                # Update PO status to in_progress
                po.status = 'in_progress'
                po.actual_start_date = timezone.now().date()
                po.save()

                messages.success(request, f'Work orders generated successfully for {po.po_number}.')
                return redirect('production_order_detail', pk=po.pk)
    else:
        form = BulkWorkOrderGenerationForm()

    context = {
        'form': form,
        'title': 'Generate Work Orders'
    }
    return render(request, 'manufacturing/generate_work_orders.html', context)


@login_required
def record_material_consumption(request, wo_pk):
    """Record material consumption for a work order"""
    wo = get_object_or_404(WorkOrder, pk=wo_pk)

    if request.method == 'POST':
        form = MaterialConsumptionForm(request.POST, work_order=wo)
        if form.is_valid():
            consumption = form.save(commit=False)
            consumption.work_order = wo
            consumption.recorded_by = request.user
            consumption.save()

            messages.success(request, f'Material consumption recorded for {consumption.material.name}.')
            return redirect('work_order_detail', pk=wo.pk)
    else:
        form = MaterialConsumptionForm(work_order=wo)

    context = {
        'form': form,
        'wo': wo,
        'title': f'Record Material Consumption - {wo.wo_number}'
    }
    return render(request, 'manufacturing/record_consumption.html', context)


@login_required
def record_production_progress(request, wo_pk):
    """Record production progress for a work order"""
    wo = get_object_or_404(WorkOrder, pk=wo_pk)

    if request.method == 'POST':
        form = ProductionProgressForm(request.POST)
        if form.is_valid():
            progress = form.save(commit=False)
            progress.work_order = wo
            progress.recorded_by = request.user
            progress.save()

            messages.success(request, f'Progress updated to {progress.progress_percentage}% for {wo.wo_number}.')
            return redirect('work_order_detail', pk=wo.pk)
    else:
        form = ProductionProgressForm()

    context = {
        'form': form,
        'wo': wo,
        'title': f'Record Production Progress - {wo.wo_number}'
    }
    return render(request, 'manufacturing/record_progress.html', context)


# Manufacturing Reports
@login_required
def manufacturing_reports(request):
    """Manufacturing reporting and analytics"""
    # Summary statistics
    total_pos = ProductionOrder.objects.count()
    completed_pos = ProductionOrder.objects.filter(status='completed').count()
    active_pos = ProductionOrder.objects.filter(status__in=['approved', 'in_progress']).count()
    total_work_orders = WorkOrder.objects.count()

    # Production efficiency metrics
    avg_completion_time = ProductionOrder.objects.filter(
        status='completed',
        actual_start_date__isnull=False,
        actual_end_date__isnull=False
    ).aggregate(
        avg_days=Avg('actual_end_date' - 'actual_start_date')
    )['avg_days']

    # Material usage summary
    total_consumed = MaterialConsumption.objects.aggregate(
        total=Sum('actual_quantity')
    )['total'] or 0

    # Work orders by stage
    stage_summary = WorkOrder.objects.values('stage').annotate(
        total=Count('id'),
        completed=Count('id', filter=Q(status='completed')),
        in_progress=Count('id', filter=Q(status='in_progress'))
    ).order_by('stage')

    context = {
        'total_pos': total_pos,
        'completed_pos': completed_pos,
        'active_pos': active_pos,
        'total_work_orders': total_work_orders,
        'avg_completion_time': avg_completion_time,
        'total_consumed': total_consumed,
        'stage_summary': stage_summary,
        'title': 'Manufacturing Reports'
    }
    return render(request, 'manufacturing/reports.html', context)
