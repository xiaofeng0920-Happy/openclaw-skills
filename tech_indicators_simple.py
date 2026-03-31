#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标计算 - 简化版
基于实时价格计算简单指标
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime
from futu import OpenQuoteContext, RET_OK

CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
TECH_CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/config/tech_indicators.json"

def load_portfolio():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_tech_config(config):
    import os
    os.makedirs(os.path.dirname(TECH_CONFIG_FILE), exist_ok=True)
    with open(TECH_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def send_feishu(message):
    import subprocess
    cmd = ["openclaw", "message", "send", "--channel", "feishu", "--target", "ou_636c8e8b7ad36d7fc28e6cf90c350fdd", "--message", message]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"发送失败：{e}")

def generate_tech_report():
    print(f"[{datetime.now()}] 计算技术指标...")
    
    portfolio = load_portfolio()
    tech_config = {'last_updated': datetime.now().isoformat(), 'indicators': {}}
    
    report_lines = ["📊 技术指标日报", f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    
    # 重点股票
    key_stocks = [
        ('GOOGL', 'US', portfolio['accounts']['us_stocks']['holdings']),
        ('BRK.B', 'US', portfolio['accounts']['us_stocks']['holdings']),
        ('KO', 'US', portfolio['accounts']['us_stocks']['holdings']),
        ('00883', 'HK', portfolio['accounts']['hk_stocks']['holdings']),
        ('07709', 'HK', portfolio['accounts']['hk_stocks']['holdings']),
        ('00700', 'HK', portfolio['accounts']['hk_stocks']['holdings']),
    ]
    
    for symbol, market, holdings in key_stocks:
        # 查找持仓数据
        holding = next((h for h in holdings if h['symbol'].replace('.HK', '') == symbol), None)
        if not holding:
            continue
        
        current_price = holding.get('current_price_hkd' if market == 'HK' else 'current_price_usd', 0)
        avg_cost = holding.get('avg_cost_hkd' if market == 'HK' else 'avg_cost_usd', 0)
        pnl_pct = holding.get('pnl_percent', 0)
        
        # 简单技术分析
        if pnl_pct > 20:
            trend = "强势上涨 🟢"
            signal = "持有"
        elif pnl_pct > 5:
            trend = "上涨 🟢"
            signal = "持有"
        elif pnl_pct > -5:
            trend = "震荡 ⚪"
            signal = "观望"
        elif pnl_pct > -10:
            trend = "弱势 🔴"
            signal = "考虑止损"
        else:
            trend = "下跌 🔴"
            signal = "止损"
        
        tech_config['indicators'][symbol] = {
            'price': current_price,
            'trend': trend,
            'signal': signal,
            'pnl_pct': pnl_pct
        }
        
        report_lines.append(f"**{symbol}** ${current_price:.2f}")
        report_lines.append(f"  趋势：{trend}")
        report_lines.append(f"  信号：{signal}")
        report_lines.append(f"  盈亏：{pnl_pct:+.1f}%")
        report_lines.append("")
    
    save_tech_config(tech_config)
    send_feishu("\n".join(report_lines))
    print(f"✅ 已计算 {len(tech_config['indicators'])} 只股票技术指标")
    return True

if __name__ == "__main__":
    generate_tech_report()
