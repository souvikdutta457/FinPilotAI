"""
dashboard_widgets.py
---------------------

FinPilot AI

Reusable CustomTkinter widgets for the dashboard UI. These mirror the
exact widget behavior and data formats already used in gui.py:

- DashboardCard        -> single stat card (Income/Expense/etc.)
- InsightsPanel         -> renders dashboard.generate_ai_insights() output
- ExpenseBreakdownPanel -> renders dashboard.get_expense_breakdown() output
- RecentTransactionsPanel -> renders transactions.get_recent_transactions()
                             (and search_transactions()-derived dicts)

No backend logic lives here. These widgets only display data that is
handed to them by the caller (gui.py).
"""

from __future__ import annotations

from typing import Any

import customtkinter as ctk

# ---------------------------------------------------------------- #
# SHARED STYLE CONSTANTS (match gui.py theme)
# ---------------------------------------------------------------- #

CARD_BG = "#1a1a1a"
ROW_BG = "#232323"
MUTED_TEXT = "#9a9a9a"
EMPTY_TEXT = "#8a8a8a"

TYPE_COLORS: dict[str, str] = {
    "Income": "#4ade80",
    "Expense": "#f87171",
    "Savings": "#60a5fa",
    "Debt": "#fbbf24",
}


# ---------------------------------------------------------------- #
# DASHBOARD SUMMARY CARD
# ---------------------------------------------------------------- #

class DashboardCard(ctk.CTkFrame):
    """
    A single dashboard stat card (e.g. Income, Expense, Savings, Debt,
    Balance).

    Usage:
        card = DashboardCard(parent, title="Income", accent="#4ade80")
        card.set_value(12500.0)
    """

    def __init__(self, master: Any, title: str, accent: str) -> None:
        super().__init__(master, corner_radius=14, fg_color=CARD_BG)

        self._accent = accent

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=MUTED_TEXT,
        )
        self.title_label.pack(anchor="w", padx=16, pady=(14, 0))

        self.value_label = ctk.CTkLabel(
            self,
            text="₹0.00",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=accent,
        )
        self.value_label.pack(anchor="w", padx=16, pady=(2, 14))

    def set_value(self, value: float | int | None) -> None:
        """Safely formats and displays a currency value. Handles None,
        missing, or non-numeric input without raising."""

        try:
            formatted = f"₹{float(value or 0):,.2f}"
        except (TypeError, ValueError):
            formatted = "₹0.00"

        self.value_label.configure(text=formatted)

    def set_title(self, title: str) -> None:
        """Updates the card's title text."""

        self.title_label.configure(text=title)


# ---------------------------------------------------------------- #
# AI / FINANCIAL INSIGHTS PANEL
# ---------------------------------------------------------------- #

class InsightsPanel(ctk.CTkFrame):
    """
    Displays a scrollable list of AI-generated insight strings, as
    returned by dashboard.generate_ai_insights() (already formatted
    with ⚠ / ✅ / ✔ prefixes -- rendered verbatim, no parsing).

    Usage:
        panel = InsightsPanel(parent)
        panel.set_data(dashboard.generate_ai_insights())
    """

    def __init__(self, master: Any, height: int = 220) -> None:
        super().__init__(master, corner_radius=14, fg_color=CARD_BG)
        self.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkLabel(
            self,
            text="AI Insights",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        heading.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self._container = ctk.CTkScrollableFrame(
            self, fg_color="transparent", height=height
        )
        self._container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self._container.grid_columnconfigure(0, weight=1)

    def set_data(self, insights: list[str] | None) -> None:
        """Renders the given list of insight strings. Safely handles
        None or an empty list."""

        for widget in self._container.winfo_children():
            widget.destroy()

        insights = insights or []

        if not insights:
            ctk.CTkLabel(
                self._container,
                text="No insights available.",
                text_color=EMPTY_TEXT,
            ).grid(row=0, column=0, sticky="w")
            return

        for i, text in enumerate(insights):
            ctk.CTkLabel(
                self._container,
                text=str(text),
                anchor="w",
                justify="left",
                wraplength=340,
            ).grid(row=i, column=0, sticky="w", pady=4)


# ---------------------------------------------------------------- #
# EXPENSE / BUDGET PROGRESS PANEL
# ---------------------------------------------------------------- #

class ExpenseBreakdownPanel(ctk.CTkFrame):
    """
    Displays budget-vs-actual progress bars per category, as returned
    by dashboard.get_expense_breakdown():

        {category: {"budget": float, "actual": float}, ...}

    Usage:
        panel = ExpenseBreakdownPanel(parent)
        panel.set_data(dashboard.get_expense_breakdown())
    """

    def __init__(self, master: Any) -> None:
        super().__init__(master, corner_radius=14, fg_color=CARD_BG)
        self.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkLabel(
            self,
            text="Expense Breakdown (Budget vs Actual)",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        heading.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self._container = ctk.CTkFrame(self, fg_color="transparent")
        self._container.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
        self._container.grid_columnconfigure(0, weight=1)

    def set_data(self, breakdown: dict[str, dict[str, float]] | None) -> None:
        """Renders one progress row per category. Safely handles None
        or an empty dict, and non-numeric/missing budget or actual
        values within each category."""

        for widget in self._container.winfo_children():
            widget.destroy()

        breakdown = breakdown or {}

        if not breakdown:
            ctk.CTkLabel(
                self._container,
                text="No expense data available.",
                text_color=EMPTY_TEXT,
            ).grid(row=0, column=0, sticky="w")
            return

        for i, (category, values) in enumerate(breakdown.items()):
            values = values or {}
            budget = values.get("budget", 0) or 0
            actual = values.get("actual", 0) or 0

            try:
                budget = float(budget)
            except (TypeError, ValueError):
                budget = 0.0
            try:
                actual = float(actual)
            except (TypeError, ValueError):
                actual = 0.0

            row_frame = ctk.CTkFrame(self._container, fg_color="transparent")
            row_frame.grid(row=i, column=0, sticky="ew", pady=4)
            row_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row_frame,
                text=str(category),
                anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(
                row_frame,
                text=f"Budget ₹{budget:,.0f}   Actual ₹{actual:,.0f}",
                anchor="e",
                text_color=MUTED_TEXT,
                font=ctk.CTkFont(size=11),
            ).grid(row=0, column=1, sticky="e")

            try:
                progress = min(actual / budget, 1.5) if budget else 0.0
            except ZeroDivisionError:
                progress = 0.0

            bar_color = "#f87171" if progress > 1 else "#4ade80"
            bar = ctk.CTkProgressBar(row_frame, progress_color=bar_color)
            bar.set(min(progress, 1.0))
            bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))


# ---------------------------------------------------------------- #
# RECENT TRANSACTIONS PANEL
# ---------------------------------------------------------------- #

class RecentTransactionsPanel(ctk.CTkFrame):
    """
    Displays a scrollable list of transaction rows, matching the dict
    shape returned by transactions.get_recent_transactions():

        {"date", "type", "category", "merchant", "amount", "description"}

    Also compatible with rows built from excel_engine.search_transactions()
    tuples once mapped to the same dict shape by the caller.

    Usage:
        panel = RecentTransactionsPanel(parent)
        panel.set_data(transactions.get_recent_transactions(limit=15))
    """

    def __init__(self, master: Any, height: int = 280) -> None:
        super().__init__(master, corner_radius=14, fg_color=CARD_BG)
        self.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkLabel(
            self,
            text="Recent Transactions",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        heading.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        self._container = ctk.CTkScrollableFrame(
            self, fg_color="transparent", height=height
        )
        self._container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))
        self._container.grid_columnconfigure(0, weight=1)

    def set_data(self, rows: list[dict[str, Any]] | None) -> None:
        """Renders one row per transaction dict. Safely handles None,
        an empty list, and missing/non-numeric amount values."""

        for widget in self._container.winfo_children():
            widget.destroy()

        rows = rows or []

        if not rows:
            ctk.CTkLabel(
                self._container,
                text="No transactions found.",
                text_color=EMPTY_TEXT,
            ).grid(row=0, column=0, sticky="w", pady=8)
            return

        for i, txn in enumerate(rows):
            txn = txn or {}
            row_frame = ctk.CTkFrame(self._container, fg_color=ROW_BG, corner_radius=10)
            row_frame.grid(row=i, column=0, sticky="ew", pady=4)
            row_frame.grid_columnconfigure(1, weight=1)

            txn_type = str(txn.get("type", ""))
            accent = TYPE_COLORS.get(txn_type, "#d1d1d1")

            amount = txn.get("amount", 0)
            try:
                amount_text = f"₹{float(amount or 0):,.2f}"
            except (TypeError, ValueError):
                amount_text = "₹0.00"

            merchant = txn.get("merchant") or "Unspecified"
            category = txn.get("category") or ""
            date_text = str(txn.get("date", ""))

            ctk.CTkLabel(
                row_frame,
                text=f"{merchant} — {category}",
                anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))

            ctk.CTkLabel(
                row_frame,
                text=date_text,
                anchor="w",
                text_color=MUTED_TEXT,
                font=ctk.CTkFont(size=11),
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

            ctk.CTkLabel(
                row_frame,
                text=txn_type,
                text_color=accent,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).grid(row=0, column=1, sticky="e", padx=(0, 12), pady=(8, 0))

            ctk.CTkLabel(
                row_frame,
                text=amount_text,
                text_color=accent,
                font=ctk.CTkFont(size=13, weight="bold"),
            ).grid(row=1, column=1, sticky="e", padx=(0, 12), pady=(0, 8))