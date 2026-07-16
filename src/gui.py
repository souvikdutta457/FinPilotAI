"""
gui.py
------
FinPilot AI - Desktop GUI

Built with CustomTkinter. Connects directly to the existing backend
modules (dashboard.py, excel_engine.py, transactions.py) with no
changes to their logic or data formats.
"""

from __future__ import annotations

from datetime import datetime
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

import dashboard
import excel_engine
import transactions

# ---------------------------------------------------------------- #
# THEME
# ---------------------------------------------------------------- #

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

MONTH_NAMES = list(dashboard.MONTH_SHEETS.values())


# ---------------------------------------------------------------- #
# DASHBOARD CARD WIDGET
# ---------------------------------------------------------------- #

class DashboardCard(ctk.CTkFrame):
    """A single stat card (Income / Expense / Savings / Debt / Balance)."""

    def __init__(self, master: Any, title: str, accent: str) -> None:
        super().__init__(master, corner_radius=14, fg_color="#1f1f1f")

        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#a0a0a0",
        )
        self.title_label.pack(anchor="w", padx=16, pady=(14, 0))

        self.value_label = ctk.CTkLabel(
            self,
            text="₹0",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=accent,
        )
        self.value_label.pack(anchor="w", padx=16, pady=(2, 14))

    def set_value(self, value: float) -> None:
        try:
            formatted = f"₹{value:,.2f}"
        except (TypeError, ValueError):
            formatted = "₹0.00"
        self.value_label.configure(text=formatted)


# ---------------------------------------------------------------- #
# MAIN APPLICATION
# ---------------------------------------------------------------- #

class FinPilotApp(ctk.CTk):

    def __init__(self) -> None:
        super().__init__()

        self.title("FinPilot AI - Personal Finance Dashboard")
        self.geometry("1200x780")
        self.minsize(1000, 700)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()

        self.refresh_all()

    # ------------------------------------------------------------ #
    # LAYOUT: HEADER
    # ------------------------------------------------------------ #

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 10))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="FinPilot AI",
            font=ctk.CTkFont(size=26, weight="bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Personal Finance Dashboard",
            font=ctk.CTkFont(size=13),
            text_color="#9a9a9a",
        )
        subtitle.grid(row=1, column=0, sticky="w")

        self.month_selector = ctk.CTkOptionMenu(
            header,
            values=MONTH_NAMES,
            command=self._on_month_change,
        )
        self.month_selector.set(dashboard._current_month_sheet())
        self.month_selector.grid(row=0, column=1, rowspan=2, sticky="e")

        refresh_btn = ctk.CTkButton(
            header, text="⟳ Refresh", width=100, command=self.refresh_all
        )
        refresh_btn.grid(row=0, column=2, rowspan=2, padx=(12, 0), sticky="e")

    def _on_month_change(self, _value: str) -> None:
        self.refresh_all()

    def _selected_month(self) -> str:
        return self.month_selector.get()

    def _year_for_selected_month(self, selected_month: str) -> int:
        """
        The Month dropdown only has month names (no year), so we infer the
        year: use the current year, unless the selected month is later in
        the calendar than today's month - in which case it must refer to
        last year (e.g. it's January 2026 and the user picks "December",
        that's December 2025, not a future December 2026).
        """
        now = datetime.now()
        month_number = {name: num for num, name in dashboard.MONTH_SHEETS.items()}.get(
            selected_month
        )

        if month_number is None:
            return now.year

        if month_number > now.month:
            return now.year - 1

        return now.year

    # ------------------------------------------------------------ #
    # LAYOUT: BODY
    # ------------------------------------------------------------ #

    def _build_body(self) -> None:
        body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)

        self._build_dashboard_cards(body)
        self._build_left_column(body)
        self._build_right_column(body)

    # ---- dashboard cards row ---- #

    def _build_dashboard_cards(self, parent: Any) -> None:
        cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
        cards_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))
        for i in range(5):
            cards_frame.grid_columnconfigure(i, weight=1)

        self.card_income = DashboardCard(cards_frame, "Income", "#4ade80")
        self.card_expense = DashboardCard(cards_frame, "Expense", "#f87171")
        self.card_savings = DashboardCard(cards_frame, "Savings", "#60a5fa")
        self.card_debt = DashboardCard(cards_frame, "Debt", "#fbbf24")
        self.card_balance = DashboardCard(cards_frame, "Balance", "#c084fc")

        cards = [
            self.card_income, self.card_expense, self.card_savings,
            self.card_debt, self.card_balance,
        ]
        for i, card in enumerate(cards):
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 8, 0))

    # ---- left column: transaction entry + recent transactions ---- #

    def _build_left_column(self, parent: Any) -> None:
        left = ctk.CTkFrame(parent, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(0, 12))
        left.grid_columnconfigure(0, weight=1)

        self._build_transaction_form(left)
        self._build_recent_transactions(left)

    def _build_transaction_form(self, parent: Any) -> None:
        frame = ctk.CTkFrame(parent, corner_radius=14, fg_color="#1a1a1a")
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        frame.grid_columnconfigure((0, 1), weight=1)

        heading = ctk.CTkLabel(
            frame, text="Add Transaction",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        heading.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 8))

        # Type
        ctk.CTkLabel(frame, text="Type").grid(row=1, column=0, sticky="w", padx=16)
        self.type_menu = ctk.CTkOptionMenu(
            frame, values=sorted(excel_engine.VALID_TYPES)
        )
        self.type_menu.set("Expense")
        self.type_menu.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Amount
        ctk.CTkLabel(frame, text="Amount").grid(row=1, column=1, sticky="w", padx=16)
        self.amount_entry = ctk.CTkEntry(frame, placeholder_text="0.00")
        self.amount_entry.grid(row=2, column=1, sticky="ew", padx=16, pady=(0, 10))

        # Category
        ctk.CTkLabel(frame, text="Category").grid(row=3, column=0, sticky="w", padx=16)
        self.category_entry = ctk.CTkEntry(frame, placeholder_text="e.g. Food Order")
        self.category_entry.grid(row=4, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Merchant
        ctk.CTkLabel(frame, text="Merchant").grid(row=3, column=1, sticky="w", padx=16)
        self.merchant_entry = ctk.CTkEntry(frame, placeholder_text="e.g. Domino's")
        self.merchant_entry.grid(row=4, column=1, sticky="ew", padx=16, pady=(0, 10))

        # Date
        ctk.CTkLabel(frame, text="Date (DD-MM-YYYY, blank = today)").grid(
            row=5, column=0, sticky="w", padx=16
        )
        self.date_entry = ctk.CTkEntry(frame, placeholder_text="today")
        self.date_entry.grid(row=6, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Description
        ctk.CTkLabel(frame, text="Description").grid(row=5, column=1, sticky="w", padx=16)
        self.description_entry = ctk.CTkEntry(frame, placeholder_text="optional note")
        self.description_entry.grid(row=6, column=1, sticky="ew", padx=16, pady=(0, 10))

        save_btn = ctk.CTkButton(
            frame, text="Save Transaction", command=self._on_save_transaction
        )
        save_btn.grid(row=7, column=0, columnspan=2, sticky="ew", padx=16, pady=(4, 16))

    def _on_save_transaction(self) -> None:
        amount_raw = self.amount_entry.get().strip()

        # The Month dropdown is the source of truth for which month/year
        # this transaction belongs to. Previously "month"/"year" were left
        # blank here, so excel_engine.normalize_transaction() derived them
        # from the transaction's date instead - and since the date field
        # defaults to "today", every transaction silently landed in the
        # real-world current month (e.g. July) no matter what month was
        # selected in the dropdown. We now pass the selected month through
        # explicitly so it's always what actually gets written to Excel.
        selected_month = self._selected_month()
        selected_year = self._year_for_selected_month(selected_month)

        transaction: dict[str, Any] = {
            "type": self.type_menu.get(),
            "amount": amount_raw,
            "category": self.category_entry.get().strip(),
            "merchant": self.merchant_entry.get().strip(),
            "date": self.date_entry.get().strip() or "today",
            "description": self.description_entry.get().strip(),
            "month": selected_month,
            "year": selected_year,
        }

        try:
            row = excel_engine.write_transaction(transaction)
        except FileNotFoundError as exc:
            messagebox.showerror("Excel File Missing", str(exc))
            return
        except KeyError as exc:
            messagebox.showerror("Sheet Error", str(exc))
            return
        except Exception as exc:  # noqa: BLE001 - surface any unexpected backend error
            messagebox.showerror("Error Saving Transaction", str(exc))
            return

        messagebox.showinfo("Saved", f"Transaction saved to row {row}.")
        self._clear_transaction_form()
        self.refresh_all()

    def _clear_transaction_form(self) -> None:
        self.amount_entry.delete(0, "end")
        self.category_entry.delete(0, "end")
        self.merchant_entry.delete(0, "end")
        self.date_entry.delete(0, "end")
        self.description_entry.delete(0, "end")
        self.type_menu.set("Expense")

    def _build_recent_transactions(self, parent: Any) -> None:
        frame = ctk.CTkFrame(parent, corner_radius=14, fg_color="#1a1a1a")
        frame.grid(row=1, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        header_row = ctk.CTkFrame(frame, fg_color="transparent")
        header_row.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        header_row.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkLabel(
            header_row, text="Recent Transactions",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        heading.grid(row=0, column=0, sticky="w")

        self.search_entry = ctk.CTkEntry(header_row, placeholder_text="Search transactions...")
        self.search_entry.grid(row=0, column=1, sticky="e", padx=(8, 8))
        self.search_entry.bind("<Return>", lambda _e: self._on_search())

        search_btn = ctk.CTkButton(header_row, text="Search", width=80, command=self._on_search)
        search_btn.grid(row=0, column=2, sticky="e")

        clear_btn = ctk.CTkButton(
            header_row, text="Clear", width=70, fg_color="#3a3a3a",
            command=self._clear_search,
        )
        clear_btn.grid(row=0, column=3, sticky="e", padx=(8, 0))

        self.transactions_list = ctk.CTkScrollableFrame(frame, fg_color="transparent", height=280)
        self.transactions_list.grid(row=1, column=0, sticky="nsew", padx=16, pady=(4, 16))
        self.transactions_list.grid_columnconfigure(0, weight=1)

    def _on_search(self) -> None:
        keyword = self.search_entry.get().strip()
        if not keyword:
            self._clear_search()
            return

        try:
            results = excel_engine.search_transactions(keyword)
        except FileNotFoundError as exc:
            messagebox.showerror("Excel File Missing", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Search Error", str(exc))
            return

        # search_transactions returns raw tuples in the same column
        # order as append_transaction writes them:
        # date, type, category, merchant, amount, description, confidence, month, year
        rows_as_dicts = [
            {
                "date": row[0],
                "type": row[1],
                "category": row[2],
                "merchant": row[3],
                "amount": row[4],
                "description": row[5] if len(row) > 5 else "",
            }
            for row in results
        ]
        self._render_transaction_rows(rows_as_dicts)

    def _clear_search(self) -> None:
        self.search_entry.delete(0, "end")
        self._load_recent_transactions()

    def _load_recent_transactions(self) -> None:
        try:
            recent = transactions.get_recent_transactions(limit=15)
        except FileNotFoundError as exc:
            messagebox.showerror("Excel File Missing", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error Loading Transactions", str(exc))
            return

        self._render_transaction_rows(recent)

    def _render_transaction_rows(self, rows: list[dict[str, Any]]) -> None:
        for widget in self.transactions_list.winfo_children():
            widget.destroy()

        if not rows:
            empty_label = ctk.CTkLabel(
                self.transactions_list, text="No transactions found.",
                text_color="#8a8a8a",
            )
            empty_label.grid(row=0, column=0, sticky="w", pady=8)
            return

        colors = {
            "Income": "#4ade80",
            "Expense": "#f87171",
            "Savings": "#60a5fa",
            "Debt": "#fbbf24",
        }

        for i, txn in enumerate(rows):
            row_frame = ctk.CTkFrame(self.transactions_list, fg_color="#232323", corner_radius=10)
            row_frame.grid(row=i, column=0, sticky="ew", pady=4)
            row_frame.grid_columnconfigure(1, weight=1)

            txn_type = str(txn.get("type", ""))
            accent = colors.get(txn_type, "#d1d1d1")

            amount = txn.get("amount", 0) or 0
            try:
                amount_text = f"₹{float(amount):,.2f}"
            except (TypeError, ValueError):
                amount_text = "₹0.00"

            left_text = f"{txn.get('merchant', 'Unspecified')} — {txn.get('category', '')}"
            date_text = str(txn.get("date", ""))

            ctk.CTkLabel(
                row_frame, text=left_text, anchor="w",
                font=ctk.CTkFont(size=13, weight="bold"),
            ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))

            ctk.CTkLabel(
                row_frame, text=date_text, anchor="w",
                text_color="#9a9a9a", font=ctk.CTkFont(size=11),
            ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

            ctk.CTkLabel(
                row_frame, text=txn_type, text_color=accent,
                font=ctk.CTkFont(size=11, weight="bold"),
            ).grid(row=0, column=1, sticky="e", padx=(0, 12), pady=(8, 0))

            ctk.CTkLabel(
                row_frame, text=amount_text, text_color=accent,
                font=ctk.CTkFont(size=13, weight="bold"),
            ).grid(row=1, column=1, sticky="e", padx=(0, 12), pady=(0, 8))

    # ---- right column: expense breakdown + AI insights ---- #

    def _build_right_column(self, parent: Any) -> None:
        right = ctk.CTkFrame(parent, fg_color="transparent")
        right.grid(row=1, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)

        self._build_expense_breakdown(right)
        self._build_insights(right)

    def _build_expense_breakdown(self, parent: Any) -> None:
        frame = ctk.CTkFrame(parent, corner_radius=14, fg_color="#1a1a1a")
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        frame.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkLabel(
            frame, text="Expense Breakdown (Budget vs Actual)",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        heading.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self.breakdown_container = ctk.CTkFrame(frame, fg_color="transparent")
        self.breakdown_container.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.breakdown_container.grid_columnconfigure(0, weight=1)

    def _render_expense_breakdown(self, breakdown: dict[str, dict[str, float]]) -> None:
        for widget in self.breakdown_container.winfo_children():
            widget.destroy()

        if not breakdown:
            ctk.CTkLabel(
                self.breakdown_container, text="No expense data available.",
                text_color="#8a8a8a",
            ).grid(row=0, column=0, sticky="w")
            return

        for i, (category, values) in enumerate(breakdown.items()):
            budget = values.get("budget", 0) or 0
            actual = values.get("actual", 0) or 0

            row_frame = ctk.CTkFrame(self.breakdown_container, fg_color="transparent")
            row_frame.grid(row=i, column=0, sticky="ew", pady=4)
            row_frame.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                row_frame, text=category, anchor="w",
                font=ctk.CTkFont(size=12, weight="bold"),
            ).grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(
                row_frame,
                text=f"Budget ₹{budget:,.0f}   Actual ₹{actual:,.0f}",
                anchor="e", text_color="#9a9a9a", font=ctk.CTkFont(size=11),
            ).grid(row=0, column=1, sticky="e")

            try:
                progress = min(float(actual) / float(budget), 1.5) if budget else 0.0
            except (TypeError, ValueError, ZeroDivisionError):
                progress = 0.0

            bar_color = "#f87171" if progress > 1 else "#4ade80"
            bar = ctk.CTkProgressBar(row_frame, progress_color=bar_color)
            bar.set(min(progress, 1.0))
            bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))

    def _build_insights(self, parent: Any) -> None:
        frame = ctk.CTkFrame(parent, corner_radius=14, fg_color="#1a1a1a")
        frame.grid(row=1, column=0, sticky="nsew")
        frame.grid_columnconfigure(0, weight=1)

        heading = ctk.CTkLabel(
            frame, text="AI Insights",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        heading.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self.insights_container = ctk.CTkScrollableFrame(frame, fg_color="transparent", height=220)
        self.insights_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
        self.insights_container.grid_columnconfigure(0, weight=1)

    def _render_insights(self, insights: list[str]) -> None:
        for widget in self.insights_container.winfo_children():
            widget.destroy()

        if not insights:
            ctk.CTkLabel(
                self.insights_container, text="No insights available.",
                text_color="#8a8a8a",
            ).grid(row=0, column=0, sticky="w")
            return

        for i, text in enumerate(insights):
            ctk.CTkLabel(
                self.insights_container, text=text, anchor="w",
                justify="left", wraplength=340,
            ).grid(row=i, column=0, sticky="w", pady=4)

    # ------------------------------------------------------------ #
    # REFRESH SYSTEM
    # ------------------------------------------------------------ #

    def refresh_all(self) -> None:
        month_sheet = self._selected_month()

        try:
            data = dashboard.get_dashboard_data(month_sheet)
        except FileNotFoundError as exc:
            messagebox.showerror("Excel File Missing", str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error Loading Dashboard", str(exc))
            return

        self.card_income.set_value(data.get("income", 0))
        self.card_expense.set_value(data.get("expense", 0))
        self.card_savings.set_value(data.get("savings", 0))
        self.card_debt.set_value(data.get("debt", 0))
        self.card_balance.set_value(data.get("balance", 0))

        try:
            breakdown = dashboard.get_expense_breakdown(month_sheet)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error Loading Breakdown", str(exc))
            breakdown = {}
        self._render_expense_breakdown(breakdown)

        try:
            insights = dashboard.generate_ai_insights(month_sheet)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error Loading Insights", str(exc))
            insights = []
        self._render_insights(insights)

        self._load_recent_transactions()


# ---------------------------------------------------------------- #
# ENTRY POINT (imported by main.py)
# ---------------------------------------------------------------- #

app = FinPilotApp()
app.mainloop()