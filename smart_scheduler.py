#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能调度脚本 - 区分交易时段和非交易时段
交易时段：每 30 分钟更新价格 + 检查持仓
非交易时段：仅监控新闻和财报
"""

import json
from datetime import datetime, timedelta
from futu import OpenQuoteContext, RET_OK
import subprocess

CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"

def is_trading_hour():
    """判断是否在交易时段"""
    now = datetime.now()
    weekday = now.weekday()
    
    if weekday >= 5:
        return False
    
    hour = now.hour
    minute = now.minute
    
    hk_morning = (9, 30) <= (hour, minute) < (12, 0)
    hk_afternoon = (13, 0) <= (hour, minute) < (16, 0)
    us_night = hour >= 21 or hour < 4
    
    return hk_morning or hk_afternoon or us_night

def is_market_open():
    """判断市场是否开盘"""
    now = datetime.now()
    weekday = now.weekday()
    
    if weekday >= 5:
        return False
    
    hour = now.hour
    minute = now.minute
    
    hk_open = (9, 30) <= (hour, minute) < (16, 0)
    us_open = hour >= 21 or hour < 4
    
    return hk_open or us_open

def load_portfolio():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def send_feishu(message):
    cmd = ["openclaw", "message", "send", "--channel", "feishu", "--target", FEISHU_USER_ID, "--message", message]
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"发送失败：{e}")
        return False

def update_prices():
    """更新价格"""
    print("🔄 更新价格...")
    try:
        subprocess.run(["python3", "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/sync_prices.py"], 
                      timeout=60, capture_output=True)
        print("✅ 价格已更新")
        return True
    except Exception as e:
        print(f"❌ 更新失败：{e}")
        return False

def check_portfolio():
    """检查持仓（显示股票名、当日涨跌幅、成本盈亏、金额变化）"""
    print("📊 检查持仓...")
    
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    portfolio = load_portfolio()
    
    alerts = []
    highlights = []
    
    total_change_usd = 0
    total_change_hkd = 0
    
    # 获取美股实时涨跌幅
    us_codes = [f"US.{h['symbol']}" for h in portfolio['accounts']['us_stocks']['holdings']]
    if us_codes:
        ret, data = quote_ctx.get_market_snapshot(us_codes)
        if ret == RET_OK:
            for i, code in enumerate(us_codes):
                symbol = code.split('.')[1]
                last_price = float(data['last_price'][i])
                prev_close = float(data['prev_close_price'][i]) if 'prev_close_price' in data.columns else last_price
                today_change = ((last_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
                
                # 获取持仓信息
                holding = next((h for h in portfolio['accounts']['us_stocks']['holdings'] if h['symbol'] == symbol), None)
                if holding:
                    name = holding.get('name', symbol)
                    shares = holding.get('shares', 0)
                    cost_pnl = holding['pnl_percent']
                    today_change_value = (last_price - prev_close) * shares if prev_close > 0 else 0
                    total_change_usd += today_change_value
                    
                    if abs(today_change) >= 3:
                        value_str = f"(${today_change_value:+,.0f})"
                        if today_change >= 5:
                            highlights.append(f"🟢 {name}({symbol}): 今日{today_change:+.1f}% {value_str} | 成本{cost_pnl:+.1f}% 🔥")
                        elif today_change <= -5:
                            alerts.append(f"🔴 {name}({symbol}): 今日{today_change:+.1f}% {value_str} | 成本{cost_pnl:+.1f}%")
                        else:
                            highlights.append(f"📈 {name}({symbol}): 今日{today_change:+.1f}% {value_str} | 成本{cost_pnl:+.1f}%")
    
    # 获取港股实时涨跌幅
    hk_codes = [f"HK.{h['symbol'].replace('.HK', '')}" for h in portfolio['accounts']['hk_stocks']['holdings']]
    if hk_codes:
        ret, data = quote_ctx.get_market_snapshot(hk_codes)
        if ret == RET_OK:
            for i, code in enumerate(hk_codes):
                symbol = code.split('.')[1] + ".HK"
                last_price = float(data['last_price'][i])
                prev_close = float(data['prev_close_price'][i]) if 'prev_close_price' in data.columns else last_price
                today_change = ((last_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
                
                # 获取持仓信息
                holding = next((h for h in portfolio['accounts']['hk_stocks']['holdings'] if h['symbol'] == symbol), None)
                if holding:
                    name = holding.get('name', symbol)
                    shares = holding.get('shares', 0)
                    cost_pnl = holding['pnl_percent']
                    today_change_value = (last_price - prev_close) * shares if prev_close > 0 else 0
                    total_change_hkd += today_change_value
                    
                    if abs(today_change) >= 3:
                        value_str = f"(HK${today_change_value:+,.0f})"
                        if today_change >= 5:
                            highlights.append(f"🟢 {name}({symbol}): 今日{today_change:+.1f}% {value_str} | 成本{cost_pnl:+.1f}% 🔥")
                        elif today_change <= -5:
                            alerts.append(f"🔴 {name}({symbol}): 今日{today_change:+.1f}% {value_str} | 成本{cost_pnl:+.1f}%")
                        else:
                            highlights.append(f"📈 {name}({symbol}): 今日{today_change:+.1f}% {value_str} | 成本{cost_pnl:+.1f}%")
    
    quote_ctx.close()
    
    # 生成报告
    if alerts or highlights:
        report = ["🔍 股价异动", f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
        
        # 汇总金额变化
        report.append(f"💰 今日持仓变化：美股 ${total_change_usd:+,.0f} | 港股 HK${total_change_hkd:+,.0f}")
        report.append("")
        
        if highlights:
            report.append("✨ 亮点")
            report.extend(highlights)
            report.append("")
        
        if alerts:
            report.append("⚠️ 预警")
            report.extend(alerts)
            report.append("")
        
        report.append("💡 说明：今日=当日涨跌幅 | 成本=持仓盈亏 | 金额=今日变化")
        
        send_feishu("\n".join(report))
        print(f"✅ 已发送报告（{len(alerts)} 预警 + {len(highlights)} 亮点）")
    else:
        print("ℹ️ 无股价异动（±3% 以内）")
    
    return True

def monitor_news():
    """监控新闻"""
    print("📰 监控新闻...")
    try:
        subprocess.run(["python3", "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/news_monitor.py"], 
                      timeout=60, capture_output=True)
        print("✅ 新闻已监控")
        return True
    except Exception as e:
        print(f"❌ 新闻监控失败：{e}")
        return False

def check_earnings():
    """检查财报"""
    print("📅 检查财报...")
    try:
        subprocess.run(["python3", "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/earnings_reminder.py"], 
                      timeout=60, capture_output=True)
        print("✅ 财报已检查")
        return True
    except Exception as e:
        print(f"❌ 财报检查失败：{e}")
        return False

def run_scheduler():
    """主调度逻辑"""
    print(f"[{datetime.now()}] 智能调度检查...")
    
    if is_market_open():
        print("📈 市场开盘中 - 执行交易时段任务")
        update_prices()
        check_portfolio()
    elif is_trading_hour():
        print("📊 交易时段（盘前/盘后）- 执行基础检查")
        check_portfolio()
    else:
        print("🌙 非交易时段 - 仅监控新闻和财报")
        monitor_news()
        check_earnings()
    
    print("✅ 调度完成")
    return True

if __name__ == "__main__":
    run_scheduler()
