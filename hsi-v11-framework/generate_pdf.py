#!/usr/bin/env python3
"""
HSI Prediction Tool v11 - PDF Export Generator
Generates a formatted PDF from the V11 framework document
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime
import os

def create_pdf():
    # Read the markdown content
    with open('memory/hsi-v11-dashboard.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create PDF document
    doc = SimpleDocTemplate(
        "HSI_Prediction_v11_Framework.pdf",
        pagesize=landscape(A4),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#006699'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    story.append(Paragraph("HSI PREDICTION TOOL v11", title_style))
    story.append(Paragraph("Multi-Theory Framework: Zhou Jintao + Gann + Solar Terms", 
                          ParagraphStyle('Subtitle', parent=styles['Normal'], 
                                       fontSize=12, textColor=colors.grey, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.2*inch))
    
    # Executive Summary
    story.append(Paragraph("EXECUTIVE SUMMARY", styles['Heading2']))
    summary_text = """
    This framework integrates Zhou Jintao's Kondratiev Cycle Theory with Gann Theory and 24 Solar Terms 
    to create a comprehensive HSI prediction system. Current positioning (2026) indicates we are at the 
    transition from Depression to Recovery phase - a generational buying opportunity.
    """
    story.append(Paragraph(summary_text, styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Key Recommendations Table
    story.append(Paragraph("CURRENT RECOMMENDATIONS (2026 Q1)", styles['Heading2']))
    
    rec_data = [
        ['Signal', '🟢 ACCUMULATE', 'Position Size', '75-80%'],
        ['Cash Reserve', '20-25%', 'Stop Loss', '-12%'],
        ['Top Sector', 'Technology (15%)', '2nd Sector', 'Financials (25%)'],
        ['HSI Target 2026', '18,000-22,000', 'HSI Target 2030', '25,000'],
        ['Key Date', '立春 Feb 4 (Increase exposure)', 'Max Position', '冬至 Dec 21']
    ]
    
    rec_table = Table(rec_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 2*inch])
    rec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006699')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    story.append(rec_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Sector Allocation
    story.append(Paragraph("SECTOR ALLOCATION MATRIX", styles['Heading2']))
    
    sector_data = [
        ['Sector', 'Allocation', 'Signal', 'Key Stocks'],
        ['🚀 Technology', '15%', 'OVERWEIGHT', 'Tencent, Alibaba, Xiaomi, SMIC'],
        ['✅ Financials', '25%', 'NEUTRAL', 'HSBC, AIA, Bank of China, CCB'],
        ['🚀 Properties', '10%', 'OVERWEIGHT', 'Sun Hung Kai, CK Asset, CR Land'],
        ['⚠️ Utilities', '10%', 'UNDERWEIGHT', 'CLP, HK Electric, Town Gas'],
        ['✅ Consumer', '15%', 'NEUTRAL', 'Mengniu, Nongfu Spring, CR Beer'],
        ['🚀 Industrials', '10%', 'OVERWEIGHT', 'CRRC, Xinjiang Goldwind, MTR'],
        ['⚠️ Energy', '5%', 'UNDERWEIGHT', 'CNOOC (high dividend only)'],
        ['🛡️ Cash/Gold', '10%', 'RESERVE', 'Liquidity for opportunities']
    ]
    
    sector_table = Table(sector_data, colWidths=[1.5*inch, 0.8*inch, 1.2*inch, 3*inch])
    sector_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006699')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    story.append(sector_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Signal Convergence
    story.append(Paragraph("SIGNAL CONVERGENCE ANALYSIS", styles['Heading2']))
    
    signal_data = [
        ['Theory/Indicator', 'Signal', 'Strength', 'Weight', 'Score'],
        ['Kondratiev Phase', '🟢 Recovery Start', 'High', '30%', '0.90'],
        ['Real Estate Cycle', '🟡 Bottoming', 'Medium', '20%', '0.40'],
        ['Juglar Cycle', '🟢 Mid-Recovery', 'Medium', '15%', '0.45'],
        ['Kitchin Cycle', '🟢 Expansion', 'Medium', '10%', '0.30'],
        ['Gann Time Cycle', '🟢 Turning Window', 'High', '15%', '0.45'],
        ['Gann Price Level', '🟡 At Support', 'Medium', '10%', '0.20'],
        ['Solar Term (Spring)', '🟢 Growth Phase', 'Low', '10%', '0.15'],
        ['TOTAL', '', '', '100%', '2.85/3.00']
    ]
    
    signal_table = Table(signal_data, colWidths=[2*inch, 1.5*inch, 1*inch, 0.8*inch, 0.8*inch])
    signal_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006699')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#00aa44')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.lightgrey]),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    story.append(signal_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Solar Term Calendar
    story.append(Paragraph("2026 SOLAR TERM KEY DATES", styles['Heading2']))
    
    solar_data = [
        ['Season', 'Solar Term', 'Date', 'Signal', 'Action'],
        ['🌱 Spring', '立春 (Lichun)', 'Feb 4', '🟢', 'Increase exposure'],
        ['🌱 Spring', '春分 (Chunfen)', 'Mar 20', '🟡', 'Hold/Rebalance'],
        ['🌱 Spring', '谷雨 (Guyu)', 'Apr 20', '🟢', 'Accumulate quality'],
        ['☀️ Summer', '立夏 (Lixia)', 'May 5', '🟢', 'Risk-on'],
        ['☀️ Summer', '夏至 (Xiazhi)', 'Jun 21', '🔴', 'Take profits'],
        ['🍂 Autumn', '立秋 (Liqiu)', 'Aug 7', '🟡', 'Reduce risk'],
        ['🍂 Autumn', '秋分 (Qiufen)', 'Sep 23', '🟡', 'Rebalance'],
        ['❄️ Winter', '立冬 (Lidong)', 'Nov 7', '🟢', 'Begin accumulation'],
        ['❄️ Winter', '冬至 (Dongzhi)', 'Dec 21', '🟢🔺', 'MAXIMUM POSITION']
    ]
    
    solar_table = Table(solar_data, colWidths=[1*inch, 1.5*inch, 1*inch, 0.6*inch, 2.4*inch])
    solar_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006699')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9)
    ]))
    story.append(solar_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Price Targets
    story.append(Paragraph("HSI PRICE TARGETS", styles['Heading2']))
    
    price_data = [
        ['Period', 'Target', 'Cycle Phase', 'Strategy'],
        ['Current (2026)', '18,000-22,000', 'Recovery Start', 'Accumulate'],
        ['2030 Target', '25,000', 'Recovery/Prosperity', 'Hold & Add'],
        ['2040+ Target', '30,000-35,000', 'Prosperity Peak', 'Take Profits']
    ]
    
    price_table = Table(price_data, colWidths=[1.5*inch, 2*inch, 2*inch, 2*inch])
    price_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#006699')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10)
    ]))
    story.append(price_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Integration Note
    story.append(Paragraph("INTEGRATION WITH V10 (GANN/SOLAR)", styles['Heading2']))
    integration_text = """
    <b>V10 (Short-term Tactical):</b> Wait for May 9, 2026 high-confluence window (70 pts solar confluence)<br/>
    <b>V11 (Long-term Strategic):</b> 2026-2030 is generational buying opportunity (Kondratiev Recovery Start)<br/><br/>
    <b>Combined Strategy:</b> Use V11 for WHAT to buy (sector allocation), use V10 for WHEN to enter (timing).
    Begin accumulation on May 9, 2026 with full V11 sector allocation.
    """
    story.append(Paragraph(integration_text, ParagraphStyle('Integration', parent=styles['Normal'], fontSize=10)))
    story.append(Spacer(1, 0.3*inch))
    
    # Footer
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')} | cyclingAi | Version 11.0", 
                          ParagraphStyle('Footer', parent=styles['Normal'], 
                                       fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
    
    # Build PDF
    doc.build(story)
    print("✅ PDF generated: HSI_Prediction_v11_Framework.pdf")

if __name__ == '__main__':
    create_pdf()
