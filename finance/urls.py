from django.urls import path
from . import views

urlpatterns = [
    # Finance Dashboard
    path('', views.finance_dashboard, name='finance_dashboard'),

    # Account URLs
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<int:pk>/', views.account_detail, name='account_detail'),
    path('accounts/<int:pk>/update/', views.account_update, name='account_update'),

    # Transaction URLs
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),

    # Journal Entry URLs
    path('journal-entries/', views.journal_entry_list, name='journal_entry_list'),
    path('journal-entries/create/', views.journal_entry_create, name='journal_entry_create'),
    path('journal-entries/<int:pk>/', views.journal_entry_detail, name='journal_entry_detail'),
    path('journal-entries/<int:pk>/post/', views.journal_entry_post, name='journal_entry_post'),

    # Budget URLs
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/create/', views.budget_create, name='budget_create'),
    path('budgets/<int:pk>/', views.budget_detail, name='budget_detail'),

    # Tax Rate URLs
    path('tax-rates/', views.tax_rate_list, name='tax_rate_list'),
    path('tax-rates/create/', views.tax_rate_create, name='tax_rate_create'),

    # Financial Reports
    path('reports/', views.financial_reports, name='financial_reports'),
    path('reports/trial-balance/', views.generate_trial_balance, name='trial_balance'),
    path('reports/balance-sheet/', views.generate_balance_sheet, name='balance_sheet'),
    path('reports/income-statement/', views.generate_income_statement, name='income_statement'),
    path('reports/cash-flow/', views.generate_cash_flow, name='cash_flow'),

    # Export URLs
    path('export/trial-balance/csv/', views.export_trial_balance_csv, name='export_trial_balance_csv'),

    # Account Transfer
    path('transfer/', views.account_transfer, name='account_transfer'),
]