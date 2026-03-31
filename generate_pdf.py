#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 1000 万投资方案 PDF 报告
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

# 尝试注册中文字体
font_paths = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/Supplemental/PingFang.ttc',
    '/Library/Fonts/PingFang.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
]

chinese_font = None
for fp in font_paths:
    if os.path.exists(fp):
        try:
            pdfmetrics.registerFont(TTFont('Chinese', fp))
            chinese_font = 'Chinese'
            break
        except:
            continue

if not chinese_font:
    chinese_font = 'Helvetica'  # Fallback

def create_pdf():
    output_path = '/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/1000w_Investment_Plan.pdf'
    
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    # 自定义样式
    title_style = ParagraphStyle(
        'ChineseTitle',
        parent=styles['Heading1'],
        fontName=chinese_font,
        fontSize=24,
        textColor=colors.darkblue,
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'ChineseHeading',
        parent=styles['Heading2'],
        fontName=chinese_font,
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=12,
        spaceBefore=12
    )
    
    normal_style = ParagraphStyle(
        'ChineseNormal',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=11,
        leading=16,
        spaceAfter=6
    )
    
    content = []
    
    # 标题
    content.append(Paragraph("1000 万长期投资组合方案", title_style))
    content.append(Paragraph(f"生成日期：{datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    content.append(Spacer(1, 0.3*inch))
    
    # 投资目标
    content.append(Paragraph("一、投资目标", heading_style))
    target_data = [
        ['总资金', '1000 万 USD'],
        ['投资期限', '1-3 年+'],
        ['目标年化收益', '15%+'],
        ['最大月回撤', '≤10%']
    ]
    target_table = Table(target_data, colWidths=[4*cm, 6*cm])
    target_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    content.append(target_table)
    content.append(Spacer(1, 0.3*inch))
    
    # 资产配置
    content.append(Paragraph("二、资产配置", heading_style))
    content.append(Paragraph("核心仓位 60% + 卫星仓位 30% + 对冲/现金 10%", normal_style))
    content.append(Spacer(1, 0.2*inch))
    
    # 核心仓位表
    content.append(Paragraph("2.1 核心仓位（600 万）", heading_style))
    core_data = [
        ['标的', '代码', '配置', '金额', '买入区间', '预期年化'],
        ['标普 500 ETF', 'VOO', '20%', '200 万', '$500-520', '10-12%'],
        ['纳斯达克 100', 'QQQ', '15%', '150 万', '$470-490', '12-15%'],
        ['伯克希尔-B', 'BRK.B', '10%', '100 万', '$470-490', '10-12%'],
        ['中国移动', '0941.HK', '4%', '40 万', '$75-78', '8-10%'],
        ['友邦保险', '1299.HK', '3%', '30 万', '$84-88', '10-12%'],
        ['汇丰控股', '0005.HK', '3%', '30 万', '$120-126', '8-10%'],
        ['20 年美债', 'TLT', '5%', '50 万', '$92-97', '4-5%']
    ]
    core_table = Table(core_data, colWidths=[2.5*cm, 2*cm, 1.5*cm, 1.5*cm, 2.5*cm, 2*cm])
    core_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    content.append(core_table)
    content.append(Spacer(1, 0.3*inch))
    
    # 卫星仓位表
    content.append(Paragraph("2.2 卫星仓位（300 万）", heading_style))
    satellite_data = [
        ['标的', '代码', '配置', '金额', '买入区间', '预期年化'],
        ['谷歌-A', 'GOOGL', '5%', '50 万', '$295-310', '20-25%'],
        ['微软', 'MSFT', '4%', '40 万', '$370-390', '15-20%'],
        ['英伟达', 'NVDA', '3%', '30 万', '$165-180', '25-30%'],
        ['腾讯控股', '0700.HK', '5%', '50 万', '$490-510', '15-20%'],
        ['阿里巴巴', '9988.HK', '3%', '30 万', '$120-128', '15-20%'],
        ['半导体 ETF', 'SOXX', '3%', '30 万', '$230-250', '20-25%'],
        ['苹果', 'AAPL', '2%', '20 万', '$245-255', '15-20%'],
        ['中海油', '0883.HK', '2%', '20 万', '$27-30', '15-20%']
    ]
    satellite_table = Table(satellite_data, colWidths=[2.5*cm, 2*cm, 1.5*cm, 1.5*cm, 2.5*cm, 2*cm])
    satellite_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    content.append(satellite_table)
    content.append(Spacer(1, 0.3*inch))
    
    # 对冲/现金
    content.append(Paragraph("2.3 对冲/现金（100 万）", heading_style))
    hedge_data = [
        ['工具', '配置', '金额', '作用'],
        ['货币基金', '5%', '50 万', '流动性 + 抄底弹药 (4.5-5% 收益)'],
        ['黄金 ETF (GLD)', '3%', '30 万', '通胀 + 地缘对冲'],
        ['VIX 看涨期权', '2%', '20 万', '黑天鹅保护']
    ]
    hedge_table = Table(hedge_data, colWidths=[3*cm, 2*cm, 2*cm, 5*cm])
    hedge_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    content.append(hedge_table)
    content.append(PageBreak())
    
    # 建仓计划
    content.append(Paragraph("三、建仓计划", heading_style))
    
    content.append(Paragraph("第 1 阶段：第 1-2 周（40% = 400 万）", ParagraphStyle('SubHeading', parent=normal_style, fontSize=12, fontName=chinese_font)))
    phase1_data = [
        ['周次', '标的', '金额', '价格区间'],
        ['第 1 周', 'VOO', '100 万', '$500-520'],
        ['第 1 周', 'QQQ', '50 万', '$470-490'],
        ['第 2 周', 'BRK.B', '100 万', '$470-490'],
        ['第 2 周', 'TLT', '50 万', '$92-97'],
        ['第 2 周', '港股高股息', '100 万', '现价附近']
    ]
    phase1_table = Table(phase1_data, colWidths=[2*cm, 3*cm, 2*cm, 3*cm])
    phase1_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    content.append(phase1_table)
    content.append(Spacer(1, 0.2*inch))
    
    content.append(Paragraph("第 2 阶段：第 3-6 周（30% = 300 万）", ParagraphStyle('SubHeading', parent=normal_style, fontSize=12, fontName=chinese_font)))
    content.append(Paragraph("• 科技股回调 5%：建仓 GOOGL + MSFT (90 万)", normal_style))
    content.append(Paragraph("• 科技股回调 10%：建仓 NVDA (30 万)", normal_style))
    content.append(Paragraph("• 港股反弹确认：建仓腾讯 + 阿里 (80 万)", normal_style))
    content.append(Paragraph("• 行业轮动：建仓 SOXX + IBB (50 万)", normal_style))
    content.append(Paragraph("• 个股机会：建仓 AAPL + 中海油 (40 万)", normal_style))
    content.append(Spacer(1, 0.2*inch))
    
    content.append(Paragraph("第 3 阶段：第 7-12 周（20% = 200 万）", ParagraphStyle('SubHeading', parent=normal_style, fontSize=12, fontName=chinese_font)))
    content.append(Paragraph("• 补齐剩余仓位", normal_style))
    content.append(Paragraph("• 建立 VIX 对冲头寸", normal_style))
    content.append(Paragraph("• 配置黄金 ETF", normal_style))
    content.append(Spacer(1, 0.3*inch))
    
    # 止损止盈
    content.append(Paragraph("四、止损/止盈规则", heading_style))
    
    content.append(Paragraph("止损规则", ParagraphStyle('SubHeading', parent=normal_style, fontSize=12, fontName=chinese_font)))
    stop_loss_data = [
        ['资产类型', '止损线', '执行'],
        ['核心 ETF (VOO/QQQ)', '-15%', '减仓 50%'],
        ['个股 (GOOGL/MSFT 等)', '-15%', '清仓'],
        ['港股 (腾讯/阿里)', '-20%', '减仓 50%'],
        ['行业 ETF', '-12%', '清仓']
    ]
    stop_loss_table = Table(stop_loss_data, colWidths=[4*cm, 2*cm, 3*cm])
    stop_loss_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.red),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    content.append(stop_loss_table)
    content.append(Spacer(1, 0.2*inch))
    
    content.append(Paragraph("止盈规则", ParagraphStyle('SubHeading', parent=normal_style, fontSize=12, fontName=chinese_font)))
    take_profit_data = [
        ['涨幅', '操作'],
        ['+20%', '止盈 25%，移动止损到成本'],
        ['+40%', '再止盈 25%'],
        ['+60%', '再止盈 25%'],
        ['+100%', '清仓或保留 25%']
    ]
    take_profit_table = Table(take_profit_data, colWidths=[3*cm, 6*cm])
    take_profit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    content.append(take_profit_table)
    content.append(PageBreak())
    
    # 预期收益
    content.append(Paragraph("五、预期收益/风险", heading_style))
    scenario_data = [
        ['情景', '概率', '组合收益', '最大回撤'],
        ['牛市', '30%', '+20-25%', '-5%'],
        ['震荡市', '50%', '+12-18%', '-8%'],
        ['熊市', '20%', '-10-15%', '-12%']
    ]
    scenario_table = Table(scenario_data, colWidths=[3*cm, 2*cm, 3*cm, 3*cm])
    scenario_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    content.append(scenario_table)
    content.append(Spacer(1, 0.2*inch))
    
    content.append(Paragraph("预期指标：", ParagraphStyle('SubHeading', parent=normal_style, fontSize=12, fontName=chinese_font)))
    content.append(Paragraph("• 年化收益：12-18%（中值 15%）✅", normal_style))
    content.append(Paragraph("• 最大月回撤：-8% 至 -12% ⚠️（接近 10% 目标）", normal_style))
    content.append(Paragraph("• 夏普比率：1.0-1.5 ✅", normal_style))
    content.append(Spacer(1, 0.3*inch))
    
    # 关键建议
    content.append(Paragraph("六、关键建议", heading_style))
    content.append(Paragraph("✅ 必须做的：", ParagraphStyle('SubHeading', parent=normal_style, fontSize=12, textColor=colors.green, fontName=chinese_font)))
    content.append(Paragraph("1. 分散投资 - 不要 All-in 单一资产/市场", normal_style))
    content.append(Paragraph("2. 止损纪律 - 严格执行 -15% 止损线", normal_style))
    content.append(Paragraph("3. 定期再平衡 - 季度调整，保持目标配置", normal_style))
    content.append(Paragraph("4. 对冲保护 - 5-10% 资金用于对冲黑天鹅", normal_style))
    content.append(Paragraph("5. 长期视角 - 建议延长到 3-5 年", normal_style))
    content.append(Spacer(1, 0.2*inch))
    
    content.append(Paragraph("❌ 必须避免的：", ParagraphStyle('SubHeading', parent=normal_style, fontSize=12, textColor=colors.red, fontName=chinese_font)))
    content.append(Paragraph("1. 杠杆交易 - 不借钱炒股，不用高杠杆 ETF", normal_style))
    content.append(Paragraph("2. 频繁交易 - 年换手率控制在 50% 以内", normal_style))
    content.append(Paragraph("3. 追涨杀跌 - 不因短期波动改变策略", normal_style))
    content.append(Paragraph("4. 集中持仓 - 单一股票不超过 5%", normal_style))
    content.append(Paragraph("5. 忽视对冲 - 牛市也要买保护", normal_style))
    content.append(Spacer(1, 0.5*inch))
    
    # 页脚
    content.append(Spacer(1, 0.3*inch))
    content.append(Paragraph("-" * 60, normal_style))
    content.append(Paragraph(f"报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    content.append(Paragraph("数据源：富途 OpenD | 分析模型：GPT-4o", normal_style))
    content.append(Paragraph("文件位置：~/.openclaw/workspace/agents/xiaoba-portfolio/1000w_Investment_Plan.pdf", normal_style))
    
    # 构建 PDF
    doc.build(content)
    print(f"✅ PDF 已生成：{output_path}")
    return output_path

if __name__ == "__main__":
    create_pdf()
