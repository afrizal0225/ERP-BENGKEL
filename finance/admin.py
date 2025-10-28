from django.contrib import admin
from .models import (
    Account, Transaction, JournalEntry, JournalEntryLine,
    Budget, BudgetLine, TaxRate, FinancialPeriod
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_type', 'balance', 'is_active', 'parent_account']
    list_filter = ['account_type', 'is_active', 'parent_account']
    search_fields = ['code', 'name']
    readonly_fields = ['balance', 'last_updated']
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'account_type', 'description')
        }),
        ('Hierarchy', {
            'fields': ('parent_account',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Balance Information', {
            'fields': ('balance', 'last_updated'),
            'classes': ('collapse',)
        }),
    )


class TransactionInline(admin.TabularInline):
    model = Transaction
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['date', 'description', 'account', 'transaction_type', 'amount', 'created_by']
    list_filter = ['transaction_type', 'date', 'account__account_type']
    search_fields = ['description', 'reference_number', 'account__name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Transaction Details', {
            'fields': ('date', 'description', 'reference_number')
        }),
        ('Financial Information', {
            'fields': ('account', 'transaction_type', 'amount')
        }),
        ('Related Documents', {
            'fields': ('sales_order', 'purchase_order', 'invoice'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class JournalEntryLineInline(admin.TabularInline):
    model = JournalEntryLine
    extra = 1


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ['reference_number', 'date', 'description', 'is_posted', 'total_debit', 'total_credit', 'is_balanced']
    list_filter = ['is_posted', 'date']
    search_fields = ['reference_number', 'description']
    readonly_fields = ['is_balanced', 'total_debit', 'total_credit', 'posted_date']
    inlines = [JournalEntryLineInline]
    fieldsets = (
        ('Journal Entry Information', {
            'fields': ('date', 'description', 'reference_number')
        }),
        ('Status', {
            'fields': ('is_posted', 'posted_date')
        }),
        ('Related Documents', {
            'fields': ('sales_order', 'purchase_order'),
            'classes': ('collapse',)
        }),
        ('Balance Check', {
            'fields': ('total_debit', 'total_credit', 'is_balanced'),
            'classes': ('collapse',)
        }),
    )


@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    list_display = ['journal_entry', 'account', 'transaction_type', 'amount']
    list_filter = ['transaction_type', 'account__account_type']
    search_fields = ['journal_entry__reference_number', 'account__name']


class BudgetLineInline(admin.TabularInline):
    model = BudgetLine
    extra = 1


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'status', 'is_active']
    list_filter = ['status', 'is_active', 'start_date']
    search_fields = ['name', 'description']
    inlines = [BudgetLineInline]
    fieldsets = (
        ('Budget Information', {
            'fields': ('name', 'description')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date')
        }),
        ('Status', {
            'fields': ('is_active', 'status')
        }),
    )


@admin.register(BudgetLine)
class BudgetLineAdmin(admin.ModelAdmin):
    list_display = ['budget', 'account', 'budgeted_amount', 'actual_amount', 'variance']
    list_filter = ['budget__status', 'account__account_type']
    search_fields = ['budget__name', 'account__name']
    readonly_fields = ['variance']


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'rate', 'is_active', 'is_current', 'effective_from', 'effective_to']
    list_filter = ['is_active', 'applicable_to_sales', 'applicable_to_purchases']
    search_fields = ['name', 'code']
    readonly_fields = ['is_current']
    fieldsets = (
        ('Tax Information', {
            'fields': ('name', 'code', 'rate', 'description')
        }),
        ('Applicability', {
            'fields': ('applicable_to_sales', 'applicable_to_purchases')
        }),
        ('Effective Period', {
            'fields': ('effective_from', 'effective_to', 'is_current')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
    )


@admin.register(FinancialPeriod)
class FinancialPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_closed', 'is_current']
    list_filter = ['is_closed', 'start_date']
    search_fields = ['name']
    readonly_fields = ['is_current', 'closed_date']
    fieldsets = (
        ('Period Information', {
            'fields': ('name', 'start_date', 'end_date', 'is_current')
        }),
        ('Closure', {
            'fields': ('is_closed', 'closed_date', 'closed_by'),
            'classes': ('collapse',)
        }),
    )
