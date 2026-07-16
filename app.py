"""
app.py
------
FinPilot AI - Streamlit Web Application

This is the web front-end for FinPilot AI. It replaces the old
CustomTkinter desktop GUI (gui.py) with a modern Streamlit interface,
while reusing the EXACT SAME backend modules and business logic:

    - dashboard.py        (dashboard totals, budget-vs-actual, AI insights)
    - excel_engine.py     (all raw Excel read/write operations)
    - transactions.py     (recent transactions + search)
    - analytics_engine.py (matplotlib charts for analytics)
    - ai_engine.py         (optional local Ollama-powered chat assistant)

No business logic has been changed. This file only builds the UI and
wires user interactions to the functions that already exist in the
backend modules above.

Run locally with:
    streamlit run app.py

Deploy for free on Streamlit Community Cloud by pointing it at this
file as the app's main file.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd
import streamlit as st

from src import dashboard
from src import excel_engine
from src import transactions
from src import analytics_engine

try:
    import ai_engine
    AI_ENGINE_AVAILABLE = True
except ImportError:
    AI_ENGINE_AVAILABLE = False


# ==================================================================
# PAGE CONFIG
# ==================================================================

st.set_page_config(
    page_title="FinPilot AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================================================================
# GLOBAL STYLING
# ==================================================================

def inject_custom_css() -> None:
    st.markdown(
        """
        <style>
        /* ---------- General layout ---------- */
        .main {
            padding-top: 1.2rem;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        /* ---------- Header ---------- */
        .fp-header-title {
            font-size: 2.1rem;
            font-weight: 800;
            margin-bottom: 0;
            background: linear-gradient(90deg, #4ade80, #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .fp-header-subtitle {
            font-size: 0.95rem;
            color: #9a9a9a;
            margin-top: -6px;
        }

        /* ---------- Metric cards ---------- */
        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, #1a1a1a, #202020);
            border: 1px solid #2b2b2b;
            border-radius: 16px;
            padding: 16px 18px 10px 18px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.25);
        }
        div[data-testid="stMetricLabel"] {
            font-weight: 600;
            color: #a0a0a0 !important;
        }
        div[data-testid="stMetricValue"] {
            font-weight: 800 !important;
        }

        /* ---------- Section cards ---------- */
        .fp-card {
            background: #1a1a1a;
            border: 1px solid #262626;
            border-radius: 16px;
            padding: 18px 20px;
            margin-bottom: 18px;
        }
        .fp-card h4 {
            margin-top: 0;
            margin-bottom: 12px;
        }

        /* ---------- Transaction row ---------- */
        .fp-txn-row {
            background: #232323;
            border-radius: 10px;
            padding: 10px 14px;
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .fp-txn-left { display: flex; flex-direction: column; }
        .fp-txn-merchant { font-weight: 700; font-size: 0.95rem; }
        .fp-txn-date { font-size: 0.78rem; color: #9a9a9a; }
        .fp-txn-right { text-align: right; }
        .fp-txn-amount { font-weight: 800; font-size: 0.95rem; }
        .fp-txn-type { font-size: 0.75rem; font-weight: 700; }

        /* ---------- Insight pill ---------- */
        .fp-insight {
            padding: 10px 14px;
            border-radius: 10px;
            background: #232323;
            margin-bottom: 8px;
            font-size: 0.9rem;
        }

        /* ---------- Badges ---------- */
        .fp-badge-green { color: #4ade80; }
        .fp-badge-red { color: #f87171; }
        .fp-badge-blue { color: #60a5fa; }
        .fp-badge-yellow { color: #fbbf24; }
        .fp-badge-purple { color: #c084fc; }
        </style>
        """,
        unsafe_allow_html=True,
    )


TYPE_COLORS = {
    "Income": "#4ade80",
    "Expense": "#f87171",
    "Savings": "#60a5fa",
    "Debt": "#fbbf24",
}

MONTH_NAMES = list(dashboard.MONTH_SHEETS.values())


# ==================================================================
# HELPERS
# ==================================================================

def safe_call(fn, *args, error_title: str = "Error", default: Any = None, **kwargs):
    """Runs a backend function and shows a friendly Streamlit error on
    failure instead of crashing the whole app."""
    try:
        return fn(*args, **kwargs)
    except FileNotFoundError as exc:
        st.error(f"📁 Excel file not found — {exc}")
        return default
    except Exception as exc:  # noqa: BLE001
        st.error(f"⚠ {error_title}: {exc}")
        return default


def format_currency(value: Any) -> str:
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"


# ==================================================================
# SIDEBAR
# ==================================================================

def build_sidebar() -> str:
    with st.sidebar:
        st.markdown("## 💰 FinPilot AI")
        st.caption("Personal Finance Dashboard")
        st.divider()

        default_month = dashboard._current_month_sheet()
        selected_month = st.selectbox(
            "📅 Select Month",
            options=MONTH_NAMES,
            index=MONTH_NAMES.index(default_month),
        )

        if st.button("⟳ Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.divider()
        st.markdown("### Navigate")
        page = st.radio(
            "Go to",
            options=[
                "🏠 Dashboard",
                "💰 Add Transaction",
                "📋 Recent Transactions",
                "📊 Expense Breakdown",
                "🤖 AI Insights",
                "📈 Analytics",
            ],
            label_visibility="collapsed",
        )

        st.divider()
        st.caption("FinPilot AI • Excel-powered • Local & private")

    return selected_month, page


# ==================================================================
# PAGE: DASHBOARD
# ==================================================================

def render_dashboard_cards(month_sheet: str) -> None:
    data = safe_call(
        dashboard.get_dashboard_data, month_sheet,
        error_title="Error Loading Dashboard", default={},
    )

    income = data.get("income", 0)
    expense = data.get("expense", 0)
    savings = data.get("savings", 0)
    debt = data.get("debt", 0)
    balance = data.get("balance", 0)

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Income", format_currency(income))
    c2.metric("Expense", format_currency(expense))
    c3.metric("Savings", format_currency(savings))
    c4.metric("Debt", format_currency(debt))
    c5.metric("Balance", format_currency(balance),
              delta=None if balance == 0 else ("Positive" if balance >= 0 else "Negative"))


def page_dashboard(month_sheet: str) -> None:
    st.markdown(f'<div class="fp-header-title">FinPilot AI</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="fp-header-subtitle">Personal Finance Dashboard — {month_sheet}</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    render_dashboard_cards(month_sheet)
    st.write("")

    left, right = st.columns([3, 2])

    with left:
        st.markdown('<div class="fp-card">', unsafe_allow_html=True)
        st.markdown("#### 📋 Recent Transactions")
        render_recent_transactions_list(limit=8)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="fp-card">', unsafe_allow_html=True)
        st.markdown("#### 📊 Expense Breakdown")
        render_expense_breakdown(month_sheet, compact=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ==================================================================
# PAGE: ADD TRANSACTION
# ==================================================================

def page_add_transaction() -> None:
    st.markdown("### 💰 Add Transaction")
    st.caption("Add a new income, expense, savings, or debt entry to your Excel workbook.")

    with st.form("add_transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            txn_type = st.selectbox("Type", sorted(excel_engine.VALID_TYPES), index=1)
            category = st.text_input("Category", placeholder="e.g. Food Order")
            date_input = st.text_input(
                "Date (DD-MM-YYYY, blank = today)", placeholder=""
            )

        with col2:
            amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0, format="%.2f")
            merchant = st.text_input("Merchant", placeholder="e.g. Domino's")
            description = st.text_area("Description", placeholder="Optional note", height=68)

        submitted = st.form_submit_button("➕ Add Transaction", use_container_width=True, type="primary")

        if submitted:
            if amount <= 0:
                st.warning("Please enter an amount greater than 0.")
            else:
                transaction = {
                    "type": txn_type,
                    "category": category or "Other Expenses",
                    "amount": amount,
                    "merchant": merchant or "Unspecified",
                    "date": date_input,
                    "month": "",
                    "year": 0,
                    "description": description,
                }
                row = safe_call(
                    excel_engine.write_transaction, transaction,
                    error_title="Error Saving Transaction",
                )
                if row is not None:
                    st.success(f"✅ Transaction added to row {row}.")
                    st.cache_data.clear()

    st.divider()
    st.markdown("#### 📋 Latest Entries")
    render_recent_transactions_list(limit=5)


# ==================================================================
# PAGE: RECENT TRANSACTIONS
# ==================================================================

def render_recent_transactions_list(limit: int = 15) -> None:
    recent = safe_call(
        transactions.get_recent_transactions, limit,
        error_title="Error Loading Transactions", default=[],
    )

    if not recent:
        st.info("No transactions found yet.")
        return

    for txn in recent:
        txn_type = str(txn.get("type", ""))
        accent = TYPE_COLORS.get(txn_type, "#d1d1d1")
        amount_text = format_currency(txn.get("amount", 0))
        merchant = txn.get("merchant", "Unspecified")
        category = txn.get("category", "")
        date_text = str(txn.get("date", ""))

        st.markdown(
            f"""
            <div class="fp-txn-row">
                <div class="fp-txn-left">
                    <span class="fp-txn-merchant">{merchant} — {category}</span>
                    <span class="fp-txn-date">{date_text}</span>
                </div>
                <div class="fp-txn-right">
                    <div class="fp-txn-type" style="color:{accent};">{txn_type}</div>
                    <div class="fp-txn-amount" style="color:{accent};">{amount_text}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def page_recent_transactions() -> None:
    st.markdown("### 📋 Recent Transactions")

    tab1, tab2 = st.tabs(["🕒 Recent", "🔍 Search"])

    with tab1:
        limit = st.slider("Number of transactions to show", 5, 50, 15)
        render_recent_transactions_list(limit=limit)

    with tab2:
        keyword = st.text_input("Search by merchant, category, description, etc.")
        if keyword:
            results = safe_call(
                excel_engine.search_transactions, keyword,
                error_title="Error Searching Transactions", default=[],
            )
            if not results:
                st.info("No matching transactions found.")
            else:
                df = pd.DataFrame(
                    results,
                    columns=["Date", "Type", "Category", "Merchant", "Amount",
                             "Description", "Confidence", "Month", "Year"][: len(results[0])]
                    if results else None,
                )
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.caption("Type a keyword above to search all transactions.")


# ==================================================================
# PAGE: EXPENSE BREAKDOWN
# ==================================================================

def render_expense_breakdown(month_sheet: str, compact: bool = False) -> None:
    breakdown = safe_call(
        dashboard.get_expense_breakdown, month_sheet,
        error_title="Error Loading Breakdown", default={},
    )

    if not breakdown:
        st.info("No expense data available for this month.")
        return

    for category, values in breakdown.items():
        budget = values.get("budget", 0) or 0
        actual = values.get("actual", 0) or 0

        try:
            progress = float(actual) / float(budget) if budget else 0.0
        except (TypeError, ValueError, ZeroDivisionError):
            progress = 0.0

        over_budget = progress > 1

        c1, c2 = st.columns([3, 2])
        c1.markdown(f"**{category}**")
        c2.markdown(
            f"<div style='text-align:right; color:#9a9a9a; font-size:0.85rem;'>"
            f"Budget {format_currency(budget)} &nbsp;•&nbsp; Actual {format_currency(actual)}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.progress(min(progress, 1.0))
        if over_budget and not compact:
            st.caption(f"⚠ Over budget by {format_currency(actual - budget)}")


def page_expense_breakdown(month_sheet: str) -> None:
    st.markdown(f"### 📊 Expense Breakdown — {month_sheet}")
    st.caption("Budget vs Actual, read live from your Excel workbook.")
    st.markdown('<div class="fp-card">', unsafe_allow_html=True)
    render_expense_breakdown(month_sheet)
    st.markdown("</div>", unsafe_allow_html=True)


# ==================================================================
# PAGE: AI INSIGHTS
# ==================================================================

def page_ai_insights(month_sheet: str) -> None:
    st.markdown(f"### 🤖 AI Insights — {month_sheet}")
    st.caption("Automatic budget-vs-actual insights generated from your data.")

    insights = safe_call(
        dashboard.generate_ai_insights, month_sheet,
        error_title="Error Generating Insights", default=[],
    )

    if not insights:
        st.info("No insights available for this month.")
    else:
        for text in insights:
            if text.startswith("⚠"):
                css_class = "fp-badge-red"
            elif text.startswith("✅"):
                css_class = "fp-badge-green"
            else:
                css_class = "fp-badge-blue"
            st.markdown(
                f'<div class="fp-insight"><span class="{css_class}">{text}</span></div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown("#### 💬 Ask FinPilot AI")
    st.caption(
        "Conversational assistant powered by a local Ollama model. "
        "Requires Ollama running locally — unavailable on Streamlit Community Cloud."
    )

    if not AI_ENGINE_AVAILABLE:
        st.warning("ai_engine.py could not be imported — chat assistant is disabled.")
        return

    question = st.text_input("Ask a question about your finances", placeholder="e.g. How much did I spend on food this month?")
    if st.button("Ask", type="primary"):
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner("Thinking..."):
                answer = safe_call(
                    ai_engine.ask_financial_assistant, question,
                    error_title="Error Contacting AI Assistant",
                    default="Unable to reach the AI assistant right now.",
                )
            st.markdown(f'<div class="fp-insight">{answer}</div>', unsafe_allow_html=True)


# ==================================================================
# PAGE: ANALYTICS
# ==================================================================

def page_analytics() -> None:
    st.markdown("### 📈 Analytics")
    st.caption("Charts generated live from all transactions in your workbook.")

    tab1, tab2, tab3 = st.tabs(
        ["🥧 Expense Pie Chart", "📊 Monthly Expenses", "📉 Income vs Expense"]
    )

    with tab1:
        fig = safe_call(
            analytics_engine.create_expense_pie_chart,
            error_title="Error Creating Pie Chart",
        )
        if fig is not None:
            st.pyplot(fig, use_container_width=True)
        else:
            st.info("No expense data available yet.")

    with tab2:
        fig = safe_call(
            analytics_engine.create_monthly_expense_chart,
            error_title="Error Creating Monthly Chart",
        )
        if fig is not None:
            st.pyplot(fig, use_container_width=True)
        else:
            st.info("No expense data available yet.")

    with tab3:
        fig = safe_call(
            analytics_engine.create_income_expense_chart,
            error_title="Error Creating Income vs Expense Chart",
        )
        if fig is not None:
            st.pyplot(fig, use_container_width=True)
        else:
            st.info("No transaction data available yet.")


# ==================================================================
# MAIN
# ==================================================================

def main() -> None:
    inject_custom_css()
    selected_month, page = build_sidebar()

    if page == "🏠 Dashboard":
        page_dashboard(selected_month)
    elif page == "💰 Add Transaction":
        page_add_transaction()
    elif page == "📋 Recent Transactions":
        page_recent_transactions()
    elif page == "📊 Expense Breakdown":
        page_expense_breakdown(selected_month)
    elif page == "🤖 AI Insights":
        page_ai_insights(selected_month)
    elif page == "📈 Analytics":
        page_analytics()


if __name__ == "__main__":
    main()