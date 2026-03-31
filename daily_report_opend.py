#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锋哥持仓日报 - 富途 OpenAPI 版本
每个交易日早上 8:00 自动生成并发送飞书消息
数据源：富途 OpenD (本地)
"""

import json
import sys
from datetime import datetime
from futu import *

# ============ 配置 ============
CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"
# =============================

def load_portfolio():
    """加载持仓配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_realtime_price(quote_ctx, symbol, market):
    """获取实时价格"""
    try:
        if market == 'US':
            code = f"US.{symbol}"
        else:
            code = f"HK.{symbol}"
        
        ret, data = quote_ctx.get_market_snapshot(code)
        if ret == RET_OK and len(data) > 0:
            return float(data['last_price'][0])
        return None
    except Exception as e:
        print(f"获取 {symbol} 价格失败：{e}")
        return None

def calculate_pnl(shares, avg_cost, current_price, is_hkd=False):
    """计算盈亏"""
    value = shares * current_price
    cost = shares * avg_cost
    pnl = value - cost
    pnl_percent = (pnl / cost) * 100 if cost != 0 else 0
    return value, pnl, pnl_percent

def format_currency(amount, is_hkd=False):
    """格式化金额"""
    currency = "HKD" if is_hkd else "USD"
    sign = "+" if amount >= 0 else ""
    return f"{sign}{amount:,.0f} {currency}"

def generate_report():
    """生成持仓日报"""
    print(f"[{datetime.now()}] 开始生成持仓日报...")
    
    # 连接 OpenD
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    # 验证连接
    ret, state = quote_ctx.get_global_state()
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！")
        return None
    
    print("✅ OpenD 连接成功")
    
    # 加载持仓
    portfolio = load_portfolio()
    
    # 获取实时价格并计算
    report_lines = []
    report_lines.append(f"📊 锋哥持仓日报")
    report_lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report_lines.append("")
    
    # === 美股账户 ===
    us_account = portfolio['accounts']['us_stocks']
    us_total_value = 0
    us_total_pnl = 0
    
    report_lines.append("🇺🇸 美股账户")
    report_lines.append("-" * 40)
    
    for holding in us_account['holdings']:
        symbol = holding['symbol']
        shares = holding['shares']
        avg_cost = holding['avg_cost_usd']
        
        # 获取实时价格
        current_price = get_realtime_price(quote_ctx, symbol, 'US')
        if current_price is None:
            current_price = holding['current_price_usd']  # 使用缓存价格
        
        value, pnl, pnl_pct = calculate_pnl(shares, avg_cost, current_price)
        us_total_value += value
        us_total_pnl += pnl
        
        status_emoji = "🟢" if pnl >= 0 else "🔴"
        report_lines.append(f"{status_emoji} {symbol}: ${current_price:.2f} | 盈亏：{format_currency(pnl)} ({pnl_pct:+.1f}%)")
    
    report_lines.append(f"  合计：${us_total_value:,.0f} | 盈亏：{format_currency(us_total_pnl)} ({us_total_pnl/us_account['value_usd']*100:+.1f}%)")
    report_lines.append("")
    
    # === 港股账户 ===
    hk_account = portfolio['accounts']['hk_stocks']
    hk_total_value = 0
    hk_total_pnl = 0
    
    report_lines.append("🇭🇰 港股账户")
    report_lines.append("-" * 40)
    
    for holding in hk_account['holdings']:
        name = holding.get('name', '')
        symbol = holding['symbol'].replace('.HK', '')
        shares = holding['shares']
        avg_cost = holding['avg_cost_hkd']
        
        # 获取实时价格
        current_price = get_realtime_price(quote_ctx, symbol, 'HK')
        if current_price is None:
            current_price = holding['current_price_hkd']  # 使用缓存价格
        
        value, pnl, pnl_pct = calculate_pnl(shares, avg_cost, current_price, is_hkd=True)
        hk_total_value += value
        hk_total_pnl += pnl
        
        status_emoji = "🟢" if pnl >= 0 else "🔴"
        display_name = f"{name}({symbol})" if name else symbol
        report_lines.append(f"{status_emoji} {display_name}: ${current_price:.2f} | 盈亏：{format_currency(pnl, is_hkd=True)} ({pnl_pct:+.1f}%)")
    
    report_lines.append(f"  合计：${hk_total_value:,.0f} HKD | 盈亏：{format_currency(hk_total_pnl, is_hkd=True)}")
    report_lines.append("")
    
    # === 总结 ===
    total_value_usd = us_total_value + (hk_total_value / 7.8)  # 粗略换算
    total_pnl_usd = us_total_pnl + (hk_total_pnl / 7.8)
    total_pnl_pct = (total_pnl_usd / (total_value_usd - total_pnl_usd)) * 100 if (total_value_usd - total_pnl_usd) != 0 else 0
    
    report_lines.append("📈 总资产")
    report_lines.append("-" * 40)
    report_lines.append(f"  总值：≈${total_value_usd:,.0f} USD")
    report_lines.append(f"  盈亏：{format_currency(total_pnl_usd)} ({total_pnl_pct:+.1f}%)")
    report_lines.append("")
    
    # ===  highlights ===
    report_lines.append("✨ 今日亮点")
    report_lines.append("-" * 40)
    
    # 找出表现最好的股票
    best_us = max(us_account['holdings'], key=lambda x: x['pnl_percent'])
    best_hk = max(hk_account['holdings'], key=lambda x: x['pnl_percent'])
    
    report_lines.append(f"  🏆 美股最佳：{best_us['symbol']} ({best_us['pnl_percent']:+.1f}%)")
    report_lines.append(f"  🏆 港股最佳：{best_hk['symbol']} ({best_hk['pnl_percent']:+.1f}%)")
    
    quote_ctx.close()
    
    return "\n".join(report_lines)

def send_feishu(message):
    """发送飞书消息"""
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
        print(f"❌ 发送飞书消息失败：{e}")

if __name__ == "__main__":
    report = generate_report()
    if report:
        send_feishu(report)
        print("✅ 持仓日报生成完成！")
    else:
        print("❌ 生成失败")
        sys.exit(1)
