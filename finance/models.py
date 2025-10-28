from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Account(models.Model):
    """Chart of accounts for financial tracking"""
    ACCOUNT_TYPES = [
        ('asset', 'Asset'),
        ('liability', 'Liability'),
        ('equity', 'Equity'),
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
    ]

    code = models.CharField(max_length=20, unique=True, help_text="Account code (e.g., 1000, 2000)")
    name = models.CharField(max_length=200, help_text="Account name")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    parent_account = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='sub_accounts')

    # Balance tracking
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_accounts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'

    def __str__(self):
        return f"{self.code} - {self.name}"

    @property
    def full_name(self):
        """Return full hierarchical account name"""
        if self.parent_account:
            return f"{self.parent_account.name} > {self.name}"
        return self.name


class Transaction(models.Model):
    """Financial transaction entries"""
    TRANSACTION_TYPES = [
        ('debit', 'Debit'),
        ('credit', 'Credit'),
    ]

    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=500)
    reference_number = models.CharField(max_length=100, blank=True, help_text="Check number, invoice number, etc.")

    # Transaction details
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # Related documents
    sales_order = models.ForeignKey('sales.SalesOrder', on_delete=models.SET_NULL, null=True, blank=True)
    purchase_order = models.ForeignKey('purchase.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)
    invoice = models.ForeignKey('sales.Invoice', on_delete=models.SET_NULL, null=True, blank=True)

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'

    def __str__(self):
        return f"{self.transaction_type.title()} - {self.account.name} - ${self.amount}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update account balance
        self.update_account_balance()

    def update_account_balance(self):
        """Update the account balance based on transaction type"""
        if self.transaction_type == 'debit':
            # For assets and expenses: debit increases balance
            if self.account.account_type in ['asset', 'expense']:
                self.account.balance += self.amount
            # For liabilities, equity, revenue: debit decreases balance
            else:
                self.account.balance -= self.amount
        else:  # credit
            # For assets and expenses: credit decreases balance
            if self.account.account_type in ['asset', 'expense']:
                self.account.balance -= self.amount
            # For liabilities, equity, revenue: credit increases balance
            else:
                self.account.balance += self.amount

        self.account.save()


class JournalEntry(models.Model):
    """Double-entry journal entries"""
    date = models.DateField(default=timezone.now)
    description = models.TextField()
    reference_number = models.CharField(max_length=100, unique=True)

    # Journal entry status
    is_posted = models.BooleanField(default=False)
    posted_date = models.DateTimeField(null=True, blank=True)

    # Related documents
    sales_order = models.ForeignKey('sales.SalesOrder', on_delete=models.SET_NULL, null=True, blank=True)
    purchase_order = models.ForeignKey('purchase.PurchaseOrder', on_delete=models.SET_NULL, null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_journal_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name = 'Journal Entry'
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        return f"JE-{self.reference_number} - {self.description[:50]}"

    @property
    def total_debit(self):
        return self.lines.filter(transaction_type='debit').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

    @property
    def total_credit(self):
        return self.lines.filter(transaction_type='credit').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

    @property
    def is_balanced(self):
        return self.total_debit == self.total_credit


class JournalEntryLine(models.Model):
    """Individual lines in a journal entry"""
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=[('debit', 'Debit'), ('credit', 'Credit')])
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Journal Entry Line'
        verbose_name_plural = 'Journal Entry Lines'

    def __str__(self):
        return f"{self.transaction_type.title()} - {self.account.name} - ${self.amount}"


class Budget(models.Model):
    """Budget planning and tracking"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Budget period
    start_date = models.DateField()
    end_date = models.DateField()

    # Budget status
    is_active = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('active', 'Active'),
            ('closed', 'Closed'),
        ],
        default='draft'
    )

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_budgets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Budget'
        verbose_name_plural = 'Budgets'

    def __str__(self):
        return f"{self.name} ({self.start_date.year})"


class BudgetLine(models.Model):
    """Individual budget line items"""
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    # Budget amounts
    budgeted_amount = models.DecimalField(max_digits=12, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Period (for monthly budgets)
    period = models.DateField(null=True, blank=True, help_text="Specific month for this budget line")

    class Meta:
        verbose_name = 'Budget Line'
        verbose_name_plural = 'Budget Lines'

    def __str__(self):
        return f"{self.budget.name} - {self.account.name}"

    @property
    def variance(self):
        return self.actual_amount - self.budgeted_amount

    @property
    def variance_percentage(self):
        if self.budgeted_amount != 0:
            return (self.variance / self.budgeted_amount) * 100
        return 0


class TaxRate(models.Model):
    """Tax rates for different tax types"""
    name = models.CharField(max_length=100, help_text="Tax name (e.g., VAT, Sales Tax)")
    code = models.CharField(max_length=20, unique=True, help_text="Tax code")
    rate = models.DecimalField(max_digits=5, decimal_places=2, help_text="Tax rate percentage")
    description = models.TextField(blank=True)

    # Tax applicability
    is_active = models.BooleanField(default=True)
    applicable_to_sales = models.BooleanField(default=True)
    applicable_to_purchases = models.BooleanField(default=True)

    # Effective dates
    effective_from = models.DateField(default=timezone.now)
    effective_to = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tax_rates')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Tax Rate'
        verbose_name_plural = 'Tax Rates'

    def __str__(self):
        return f"{self.name} ({self.rate}%)"

    @property
    def is_current(self):
        today = timezone.now().date()
        if self.effective_to and today > self.effective_to:
            return False
        return today >= self.effective_from


class FinancialPeriod(models.Model):
    """Accounting periods for financial reporting"""
    name = models.CharField(max_length=100, help_text="Period name (e.g., January 2024)")
    start_date = models.DateField()
    end_date = models.DateField()

    # Period status
    is_closed = models.BooleanField(default=False)
    closed_date = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='closed_periods')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_periods')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Financial Period'
        verbose_name_plural = 'Financial Periods'

    def __str__(self):
        return self.name

    @property
    def is_current(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
