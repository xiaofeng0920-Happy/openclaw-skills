#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资周报/月报 - 定期生成投资总结报告
包含收益分析、持仓变化、市场回顾等
"""

import json
from datetime import datetime, timedelta
from futu import *

CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
BACKUP_DIR = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/backups/"
FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"

def load_portfolio():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_historical_data():
    """加载历史数据（用于对比）"""
    import os
    history = []
    
    if os.path.exists(BACKUP_DIR):
        for filename in sorted(os.listdir(BACKUP_DIR))[-4:]:  # 最近 4 个备份
            if filename.endswith('.json'):
                try:
                    with open(f"{BACKUP_DIR}{filename}", 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        history.append({
                            'date': filename.replace('.json', ''),
                            'data': data
                        })
                except:
                    pass
    
    return history

def calculate_portfolio_metrics(portfolio):
    """计算组合指标"""
    metrics = {
        'total_value_usd': portfolio.get('total_value_usd', 0),
        'us_stocks_value': portfolio['accounts']['us_stocks']['value_usd'],
        'us_stocks_pnl_pct': portfolio['accounts']['us_stocks']['pnl_percent'],
        'hk_stocks_value_hkd': portfolio['accounts']['hk_stocks']['value_hkd'],
        'hk_stocks_pnl_pct': portfolio['accounts']['hk_stocks']['pnl_percent'],
        'us_stocks_count': len(portfolio['accounts']['us_stocks']['holdings']),
        'hk_stocks_count': len(portfolio['accounts']['hk_stocks']['holdings']),
        'us_options_count': len(portfolio['options']['us_options']),
        'hk_options_count': len(portfolio['options']['hk_options']),
    }
    
    # 找出最佳/最差持仓
    us_holdings = portfolio['accounts']['us_stocks']['holdings']
    hk_holdings = portfolio['accounts']['hk_stocks']['holdings']
    
    if us_holdings:
        best_us = max(us_holdings, key=lambda x: x['pnl_percent'])
        worst_us = min(us_holdings, key=lambda x: x['pnl_percent'])
        metrics['best_us'] = f"{best_us['symbol']} ({best_us['pnl_percent']:+.1f}%)"
        metrics['worst_us'] = f"{worst_us['symbol']} ({worst_us['pnl_percent']:+.1f}%)"
    
    if hk_holdings:
        best_hk = max(hk_holdings, key=lambda x: x['pnl_percent'])
        worst_hk = min(hk_holdings, key=lambda x: x['pnl_percent'])
        metrics['best_hk'] = f"{best_hk['symbol']} ({best_hk['pnl_percent']:+.1f}%)"
        metrics['worst_hk'] = f"{worst_hk['symbol']} ({worst_hk['pnl_percent']:+.1f}%)"
    
    return metrics

def generate_weekly_report():
    """生成周报"""
    print(f"[{datetime.now()}] 生成投资周报...")
    
    portfolio = load_portfolio()
    history = load_historical_data()
    metrics = calculate_portfolio_metrics(portfolio)
    
    # 计算周变化
    week_change = None
    if len(history) >= 1:
        old_value = history[0]['data'].get('total_value_usd', 0)
        week_change = ((metrics['total_value_usd'] - old_value) / old_value) * 100 if old_value > 0 else 0
    
    report = []
    report.append("📊 投资周报")
    report.append(f"📅 报告期间：{(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')} - {datetime.now().strftime('%Y-%m-%d')}")
    report.append("")
    
    # 总资产
    report.append("💰 总资产")
    report.append(f"  当前总值：${metrics['total_value_usd']:,.0f} USD")
    if week_change is not None:
        emoji = "🟢" if week_change >= 0 else "🔴"
        report.append(f"  本周变化：{emoji} {week_change:+.1f}%")
    report.append("")
    
    # 美股表现
    report.append("🇺🇸 美股账户")
    us_emoji = "🟢" if metrics['us_stocks_pnl_pct'] >= 0 else "🔴"
    report.append(f"  市值：${metrics['us_stocks_value']:,.0f} {us_emoji} ({metrics['us_stocks_pnl_pct']:+.1f}%)")
    report.append(f"  持仓：{metrics['us_stocks_count']} 只股票 + {metrics['us_options_count']} 个期权")
    if 'best_us' in metrics:
        report.append(f"  最佳：{metrics['best_us']} 🏆")
        report.append(f"  最差：{metrics['worst_us']}")
    report.append("")
    
    # 港股表现
    report.append("🇭🇰 港股账户")
    hk_emoji = "🟢" if metrics['hk_stocks_pnl_pct'] >= 0 else "🔴"
    report.append(f"  市值：${metrics['hk_stocks_value_hkd']:,.0f} HKD {hk_emoji} ({metrics['hk_stocks_pnl_pct']:+.1f}%)")
    report.append(f"  持仓：{metrics['hk_stocks_count']} 只股票 + {metrics['hk_options_count']} 个期权")
    if 'best_hk' in metrics:
        report.append(f"  最佳：{metrics['best_hk']} 🏆")
        report.append(f"  最差：{metrics['worst_hk']}")
    report.append("")
    
    # 本周操作
    report.append("📝 本周操作")
    report.append("  （待补充：买卖记录）")
    report.append("")
    
    # 下周展望
    report.append("🔮 下周展望")
    report.append("  - 关注财报季")
    report.append("  - 关注美联储议息")
    report.append("  - 关注地缘政治")
    report.append("")
    
    # 小巴点评
    report.append("💡 小巴点评")
    if metrics['hk_stocks_pnl_pct'] > metrics['us_stocks_pnl_pct']:
        report.append("  港股表现优于美股，继续持有优质港股～")
    else:
        report.append("  美股稳健，港股等待反弹机会～")
    report.append("")
    
    return "\n".join(report)

def generate_monthly_report():
    """生成月报"""
    print(f"[{datetime.now()}] 生成投资月报...")
    
    portfolio = load_portfolio()
    history = load_historical_data()
    metrics = calculate_portfolio_metrics(portfolio)
    
    # 计算月变化
    month_change = None
    if len(history) >= 4:
        old_value = history[0]['data'].get('total_value_usd', 0)
        month_change = ((metrics['total_value_usd'] - old_value) / old_value) * 100 if old_value > 0 else 0
    
    report = []
    report.append("📊 投资月报")
    report.append(f"📅 报告期间：{(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')} - {datetime.now().strftime('%Y-%m-%d')}")
    report.append("")
    
    # 月度总结
    report.append("🎯 月度总结")
    report.append(f"  总资产：${metrics['total_value_usd']:,.0f} USD")
    if month_change is not None:
        emoji = "🟢" if month_change >= 0 else "🔴"
        report.append(f"  本月收益：{emoji} {month_change:+.1f}%")
    report.append("")
    
    # 资产配置
    report.append("📈 资产配置")
    us_ratio = (metrics['us_stocks_value'] / metrics['total_value_usd']) * 100 if metrics['total_value_usd'] > 0 else 0
    hk_ratio = (metrics['hk_stocks_value_hkd'] / 7.8 / metrics['total_value_usd']) * 100 if metrics['total_value_usd'] > 0 else 0
    report.append(f"  美股：{us_ratio:.1f}%")
    report.append(f"  港股：{hk_ratio:.1f}%")
    report.append("")
    
    # 最佳/最差
    report.append("🏆 月度最佳")
    if 'best_hk' in metrics:
        report.append(f"  港股：{metrics['best_hk']}")
    if 'best_us' in metrics:
        report.append(f"  美股：{metrics['best_us']}")
    report.append("")
    
    report.append("📉 月度最差")
    if 'worst_hk' in metrics:
        report.append(f"  港股：{metrics['worst_hk']}")
    if 'worst_us' in metrics:
        report.append(f"  美股：{metrics['worst_us']}")
    report.append("")
    
    # 市场回顾
    report.append("🌍 市场回顾")
    report.append("  美股：科技股分化，AI 概念持续火热")
    report.append("  港股：震荡整理，等待政策催化")
    report.append("  A 股：结构性行情，新能源反弹")
    report.append("")
    
    # 下月计划
    report.append("📋 下月计划")
    report.append("  - 调整仓位至 60% 股票 +40% 现金")
    report.append("  - 关注财报季机会")
    report.append("  - 止损表现不佳的持仓")
    report.append("")
    
    # 小巴寄语
    report.append("💝 小巴寄语")
    report.append("  投资是场马拉松，保持耐心，坚持价值投资！")
    report.append("  锋哥加油～ (◍•ᴗ•◍)")
    report.append("")
    
    return "\n".join(report)

def send_feishu(message):
    import subprocess
    cmd = [
        "openclaw", "message", "send",
        "--channel", "feishu",
        "--target", FEISHU_USER_ID,
        "--message", message
    ]
    try:
        subprocess.run(cmd, check=True)
        print("✅ 飞书消息已发送")
    except Exception as e:
        print(f"❌ 发送失败：{e}")

def generate_report(report_type='weekly'):
    """生成报告"""
    if report_type == 'weekly':
        report = generate_weekly_report()
    else:
        report = generate_monthly_report()
    
    send_feishu(report)
    return True

if __name__ == "__main__":
    import sys
    report_type = sys.argv[1] if len(sys.argv) > 1 else 'weekly'
    success = generate_report(report_type)
    exit(0 if success else 1)
