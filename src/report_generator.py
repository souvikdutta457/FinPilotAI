"""
report_generator.py
-------------------
Generates a professional monthly financial PDF report containing:
- Income vs Expense summary
- Category-wise spending
- Savings Rate
- Top Merchants
- Automated AI-style recommendations
"""

import os
import pandas as pd
from datetime import datetime
import excel_engine

# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def fetch_data_as_dataframe() -> pd.DataFrame:
    """Reads live transactions from the Excel engine and loads them into a Pandas DataFrame."""
    # Temporarily bypass file location checks if folder configuration varies
    raw_data = excel_engine.read_transactions()
    
    # Define actual columns based on Excel structure:
    # (Date, Type, Category, Merchant, Amount, Note, Confidence, Month, Year)
    columns = ['Date', 'Type', 'Category', 'Merchant', 'Amount', 'Description', 'Confidence', 'Month', 'Year']
    df = pd.DataFrame(raw_data, columns=columns)
    
    # Clean numeric fields
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0.0)
    return df

def generate_monthly_report(target_month: str, output_filename: str = None) -> str:
    """Processes financial metrics for a target month and saves a beautifully formatted PDF report."""
    df = fetch_data_as_dataframe()
    
    # Filter for the target month (case-insensitive)
    df_month = df[df['Month'].str.lower() == target_month.lower()]
    
    if df_month.empty:
        print(f"❌ No transaction data found for '{target_month}'. Check your Excel records.")
        return ""
    
    # --- 1. FINANCIAL METRICS CALCULATION ---
    # Totals by type
    income = df_month[df_month['Type'] == 'Income']['Amount'].sum()
    expense = df_month[df_month['Type'] == 'Expense']['Amount'].sum()
    savings_allocation = df_month[df_month['Type'] == 'Savings']['Amount'].sum()
    debt_payments = df_month[df_month['Type'] == 'Debt']['Amount'].sum()
    
    net_savings = income - expense - debt_payments
    savings_rate = (net_savings / income * 100) if income > 0 else 0.0
    
    # Category spending breakdown (for Expenses)
    category_spend = (df_month[df_month['Type'] == 'Expense']
                      .groupby('Category')['Amount']
                      .sum()
                      .reset_index()
                      .sort_values(by='Amount', ascending=False))
    
    # Top Merchants (excluding Unspecified/Unknown)
    top_merchants = (df_month[(df_month['Type'] == 'Expense') & (~df_month['Merchant'].str.lower().isin(['unspecified', 'unknown', 'none']))]
                     .groupby('Merchant')['Amount']
                     .sum()
                     .reset_index()
                     .sort_values(by='Amount', ascending=False)
                     .head(3))

    # --- 2. AUTOMATED AI RECOMMENDATIONS ---
    recommendations = []
    if savings_rate < 20:
        recommendations.append("⚠️ Your savings rate is below the 20% rule of thumb. Consider auditing non-essential dining/subscriptions.")
    else:
        recommendations.append("🏆 Excellent budget control! Your savings rate exceeds the benchmark goal.")
        
    if not category_spend.empty:
        highest_cat = category_spend.iloc[0]['Category']
        highest_amt = category_spend.iloc[0]['Amount']
        recommendations.append(f"🔍 Alert: '{highest_cat}' is your largest expense category this month (₹{highest_amt:,.2f}).")
    
    if debt_payments > (income * 0.4) and income > 0:
        recommendations.append("⚠️ Debt management advice: Debt servicing payments represent >40% of net incoming cashflow.")
    else:
        recommendations.append("✅ Debt levels are well-balanced and safe compared to income.")

    # --- 3. PDF DOCUMENT COMPILATION ---
    if not output_filename:
        os.makedirs("reports", exist_ok=True)
        output_filename = f"reports/Financial_Report_{target_month.capitalize()}.pdf"
        
    doc = SimpleDocTemplate(output_filename, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=15
    )
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#111827'),
        spaceBefore=15,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4b5563')
    )
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )
    
    # Title & Header
    story.append(Paragraph(f"Monthly Financial Summary: {target_month.capitalize()}", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')} | FinPilot AI v1.0", body_style))
    story.append(Spacer(1, 15))
    
    # Key Metrics Table
    story.append(Paragraph("I. Income vs Expense Summary", section_style))
    summary_data = [
        [Paragraph('<b>Financial Metric</b>', body_style), Paragraph('<b>Value (₹)</b>', body_style)],
        [Paragraph('Total Income', body_style), f"₹{income:,.2f}"],
        [Paragraph('Total Expenses', body_style), f"₹{expense:,.2f}"],
        [Paragraph('Savings Allocated', body_style), f"₹{savings_allocation:,.2f}"],
        [Paragraph('Debt Payments', body_style), f"₹{debt_payments:,.2f}"],
        [Paragraph('Savings Rate', body_style), f"{savings_rate:.1f}%"]
    ]
    t_summary = Table(summary_data, colWidths=[250, 150])
    t_summary.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#f3f4f6')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    story.append(t_summary)
    story.append(Spacer(1, 15))
    
    # Category Spending Table
    story.append(Paragraph("II. Category-Wise Spending", section_style))
    cat_data = [[Paragraph('<b>Category</b>', body_style), Paragraph('<b>Total Spent (₹)</b>', body_style)]]
    for _, row in category_spend.iterrows():
        cat_data.append([Paragraph(row['Category'], body_style), f"₹{row['Amount']:,.2f}"])
    
    if len(cat_data) == 1: # Empty
        cat_data.append([Paragraph('No expenses logged', body_style), "₹0.00"])
        
    t_cat = Table(cat_data, colWidths=[250, 150])
    t_cat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#f3f4f6')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    story.append(t_cat)
    story.append(Spacer(1, 15))
    
    # Top Merchants Table
    if not top_merchants.empty:
        story.append(Paragraph("III. Top Spending Outlets", section_style))
        merchant_data = [[Paragraph('<b>Merchant</b>', body_style), Paragraph('<b>Total Spent (₹)</b>', body_style)]]
        for _, row in top_merchants.iterrows():
            merchant_data.append([Paragraph(row['Merchant'], body_style), f"₹{row['Amount']:,.2f}"])
        t_merch = Table(merchant_data, colWidths=[250, 150])
        t_merch.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (1,0), colors.HexColor('#f3f4f6')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ]))
        story.append(t_merch)
        story.append(Spacer(1, 15))

    # Recommendations / AI Insights Section
    story.append(Paragraph("IV. FinPilot AI Financial Advisory", section_style))
    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", bullet_style))
        
    # Build Document
    doc.build(story)
    print(f"✅ Success! Generated PDF financial summary: {output_filename}")
    return output_filename

if __name__ == "__main__":
    # Quick standalone test for 'July' or current month
    generate_monthly_report("July")