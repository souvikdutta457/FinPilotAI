"""
analytics.py
-------------
FinPilot AI Analytics Engine
Reads Excel transactions and creates financial analytics.
"""

import matplotlib.pyplot as plt
from collections import defaultdict

from transactions import get_all_transactions


# -------------------------------------------------
# EXPENSE BY CATEGORY
# -------------------------------------------------

def get_expense_by_category():

    transactions = get_all_transactions()

    expenses = defaultdict(float)

    for row in transactions:

        transaction_type = row[1]
        category = row[2]
        amount = row[4]

        if transaction_type == "Expense":
            expenses[category] += float(amount or 0)

    return dict(expenses)



# -------------------------------------------------
# MONTHLY EXPENSE TREND
# -------------------------------------------------

def get_monthly_expenses():

    transactions = get_all_transactions()

    monthly = defaultdict(float)

    for row in transactions:

        transaction_type = row[1]
        amount = float(row[4] or 0)

        month = row[7]

        # Clean invalid month values
        if month is None or str(month).strip().lower() in (
            "",
            "none",
            "unknown",
            "not specified"
        ):
            month = "Unknown"

        month = str(month)

        if transaction_type == "Expense":
            monthly[month] += amount

    return dict(monthly)



# -------------------------------------------------
# INCOME VS EXPENSE
# -------------------------------------------------

def get_income_expense():

    transactions = get_all_transactions()

    data = defaultdict(
        lambda: {
            "Income": 0,
            "Expense": 0
        }
    )

    for row in transactions:

        month = row[7]

        # Clean invalid month values
        if month is None or str(month).strip().lower() in (
            "",
            "none",
            "unknown",
            "not specified"
        ):
            month = "Unknown"

        month = str(month)

        amount = float(row[4] or 0)
        transaction_type = row[1]

        if transaction_type == "Income":
            data[month]["Income"] += amount

        elif transaction_type == "Expense":
            data[month]["Expense"] += amount

    return dict(data)



# -------------------------------------------------
# CHARTS
# -------------------------------------------------

def create_expense_pie_chart():

    data = get_expense_by_category()

    if not data:
        return None


    fig, ax = plt.subplots(figsize=(5,5))


    ax.pie(
        data.values(),
        labels=data.keys(),
        autopct="%1.1f%%"
    )

    ax.set_title(
        "Expense Breakdown"
    )


    return fig



def create_monthly_expense_chart():

    data = get_monthly_expenses()

    if not data:
        return None

    months = list(map(str, data.keys()))
    amounts = list(data.values())

    fig, ax = plt.subplots(figsize=(7, 4))

    ax.bar(months, amounts)

    ax.set_title("Monthly Expenses")
    ax.set_ylabel("Amount (₹)")
    plt.xticks(rotation=45)

    return fig



def create_income_expense_chart():

    data = get_income_expense()


    if not data:
        return None


    months = list(data.keys())


    income = [
        data[m]["Income"]
        for m in months
    ]

    expense = [
        data[m]["Expense"]
        for m in months
    ]


    fig, ax = plt.subplots(figsize=(7,4))


    ax.plot(
        months,
        income,
        marker="o",
        label="Income"
    )

    ax.plot(
        months,
        expense,
        marker="o",
        label="Expense"
    )


    ax.set_title(
        "Income vs Expense"
    )


    ax.legend()

    plt.xticks(rotation=45)


    return fig