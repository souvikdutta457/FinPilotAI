import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from analytics_engine import *

print("Expense Breakdown:")
print(get_expense_by_category())

print("\nMonthly Expenses:")
print(get_monthly_expenses())

print("\nIncome vs Expense:")
print(get_income_expense())


create_expense_pie_chart()
create_monthly_expense_chart()
create_income_expense_chart()


import matplotlib.pyplot as plt
plt.show()