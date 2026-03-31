#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锋哥真实持仓配置 - 最终完整版
数据来源：富途牛牛 APP 截图 (2026-03-24 13:21-13:27)
账户：保证金综合账户 (8093)
总资产：$886,186.27 USD
"""

import json
import shutil
from datetime import datetime

CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
BACKUP_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.backup_20260324.json"

def calculate_status(pnl_pct):
    if pnl_pct >= 5:
        return "盈利", "继续持有"
    elif pnl_pct >= 0:
        return "持平", "继续持有"
    elif pnl_pct >= -5:
        return "小亏", "持有"
    else:
        return "亏损", "等待反弹"

def update_portfolio():
    # 备份
    shutil.copy2(CONFIG_FILE, BACKUP_FILE)
    print(f"✅ 已备份配置文件")
    
    # 加载旧配置
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        portfolio = json.load(f)
    
    # ============ 更新美股股票 ============
    print("\n🇺🇸 更新美股持仓...")
    US_STOCKS = [
        {"name": "英伟达", "symbol": "NVDA", "shares": 287, "avg_cost": 187.157, "price": 174.85},
        {"name": "微软", "symbol": "MSFT", "shares": 156, "avg_cost": 459.077, "price": 381.33},
        {"name": "可口可乐", "symbol": "KO", "shares": 1689, "avg_cost": 72.875, "price": 74.92},
        {"name": "苹果", "symbol": "AAPL", "shares": 329, "avg_cost": 260.147, "price": 250.37},
        {"name": "甲骨文", "symbol": "ORCL", "shares": 647, "avg_cost": 152.65, "price": 152.65},
        {"name": "谷歌-A", "symbol": "GOOGL", "shares": 583, "avg_cost": 302.37, "price": 304.62},
        {"name": "伯克希尔-B", "symbol": "BRK.B", "shares": 104, "avg_cost": 464.53, "price": 480.13},
    ]
    
    portfolio['accounts']['us_stocks']['holdings'] = []
    us_total_value = 0
    us_total_pnl = 0
    
    for stock in US_STOCKS:
        value = stock['shares'] * stock['price']
        cost = stock['shares'] * stock['avg_cost']
        pnl = value - cost
        pnl_pct = (pnl / cost) * 100 if cost != 0 else 0
        status, suggestion = calculate_status(pnl_pct)
        
        portfolio['accounts']['us_stocks']['holdings'].append({
            "name": stock['name'],
            "symbol": stock['symbol'],
            "shares": stock['shares'],
            "avg_cost_usd": stock['avg_cost'],
            "current_price_usd": stock['price'],
            "value_usd": value,
            "pnl_usd": pnl,
            "pnl_percent": pnl_pct,
            "status": status,
            "suggestion": suggestion
        })
        us_total_value += value
        us_total_pnl += pnl
        print(f"  ✅ {stock['symbol']}: {stock['shares']} 股 | ${stock['price']:.2f} | {pnl_pct:+.1f}%")
    
    portfolio['accounts']['us_stocks']['value_usd'] = us_total_value
    portfolio['accounts']['us_stocks']['pnl_usd'] = us_total_pnl
    portfolio['accounts']['us_stocks']['pnl_percent'] = (us_total_pnl / (us_total_value - us_total_pnl)) * 100 if (us_total_value - us_total_pnl) != 0 else 0
    print(f"  合计：${us_total_value:,.0f} | 盈亏：${us_total_pnl:,.0f} ({portfolio['accounts']['us_stocks']['pnl_percent']:+.1f}%)")
    
    # ============ 更新美股期权 ============
    print("\n📊 更新美股期权...")
    US_OPTIONS = [
        {"symbol": "NVDA", "type": "PUT", "expiry": "2027-01-15", "strike": 125, "qty": 2, "avg_cost": 7.50, "price": 6.925},
        {"symbol": "MSFT", "type": "CALL", "expiry": "2026-04-24", "strike": 440, "qty": 5, "avg_cost": 1.90, "price": 0.445},
        {"symbol": "KO", "type": "CALL", "expiry": "2026-04-24", "strike": 80, "qty": 10, "avg_cost": 0.705, "price": 0.3453},
        {"symbol": "KO", "type": "PUT", "expiry": "2026-05-15", "strike": 72.5, "qty": -5, "avg_cost": 1.45, "price": 1.42},
        {"symbol": "GOOGL", "type": "CALL", "expiry": "2026-06-18", "strike": 320, "qty": 20, "avg_cost": 15.50, "price": 15.60},
        {"symbol": "BRK.B", "type": "PUT", "expiry": "2026-05-15", "strike": 470, "qty": -2, "avg_cost": 8.08, "price": 9.652},
        {"symbol": "MU", "type": "CALL", "expiry": "2026-07-17", "strike": 550, "qty": 2, "avg_cost": 10.342, "price": 20.684},
        {"symbol": "TSLA", "type": "CALL", "expiry": "2026-04-10", "strike": 405, "qty": 1, "avg_cost": 4.75, "price": 4.75},
    ]
    
    portfolio['options']['us_options'] = []
    for opt in US_OPTIONS:
        multiplier = 100
        value = abs(opt['qty']) * multiplier * opt['price']
        cost = abs(opt['qty']) * multiplier * opt['avg_cost']
        pnl = value - cost if opt['qty'] > 0 else cost - value
        
        portfolio['options']['us_options'].append({
            "symbol": opt['symbol'],
            "type": opt['type'],
            "expiry": opt['expiry'],
            "strike": opt['strike'],
            "quantity": opt['qty'],
            "avg_cost": opt['avg_cost'],
            "current_price": opt['price'],
            "value_usd": value if opt['qty'] > 0 else -value,
            "pnl_usd": pnl,
            "status": "盈利" if pnl >= 0 else "亏损"
        })
        print(f"  ✅ {opt['symbol']} {opt['type']} {opt['strike']}: {opt['qty']} 张 | ${pnl:+,.0f}")
    
    # ============ 更新港股股票 ============
    print("\n🇭🇰 更新港股持仓...")
    HK_STOCKS = [
        {"name": "腾讯控股", "symbol": "00700.HK", "shares": 2500, "avg_cost": 585.78, "price": 506.00},
        {"name": "南方日经 225", "symbol": "03153.HK", "shares": 13330, "avg_cost": 119.50, "price": 104.60},
        {"name": "中国海洋石油", "symbol": "00883.HK", "shares": 15000, "avg_cost": 10.428, "price": 29.98},
        {"name": "阿里巴巴-W", "symbol": "09988.HK", "shares": 6700, "avg_cost": 140.322, "price": 121.00},
        {"name": "南方两倍做多", "symbol": "07709.HK", "shares": 20500, "avg_cost": 20.976, "price": 30.08},
        {"name": "潍柴动力", "symbol": "02338.HK", "shares": 16000, "avg_cost": 26.42, "price": 26.40},
        {"name": "心动公司", "symbol": "02400.HK", "shares": 3600, "avg_cost": 73.65, "price": 67.10},
        {"name": "紫金矿业", "symbol": "02899.HK", "shares": 6000, "avg_cost": 41.46, "price": 34.02},
        {"name": "智谱", "symbol": "02513.HK", "shares": 200, "avg_cost": 590.00, "price": 625.50},
    ]
    
    portfolio['accounts']['hk_stocks']['holdings'] = []
    hk_total_value = 0
    hk_total_pnl = 0
    
    for stock in HK_STOCKS:
        value = stock['shares'] * stock['price']
        cost = stock['shares'] * stock['avg_cost']
        pnl = value - cost
        pnl_pct = (pnl / cost) * 100 if cost != 0 else 0
        status, suggestion = calculate_status(pnl_pct)
        
        portfolio['accounts']['hk_stocks']['holdings'].append({
            "name": stock['name'],
            "symbol": stock['symbol'],
            "shares": stock['shares'],
            "avg_cost_hkd": stock['avg_cost'],
            "current_price_hkd": stock['price'],
            "value_hkd": value,
            "pnl_hkd": pnl,
            "pnl_percent": pnl_pct,
            "status": status,
            "suggestion": suggestion
        })
        hk_total_value += value
        hk_total_pnl += pnl
        print(f"  ✅ {stock['symbol']}: {stock['shares']} 股 | ${stock['price']:.2f} | {pnl_pct:+.1f}%")
    
    portfolio['accounts']['hk_stocks']['value_hkd'] = hk_total_value
    portfolio['accounts']['hk_stocks']['pnl_hkd'] = hk_total_pnl
    portfolio['accounts']['hk_stocks']['pnl_percent'] = (hk_total_pnl / (hk_total_value - hk_total_pnl)) * 100 if (hk_total_value - hk_total_pnl) != 0 else 0
    print(f"  合计：${hk_total_value:,.0f} HKD | 盈亏：${hk_total_pnl:,.0f} HKD ({portfolio['accounts']['hk_stocks']['pnl_percent']:+.1f}%)")
    
    # ============ 更新港股期权 ============
    print("\n📊 更新港股期权...")
    HK_OPTIONS = [
        {"symbol": "00700.HK", "type": "PUT", "expiry": "2026-03-27", "strike": 510, "qty": -5, "avg_cost": 1.0, "price": 1.0},
        {"symbol": "00700.HK", "type": "CALL", "expiry": "2026-05-28", "strike": 600, "qty": 10, "avg_cost": 4.84, "price": 13.58},
        {"symbol": "00700.HK", "type": "CALL", "expiry": "2026-03-27", "strike": 540, "qty": 20, "avg_cost": 1.0, "price": 1.0},
        {"symbol": "00883.HK", "type": "CALL", "expiry": "2026-04-29", "strike": 28, "qty": -15, "avg_cost": 1.447, "price": 2.73},
        {"symbol": "00883.HK", "type": "CALL", "expiry": "2026-04-29", "strike": 28, "qty": 1, "avg_cost": 9.328, "price": 1.20},
        {"symbol": "09988.HK", "type": "CALL", "expiry": "2026-05-28", "strike": 160, "qty": 10, "avg_cost": 2.32, "price": 0.82},
        {"symbol": "09988.HK", "type": "CALL", "expiry": "2026-03-30", "strike": 130, "qty": 22, "avg_cost": 1.20, "price": 0.33},
    ]
    
    portfolio['options']['hk_options'] = []
    for opt in HK_OPTIONS:
        multiplier = 1000
        value = abs(opt['qty']) * multiplier * opt['price']
        cost = abs(opt['qty']) * multiplier * opt['avg_cost']
        pnl = value - cost if opt['qty'] > 0 else cost - value
        
        portfolio['options']['hk_options'].append({
            "symbol": opt['symbol'],
            "type": opt['type'],
            "expiry": opt['expiry'],
            "strike": opt['strike'],
            "quantity": opt['qty'],
            "avg_cost_hkd": opt['avg_cost'],
            "current_price_hkd": opt['price'],
            "value_hkd": value if opt['qty'] > 0 else -value,
            "pnl_hkd": pnl,
            "pnl_percent": (pnl / cost) * 100 if cost != 0 else 0,
            "status": "盈利" if pnl >= 0 else "亏损"
        })
        print(f"  ✅ {opt['symbol']} {opt['type']} {opt['strike']}: {opt['qty']} 张 | ${pnl:+,.0f} HKD")
    
    # ============ 更新总计 ============
    total_value_usd = us_total_value + (hk_total_value / 7.8)
    total_pnl_usd = us_total_pnl + (hk_total_pnl / 7.8)
    portfolio['total_value_usd'] = total_value_usd
    portfolio['total_pnl_usd'] = total_pnl_usd
    portfolio['total_pnl_percent'] = (total_pnl_usd / (total_value_usd - total_pnl_usd)) * 100 if (total_value_usd - total_pnl_usd) != 0 else 0
    
    # ============ 账户信息 ============
    portfolio['account_info'] = {
        "account_id": "8093",
        "account_type": "保证金综合账户",
        "total_asset_usd": 886186.27,
        "securities_value_usd": 1355016.12,
        "cash_usd": -468829.86,
        "frozen_fund_usd": 160585.20,
        "remaining_liquidity_usd": 285882.46,
        "today_pnl_usd": 21191.23,
        "today_pnl_percent": 2.45
    }
    
    # ============ 保存配置 ============
    portfolio['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    portfolio['source_file'] = "富途牛牛 APP 完整截图 (2026-03-24 13:21-13:27)"
    
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 配置文件已更新！")
    print(f"📅 最后更新：{portfolio['last_updated']}")
    print(f"📊 总估值：≈${total_value_usd:,.0f} USD")
    print(f"   - 美股：${us_total_value:,.0f} ({portfolio['accounts']['us_stocks']['pnl_percent']:+.1f}%)")
    print(f"   - 港股：${hk_total_value:,.0f} HKD ({portfolio['accounts']['hk_stocks']['pnl_percent']:+.1f}%)")
    print(f"💰 总资产：$886,186 (富途显示)")
    print(f"📈 今日盈亏：+$21,191 (+2.45%) 🔥")
    
    return True

if __name__ == "__main__":
    success = update_portfolio()
    exit(0 if success else 1)
