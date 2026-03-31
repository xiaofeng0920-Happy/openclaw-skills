#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合检查脚本 - 每 30 分钟自动运行
检查持仓、价格、止损止盈、新闻等
"""

import json
from datetime import datetime
from futu import OpenQuoteContext, RET_OK

CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"

def load_portfolio():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def send_feishu(message):
    import subprocess
    cmd = ["openclaw", "message", "send", "--channel", "feishu", "--target", FEISHU_USER_ID, "--message", message]
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"发送失败：{e}")
        return False

def check_portfolio():
    """综合检查"""
    print(f"[{datetime.now()}] 开始综合检查...")
    
    portfolio = load_portfolio()
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    alerts = []
    highlights = []
    
    # 检查美股
    for holding in portfolio['accounts']['us_stocks']['holdings']:
        symbol = holding['symbol']
        pnl_pct = holding['pnl_percent']
        
        # 止损检查
        if pnl_pct <= -10:
            alerts.append(f"🛑 {symbol} 止损：{pnl_pct:+.1f}%")
        # 止盈检查
        elif pnl_pct >= 20:
            highlights.append(f"✅ {symbol} 止盈：{pnl_pct:+.1f}% 🔥")
        # 大涨检查
        elif pnl_pct >= 5:
            highlights.append(f"🟢 {symbol} 大涨：{pnl_pct:+.1f}%")
    
    # 检查港股
    for holding in portfolio['accounts']['hk_stocks']['holdings']:
        symbol = holding['symbol']
        pnl_pct = holding['pnl_percent']
        
        # 止损检查
        if pnl_pct <= -10:
            alerts.append(f"🛑 {symbol} 止损：{pnl_pct:+.1f}%")
        # 止盈检查
        elif pnl_pct >= 20:
            highlights.append(f"✅ {symbol} 止盈：{pnl_pct:+.1f}% 🔥")
        # 大涨检查
        elif pnl_pct >= 5:
            highlights.append(f"🟢 {symbol} 大涨：{pnl_pct:+.1f}%")
    
    quote_ctx.close()
    
    # 生成报告
    report_lines = ["🔍 持仓检查", f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    
    if highlights:
        report_lines.append("✨ 亮点")
        report_lines.extend(highlights)
        report_lines.append("")
    
    if alerts:
        report_lines.append("⚠️ 预警")
        report_lines.extend(alerts)
        report_lines.append("")
    
    # 汇总
    us_pnl = portfolio['accounts']['us_stocks']['pnl_percent']
    hk_pnl = portfolio['accounts']['hk_stocks']['pnl_percent']
    
    report_lines.append("📊 总览")
    report_lines.append(f"  美股：{us_pnl:+.1f}%")
    report_lines.append(f"  港股：{hk_pnl:+.1f}%")
    report_lines.append("")
    
    # 只有重要消息才发送
    if alerts or [h for h in highlights if '🔥' in h]:
        send_feishu("\n".join(report_lines))
        print(f"✅ 已发送报告（{len(alerts)} 预警 + {len(highlights)} 亮点）")
    else:
        print("ℹ️ 无重要变化，不发送报告")
    
    return True

if __name__ == "__main__":
    check_portfolio()
