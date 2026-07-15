import os
import shutil
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import excel_engine
import dashboard

def export_to_csv(output_dir="exports"):
    """Saves all your Excel transactions into a portable CSV spreadsheet."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "transactions_export.csv")
    
    all_txns = excel_engine.read_transactions()
    df = pd.DataFrame(all_txns, columns=['Date','Type','Category','Merchant','Amount','Description','Confidence','Month','Year'])
    df.to_csv(output_path, index=False)
    return output_path

def create_excel_backup(output_dir="backups"):
    """Creates a secure timestamped copy of your database file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(output_dir, f"Budget_Tracker_Backup_{timestamp}.xlsx")
    
    shutil.copy(excel_engine.EXCEL_FILE, backup_path)
    return backup_path

def generate_pdf_report(month_name: str, output_dir="exports"):
    """Compiles professional monthly metrics into a ready-to-print PDF file."""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"Financial_Report_{month_name}.pdf")
    
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    story.append(Paragraph(f"FinPilot AI Executive Summary: {month_name}", styles['Title']))
    story.append(Spacer(1, 20))
    
    data = dashboard.get_dashboard_data(month_name)
    table_data = [
        ['Financial Metric', 'Amount'],
        ['Total Income', f"INR {data['income']:,}"],
        ['Total Expenses', f"INR {data['expense']:,}"],
        ['Savings Growth', f"INR {data['savings']:,}"],
        ['Debt Payments', f"INR {data['debt']:,}"],
        ['Net Balance Available', f"INR {data['balance']:,}"]
    ]
    
    t = Table(table_data, colWidths=[220, 160])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), colors.HexColor('#1a1a1a')),
        ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f5f5f5')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    
    story.append(t)
    doc.build(story)
    return output_path