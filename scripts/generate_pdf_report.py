#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成回测报告 PDF
使用 reportlab 生成 PDF 格式报告
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER
from pathlib import Path
import pandas as pd
from datetime import datetime

# 创建 PDF 文档
output_file = Path('reports/回测分析报告_20260330.pdf')
doc = SimpleDocTemplate(str(output_file), pagesize=A4)

styles = getSampleStyleSheet()
title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, textColor=colors.darkblue, spaceAfter=12, alignment=TA_CENTER)
heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, textColor=colors.darkred, spaceAfter=10, spaceBefore=12)
normal_style = ParagraphStyle('CustomNormal', parent=styles['Normal'], fontSize=10, spaceAfter=6, leading=12)

content = []

# 标题
content.append(Paragraph('A 股回测分析报告', title_style))
content.append(Paragraph(f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}', normal_style))
content.append(Spacer(1, 0.3*inch))

# 回测概览
content.append(Paragraph('一、回测概览', heading_style))

# 读取回测数据
file_8y = Path('reports/backtest_iths_8y_buyhold_20260330_1728.csv')
if file_8y.exists():
    df = pd.read_csv(file_8y)
    
    # 统计信息
    total_stocks = len(df)
    avg_return = df['total_return'].mean()
    best_stock = df.loc[df['total_return'].idxmax()]
    
    data = [
        ['回测周期', '8 年 (2018-2026)'],
        ['有效股票', f'{total_stocks}只'],
        ['平均收益', f'{avg_return:+.1f}%'],
        ['最佳股票', f'{best_stock["name"]} ({best_stock["total_return"]:+.1f}%)'],
    ]
    
    table = Table(data, colWidths=[2*inch, 3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(table)

content.append(Spacer(1, 0.3*inch))

# 明星股票
content.append(Paragraph('二、明星股票 Top 10', heading_style))

# 按收益排序
df_sorted = df.sort_values('total_return', ascending=False)
top10 = df_sorted.head(10)

top10_data = [['排名', '代码', '名称', '8 年收益', '年化收益']]
for idx, (_, row) in enumerate(top10.iterrows(), 1):
    annual = ((1 + row['total_return']/100) ** (1/8) - 1) * 100
    top10_data.append([
        str(idx),
        row['ts_code'],
        row['name'],
        f"{row['total_return']:+.1f}%",
        f"{annual:+.1f}%"
    ])

top10_table = Table(top10_data, colWidths=[0.6*inch, 1.2*inch, 1.5*inch, 1.2*inch, 1*inch])
top10_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 9),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
]))
content.append(top10_table)

content.append(Spacer(1, 0.3*inch))

# 投资建议
content.append(Paragraph('三、投资建议', heading_style))
content.append(Paragraph('1. 行业选择：黄金/化工/医药/机械', normal_style))
content.append(Paragraph('2. 选股标准：行业龙头 + ROE>10% + 低负债', normal_style))
content.append(Paragraph('3. 仓位管理：单只≤15%, 单行业≤30%', normal_style))
content.append(Paragraph('4. 风险提示：注意周期波动和政策风险', normal_style))

# 生成 PDF
doc.build(content)
print(f'✅ PDF 报告已生成：{output_file}')
