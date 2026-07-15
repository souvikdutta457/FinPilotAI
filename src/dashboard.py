"""
dashboard.py
------------
FinPilot AI
Reads dashboard information and calculates dynamic totals from the Transactions sheet.
"""

from datetime import datetime
from typing import Any
from openpyxl import load_workbook
import excel_engine

# ---------------- CONFIG ---------------- #
EXCEL_FILE = "data/Budget Tracker Final...xlsx"

MONTH_SHEETS = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

def _current_month_sheet() -> str:
    return MONTH_SHEETS[datetime.now().month]

# ---------------- DASHBOARD ---------------- #

def get_dashboard_data(month_sheet: str | None = None) -> dict[str, float]:
    """Calculates the main dashboard numbers dynamically from the Transactions sheet."""
    target_month = month_sheet or _current_month_sheet()
    
    # Load all transactions to calculate dynamic values
    all_txns = excel_engine.read_transactions()
    
    # Filter transactions matching this specific month name (column 8 index 7)
    month_txns = [t for t in all_txns if len(t) > 7 and str(t[7]).strip().lower() == target_month.lower()]
    
    income = sum(float(t[4] or 0) for t in month_txns if t[1] == "Income")
    expense = sum(float(t[4] or 0) for t in month_txns if t[1] == "Expense")
    debt = sum(float(t[4] or 0) for t in month_txns if t[1] == "Debt")
    savings = sum(float(t[4] or 0) for t in month_txns if t[1] == "Savings")
    
    # If no transactions exist yet for a newly selected month, fallback to sheet baselines
    if income == 0 and expense == 0 and debt == 0 and savings == 0:
        workbook = load_workbook(EXCEL_FILE, data_only=True)
        try:
            sheet = workbook[target_month]
            income = sheet["D8"].value or 0
            expense = sheet["D9"].value or 0
            debt = sheet["D10"].value or 0
            savings = sheet["D11"].value or 0
        except Exception:
            pass
        finally:
            workbook.close()

    return {
        "income": income,
        "expense": expense,
        "debt": debt,
        "savings": savings,
        "balance": income - expense - debt
    }

# ---------------- EXPENSE BREAKDOWN ---------------- #

def get_expense_breakdown(month_sheet: str | None = None) -> dict[str, dict[str, float]]:
    """Fetches static budgets from the month sheet, but calculates actual values dynamically."""
    target_month = month_sheet or _current_month_sheet()
    
    # 1. Fetch Budgets from the specific month sheet
    workbook = load_workbook(EXCEL_FILE, data_only=True)
    rows = {
        "Bus": 16, "Uber/Rapido": 17, "Dining Out": 18,
        "Other Expenses": 19, "Food Outside": 20, "Food Order": 21,
    }
    
    expenses = {}
    try:
        sheet = workbook[target_month]
        for category, row in rows.items():
            expenses[category] = {
                "budget": sheet[f"H{row}"].value or 0,
                "actual": 0.0  # Will be calculated dynamically below
            }
    except Exception:
        # Fallback if sheet doesn't exist yet
        for category in rows:
            expenses[category] = {"budget": 0.0, "actual": 0.0}
    finally:
        workbook.close()
        
    # 2. Calculate Actuals dynamically from Transactions
    all_txns = excel_engine.read_transactions()
    for t in all_txns:
        if len(t) > 7 and str(t[7]).strip().lower() == target_month.lower():
            t_type = t[1]
            t_category = t[2]
            t_amount = float(t[4] or 0)
            
            if t_type == "Expense" and t_category in expenses:
                expenses[t_category]["actual"] += t_amount
            elif t_type == "Expense" and t_category not in expenses:
                # Catch-all for miscellaneous custom categories into Other Expenses
                expenses["Other Expenses"]["actual"] += t_amount

    return expenses

# ---------------- AI INSIGHTS ---------------- #

def generate_ai_insights(month_sheet: str | None = None) -> list[str]:
    expenses = get_expense_breakdown(month_sheet)
    insights = []

    for category, values in expenses.items():
        budget = values["budget"]
        actual = values["actual"]

        if actual > budget:
            insights.append(f"⚠ {category} exceeded budget by ₹{actual - budget:,.2f}")
        elif actual < budget:
            insights.append(f"✅ {category} is under budget by ₹{budget - actual:,.2f}")
        else:
            insights.append(f"✔ {category} is exactly on budget.")

    return insights