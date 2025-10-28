from django import forms
from django.forms import inlineformset_factory
from .models import Account, Transaction, JournalEntry, JournalEntryLine, Budget, BudgetLine, TaxRate, FinancialPeriod


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = [
            'code', 'name', 'account_type', 'description', 'is_active',
            'parent_account'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'date', 'description', 'reference_number', 'account',
            'transaction_type', 'amount'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }


class JournalEntryForm(forms.ModelForm):
    class Meta:
        model = JournalEntry
        fields = [
            'date', 'description', 'reference_number'
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class JournalEntryLineForm(forms.ModelForm):
    class Meta:
        model = JournalEntryLine
        fields = ['account', 'transaction_type', 'amount', 'description']
        widgets = {
            'amount': forms.NumberInput(attrs={'step': '0.01'}),
        }


# Formset for journal entry lines
JournalEntryLineFormSet = inlineformset_factory(
    JournalEntry,
    JournalEntryLine,
    form=JournalEntryLineForm,
    extra=2,
    can_delete=True
)


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = [
            'name', 'description', 'start_date', 'end_date', 'status'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class BudgetLineForm(forms.ModelForm):
    class Meta:
        model = BudgetLine
        fields = ['account', 'budgeted_amount', 'period']
        widgets = {
            'budgeted_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'period': forms.DateInput(attrs={'type': 'date'}),
        }


# Formset for budget lines
BudgetLineFormSet = inlineformset_factory(
    Budget,
    BudgetLine,
    form=BudgetLineForm,
    extra=1,
    can_delete=True
)


class TaxRateForm(forms.ModelForm):
    class Meta:
        model = TaxRate
        fields = [
            'name', 'code', 'rate', 'description', 'is_active',
            'applicable_to_sales', 'applicable_to_purchases',
            'effective_from', 'effective_to'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'rate': forms.NumberInput(attrs={'step': '0.01'}),
            'effective_from': forms.DateInput(attrs={'type': 'date'}),
            'effective_to': forms.DateInput(attrs={'type': 'date'}),
        }


class FinancialPeriodForm(forms.ModelForm):
    class Meta:
        model = FinancialPeriod
        fields = ['name', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class FinancialReportForm(forms.Form):
    """Form for generating financial reports"""
    report_type = forms.ChoiceField(
        choices=[
            ('balance_sheet', 'Balance Sheet'),
            ('income_statement', 'Income Statement'),
            ('cash_flow', 'Cash Flow Statement'),
            ('trial_balance', 'Trial Balance'),
        ]
    )
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    account_filter = forms.ModelMultipleChoiceField(
        queryset=Account.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )


class AccountTransferForm(forms.Form):
    """Form for transferring amounts between accounts"""
    from_account = forms.ModelChoiceField(
        queryset=Account.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    to_account = forms.ModelChoiceField(
        queryset=Account.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01'})
    )
    description = forms.CharField(
        max_length=500,
        widget=forms.Textarea(attrs={'rows': 3})
    )
    transfer_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )