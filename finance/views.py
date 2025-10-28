from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
import csv
import json
from .models import (
    Account, Transaction, JournalEntry, JournalEntryLine,
    Budget, BudgetLine, TaxRate, FinancialPeriod
)
from .forms import (
    AccountForm, TransactionForm, JournalEntryForm, JournalEntryLineFormSet,
    BudgetForm, BudgetLineFormSet, TaxRateForm, FinancialPeriodForm,
    FinancialReportForm, AccountTransferForm
)


@login_required
def finance_dashboard(request):
    """Finance module dashboard"""
    # Account balances summary
    asset_accounts = Account.objects.filter(account_type='asset', is_active=True).aggregate(
        total=Sum('balance')
    )['total'] or Decimal('0.00')

    liability_accounts = Account.objects.filter(account_type='liability', is_active=True).aggregate(
        total=Sum('balance')
    )['total'] or Decimal('0.00')

    equity_accounts = Account.objects.filter(account_type='equity', is_active=True).aggregate(
        total=Sum('balance')
    )['total'] or Decimal('0.00')

    # Recent transactions
    recent_transactions = Transaction.objects.select_related('account').order_by('-created_at')[:10]

    # Active budgets
    active_budgets = Budget.objects.filter(is_active=True, status='active')

    # Current financial period
    current_period = FinancialPeriod.objects.filter(is_closed=False).first()

    context = {
        'asset_total': asset_accounts,
        'liability_total': liability_accounts,
        'equity_total': equity_accounts,
        'net_worth': asset_accounts - liability_accounts - equity_accounts,
        'recent_transactions': recent_transactions,
        'active_budgets': active_budgets,
        'current_period': current_period,
        'title': 'Finance Dashboard'
    }
    return render(request, 'finance/dashboard.html', context)


# Account Views
@login_required
def account_list(request):
    accounts = Account.objects.all().order_by('code')
    paginator = Paginator(accounts, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Chart of Accounts'
    }
    return render(request, 'finance/account_list.html', context)


@login_required
def account_create(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.created_by = request.user
            account.save()
            messages.success(request, f'Account {account.name} created successfully.')
            return redirect('account_detail', pk=account.pk)
    else:
        form = AccountForm()

    context = {
        'form': form,
        'title': 'Create Account'
    }
    return render(request, 'finance/account_form.html', context)


@login_required
def account_detail(request, pk):
    account = get_object_or_404(Account, pk=pk)
    transactions = account.transactions.select_related().order_by('-date')[:20]

    context = {
        'account': account,
        'recent_transactions': transactions,
        'title': f'Account: {account.name}'
    }
    return render(request, 'finance/account_detail.html', context)


@login_required
def account_update(request, pk):
    account = get_object_or_404(Account, pk=pk)
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, f'Account {account.name} updated successfully.')
            return redirect('account_detail', pk=account.pk)
    else:
        form = AccountForm(instance=account)

    context = {
        'form': form,
        'account': account,
        'title': 'Update Account'
    }
    return render(request, 'finance/account_form.html', context)


# Transaction Views
@login_required
def transaction_list(request):
    transactions = Transaction.objects.select_related('account', 'created_by').order_by('-date')
    paginator = Paginator(transactions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Transactions'
    }
    return render(request, 'finance/transaction_list.html', context)


@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()
            messages.success(request, f'Transaction recorded successfully.')
            return redirect('transaction_list')
    else:
        form = TransactionForm()

    context = {
        'form': form,
        'title': 'Record Transaction'
    }
    return render(request, 'finance/transaction_form.html', context)


# Journal Entry Views
@login_required
def journal_entry_list(request):
    entries = JournalEntry.objects.select_related().order_by('-date')
    paginator = Paginator(entries, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Journal Entries'
    }
    return render(request, 'finance/journal_entry_list.html', context)


@login_required
def journal_entry_create(request):
    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        formset = JournalEntryLineFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                entry = form.save(commit=False)
                entry.created_by = request.user
                entry.save()

                formset.instance = entry
                formset.save()

                messages.success(request, f'Journal entry {entry.reference_number} created successfully.')
                return redirect('journal_entry_detail', pk=entry.pk)
    else:
        form = JournalEntryForm()
        formset = JournalEntryLineFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Journal Entry'
    }
    return render(request, 'finance/journal_entry_form.html', context)


@login_required
def journal_entry_detail(request, pk):
    entry = get_object_or_404(JournalEntry.objects.select_related(), pk=pk)
    lines = entry.lines.select_related('account').all()

    context = {
        'entry': entry,
        'lines': lines,
        'title': f'Journal Entry: {entry.reference_number}'
    }
    return render(request, 'finance/journal_entry_detail.html', context)


@login_required
def journal_entry_post(request, pk):
    entry = get_object_or_404(JournalEntry, pk=pk)

    if entry.is_posted:
        messages.error(request, 'Journal entry is already posted.')
        return redirect('journal_entry_detail', pk=entry.pk)

    if not entry.is_balanced:
        messages.error(request, 'Cannot post unbalanced journal entry.')
        return redirect('journal_entry_detail', pk=entry.pk)

    with transaction.atomic():
        # Create transactions for each journal entry line
        for line in entry.lines.all():
            Transaction.objects.create(
                date=entry.date,
                description=f"JE-{entry.reference_number}: {entry.description}",
                account=line.account,
                transaction_type=line.transaction_type,
                amount=line.amount,
                created_by=request.user
            )

        entry.is_posted = True
        entry.posted_date = timezone.now()
        entry.save()

    messages.success(request, f'Journal entry {entry.reference_number} posted successfully.')
    return redirect('journal_entry_detail', pk=entry.pk)


# Budget Views
@login_required
def budget_list(request):
    budgets = Budget.objects.select_related().order_by('-start_date')
    paginator = Paginator(budgets, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Budgets'
    }
    return render(request, 'finance/budget_list.html', context)


@login_required
def budget_create(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        formset = BudgetLineFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                budget = form.save(commit=False)
                budget.created_by = request.user
                budget.save()

                formset.instance = budget
                formset.save()

                messages.success(request, f'Budget {budget.name} created successfully.')
                return redirect('budget_detail', pk=budget.pk)
    else:
        form = BudgetForm()
        formset = BudgetLineFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Create Budget'
    }
    return render(request, 'finance/budget_form.html', context)


@login_required
def budget_detail(request, pk):
    budget = get_object_or_404(Budget, pk=pk)
    lines = budget.lines.select_related('account').all()

    context = {
        'budget': budget,
        'lines': lines,
        'title': f'Budget: {budget.name}'
    }
    return render(request, 'finance/budget_detail.html', context)


# Tax Rate Views
@login_required
def tax_rate_list(request):
    tax_rates = TaxRate.objects.all().order_by('name')
    paginator = Paginator(tax_rates, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'title': 'Tax Rates'
    }
    return render(request, 'finance/tax_rate_list.html', context)


@login_required
def tax_rate_create(request):
    if request.method == 'POST':
        form = TaxRateForm(request.POST)
        if form.is_valid():
            tax_rate = form.save(commit=False)
            tax_rate.created_by = request.user
            tax_rate.save()
            messages.success(request, f'Tax rate {tax_rate.name} created successfully.')
            return redirect('tax_rate_list')
    else:
        form = TaxRateForm()

    context = {
        'form': form,
        'title': 'Create Tax Rate'
    }
    return render(request, 'finance/tax_rate_form.html', context)


# Financial Reports
@login_required
def financial_reports(request):
    """Financial reporting dashboard"""
    if request.method == 'POST':
        form = FinancialReportForm(request.POST)
        if form.is_valid():
            report_type = form.cleaned_data['report_type']
            start_date = form.cleaned_data.get('start_date')
            end_date = form.cleaned_data.get('end_date')
            account_filter = form.cleaned_data.get('account_filter')

            # Generate report based on type
            if report_type == 'trial_balance':
                return generate_trial_balance(request, start_date, end_date, account_filter)
            elif report_type == 'balance_sheet':
                return generate_balance_sheet(request, start_date, end_date)
            elif report_type == 'income_statement':
                return generate_income_statement(request, start_date, end_date)
            elif report_type == 'cash_flow':
                return generate_cash_flow(request, start_date, end_date)
    else:
        form = FinancialReportForm()

    context = {
        'form': form,
        'title': 'Financial Reports'
    }
    return render(request, 'finance/reports.html', context)


def generate_trial_balance(request, start_date=None, end_date=None, account_filter=None):
    """Generate trial balance report"""
    accounts = Account.objects.filter(is_active=True)

    if account_filter:
        accounts = accounts.filter(pk__in=account_filter)

    trial_balance_data = []
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')

    for account in accounts:
        # Calculate balance for the period
        transactions = account.transactions.all()
        if start_date:
            transactions = transactions.filter(date__gte=start_date)
        if end_date:
            transactions = transactions.filter(date__lte=end_date)

        debit_total = transactions.filter(transaction_type='debit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        credit_total = transactions.filter(transaction_type='credit').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')

        balance = debit_total - credit_total

        if balance != 0:
            trial_balance_data.append({
                'account': account,
                'debit': balance if balance > 0 else Decimal('0.00'),
                'credit': abs(balance) if balance < 0 else Decimal('0.00')
            })

            total_debit += balance if balance > 0 else Decimal('0.00')
            total_credit += abs(balance) if balance < 0 else Decimal('0.00')

    context = {
        'trial_balance_data': trial_balance_data,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'start_date': start_date,
        'end_date': end_date,
        'title': 'Trial Balance'
    }
    return render(request, 'finance/trial_balance.html', context)


def generate_balance_sheet(request, start_date=None, end_date=None):
    """Generate balance sheet report"""
    # Assets
    assets = Account.objects.filter(account_type='asset', is_active=True)
    total_assets = assets.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

    # Liabilities
    liabilities = Account.objects.filter(account_type='liability', is_active=True)
    total_liabilities = liabilities.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

    # Equity
    equity = Account.objects.filter(account_type='equity', is_active=True)
    total_equity = equity.aggregate(total=Sum('balance'))['total'] or Decimal('0.00')

    context = {
        'assets': assets,
        'liabilities': liabilities,
        'equity': equity,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'total_equity': total_equity,
        'start_date': start_date,
        'end_date': end_date,
        'title': 'Balance Sheet'
    }
    return render(request, 'finance/balance_sheet.html', context)


def generate_income_statement(request, start_date=None, end_date=None):
    """Generate income statement report"""
    # Revenue accounts
    revenue_accounts = Account.objects.filter(account_type='revenue', is_active=True)
    total_revenue = Decimal('0.00')
    revenue_data = []

    for account in revenue_accounts:
        balance = account.balance
        if balance != 0:
            revenue_data.append({'account': account, 'amount': balance})
            total_revenue += balance

    # Expense accounts
    expense_accounts = Account.objects.filter(account_type='expense', is_active=True)
    total_expenses = Decimal('0.00')
    expense_data = []

    for account in expense_accounts:
        balance = account.balance
        if balance != 0:
            expense_data.append({'account': account, 'amount': balance})
            total_expenses += balance

    net_income = total_revenue - total_expenses

    context = {
        'revenue_data': revenue_data,
        'expense_data': expense_data,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'start_date': start_date,
        'end_date': end_date,
        'title': 'Income Statement'
    }
    return render(request, 'finance/income_statement.html', context)


def generate_cash_flow(request, start_date=None, end_date=None):
    """Generate cash flow statement report"""
    # This is a simplified cash flow statement
    # In a real implementation, this would be more complex

    # Operating activities (simplified)
    operating_cash_flow = Decimal('0.00')

    # Investing activities (simplified)
    investing_cash_flow = Decimal('0.00')

    # Financing activities (simplified)
    financing_cash_flow = Decimal('0.00')

    net_cash_flow = operating_cash_flow + investing_cash_flow + financing_cash_flow

    context = {
        'operating_cash_flow': operating_cash_flow,
        'investing_cash_flow': investing_cash_flow,
        'financing_cash_flow': financing_cash_flow,
        'net_cash_flow': net_cash_flow,
        'start_date': start_date,
        'end_date': end_date,
        'title': 'Cash Flow Statement'
    }
    return render(request, 'finance/cash_flow.html', context)


@login_required
def export_trial_balance_csv(request):
    """Export trial balance to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="trial_balance.csv"'

    writer = csv.writer(response)
    writer.writerow(['Account Code', 'Account Name', 'Debit', 'Credit'])

    accounts = Account.objects.filter(is_active=True)
    for account in accounts:
        balance = account.balance
        debit = balance if balance > 0 else Decimal('0.00')
        credit = abs(balance) if balance < 0 else Decimal('0.00')

        if balance != 0:
            writer.writerow([
                account.code,
                account.name,
                f"{debit:.2f}",
                f"{credit:.2f}"
            ])

    return response


@login_required
def account_transfer(request):
    """Transfer amounts between accounts"""
    if request.method == 'POST':
        form = AccountTransferForm(request.POST)
        if form.is_valid():
            from_account = form.cleaned_data['from_account']
            to_account = form.cleaned_data['to_account']
            amount = form.cleaned_data['amount']
            description = form.cleaned_data['description']
            transfer_date = form.cleaned_data['transfer_date']

            with transaction.atomic():
                # Debit from source account
                Transaction.objects.create(
                    date=transfer_date,
                    description=f"Transfer to {to_account.name}: {description}",
                    account=from_account,
                    transaction_type='debit',
                    amount=amount,
                    created_by=request.user
                )

                # Credit to destination account
                Transaction.objects.create(
                    date=transfer_date,
                    description=f"Transfer from {from_account.name}: {description}",
                    account=to_account,
                    transaction_type='credit',
                    amount=amount,
                    created_by=request.user
                )

            messages.success(request, f'Amount of ${amount} transferred successfully.')
            return redirect('finance_dashboard')
    else:
        form = AccountTransferForm()

    context = {
        'form': form,
        'title': 'Account Transfer'
    }
    return render(request, 'finance/account_transfer.html', context)
