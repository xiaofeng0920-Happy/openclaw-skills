#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据锋哥的真实持仓截图更新配置文件
数据来源：富途牛牛 APP 截图 (2026-03-24 13:21)
账户：保证金综合账户 (8093)
"""

import json
from datetime import datetime

CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
BACKUP_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.backup.json"

# 真实持仓数据（来自截图）
REAL_HOLDINGS = {
    "us_stocks": [
        {
            "name": "英伟达",
            "symbol": "NVDA",
            "shares": 287,
            "avg_cost_usd": 187.157,
            "current_price_usd": 174.85,
            "value_usd": 50181.95,
            "pnl_usd": -226.73,
        },
        {
            "name": "微软",
            "symbol": "MSFT",
            "shares": 156,
            "avg_cost_usd": 459.077,
            "current_price_usd": 381.33,
            "value_usd": 59487.48,
            "pnl_usd": -260.52,
        },
        {
            "name": "可口可乐",
            "symbol": "KO",
            "shares": 1689,
            "avg_cost_usd": 72.875,
            "current_price_usd": 74.92,
            "value_usd": 126539.88,
            "pnl_usd": -320.91,
        },
        {
            "name": "苹果",
            "symbol": "AAPL",
            "shares": 329,
            "avg_cost_usd": 260.147,
            "current_price_usd": 250.37,
            "value_usd": 82371.73,
            "pnl_usd": -368.48,
        },
        {
            "name": "甲骨文",
            "symbol": "ORCL",
            "shares": 647,
            "avg_cost_usd": 152.65,
            "current_price_usd": 152.65,
            "value_usd": 98891.10,
            "pnl_usd": -1093.43,
        },
        {
            "name": "谷歌-A",
            "symbol": "GOOGL",
            "shares": 583,
            "avg_cost_usd": 302.37,
            "current_price_usd": 304.62,
            "value_usd": 177595.97,
            "pnl_usd": 1314.26,
        },
    ],
    "us_options": [
        {
            "symbol": "NVDA",
            "type": "PUT",
            "expiry": "2027-01-15",
            "strike": 125,
            "quantity": 2,
            "avg_cost": 7.50,
            "current_price": 6.925,
            "value_usd": 1385.00,
            "pnl_usd": 0.00,
        },
        {
            "symbol": "MSFT",
            "type": "CALL",
            "expiry": "2026-04-24",
            "strike": 440,
            "quantity": 5,
            "avg_cost": 1.90,
            "current_price": 0.445,
            "value_usd": 222.50,
            "pnl_usd": 0.00,
        },
        {
            "symbol": "KO",
            "type": "CALL",
            "expiry": "2026-04-24",
            "strike": 80,
            "quantity": 10,
            "avg_cost": 0.705,
            "current_price": 0.3453,
            "value_usd": 345.30,
            "pnl_usd": 0.00,
        },
        {
            "symbol": "KO",
            "type": "PUT",
            "expiry": "2026-05-15",
            "strike": 72.5,
            "quantity": -5,
            "avg_cost": 1.45,
            "current_price": 1.42,
            "value_usd": -710.00,
            "pnl_usd": 0.00,
        },
        {
            "symbol": "GOOGL",
            "type": "CALL",
            "expiry": "2026-06-18",
            "strike": 320,
            "quantity": 20,
            "avg_cost": 15.50,
            "current_price": 15.60,
            "value_usd": 11049.00,
            "pnl_usd": 0.00,
        },
    ]
}

def update_portfolio():
    """更新配置文件"""
    import shutil
    
    # 备份旧配置
    shutil.copy2(CONFIG_FILE, BACKUP_FILE)
    print(f"✅ 已备份配置文件到 {BACKUP_FILE}")
    
    # 加载旧配置
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        portfolio = json.load(f)
    
    # 更新美股持仓
    print("\n📊 更新美股持仓...")
    portfolio['accounts']['us_stocks']['holdings'] = []
    
    total_value = 0
    total_pnl = 0
    
    for real_holding in REAL_HOLDINGS['us_stocks']:
        # 计算盈亏百分比
        cost = real_holding['shares'] * real_holding['avg_cost_usd']
        pnl_pct = (real_holding['pnl_usd'] / cost) * 100 if cost != 0 else 0
        
        # 确定状态和建议
        if pnl_pct >= 5:
            status = "盈利"
            suggestion = "继续持有"
        elif pnl_pct >= 0:
            status = "持平"
            suggestion = "继续持有"
        elif pnl_pct >= -5:
            status = "小亏"
            suggestion = "持有"
        else:
            status = "亏损"
            suggestion = "等待反弹"
        
        holding = {
            "name": real_holding['name'],
            "symbol": real_holding['symbol'],
            "shares": real_holding['shares'],
            "avg_cost_usd": real_holding['avg_cost_usd'],
            "current_price_usd": real_holding['current_price_usd'],
            "value_usd": real_holding['value_usd'],
            "pnl_usd": real_holding['pnl_usd'],
            "pnl_percent": pnl_pct,
            "status": status,
            "suggestion": suggestion
        }
        
        portfolio['accounts']['us_stocks']['holdings'].append(holding)
        total_value += real_holding['value_usd']
        total_pnl += real_holding['pnl_usd']
        
        print(f"  ✅ {real_holding['symbol']}: {real_holding['shares']} 股 | ${real_holding['current_price_usd']:.2f} | {pnl_pct:+.1f}%")
    
    # 更新美股账户总计
    portfolio['accounts']['us_stocks']['value_usd'] = total_value
    portfolio['accounts']['us_stocks']['pnl_usd'] = total_pnl
    portfolio['accounts']['us_stocks']['pnl_percent'] = (total_pnl / (total_value - total_pnl)) * 100 if (total_value - total_pnl) != 0 else 0
    
    print(f"\n  合计：${total_value:,.0f} | 盈亏：${total_pnl:,.0f} ({portfolio['accounts']['us_stocks']['pnl_percent']:+.1f}%)")
    
    # 更新期权持仓
    print("\n📊 更新美股期权...")
    portfolio['options']['us_options'] = []
    
    for option in REAL_HOLDINGS['us_options']:
        portfolio['options']['us_options'].append(option)
        print(f"  ✅ {option['symbol']} {option['type']} {option['strike']} {option['expiry']}: {option['quantity']} 张")
    
    # 更新时间
    portfolio['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    portfolio['source_file'] = "富途牛牛 APP 截图 (2026-03-24 13:21)"
    
    # 保存新配置
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 配置文件已更新！")
    print(f"📅 最后更新：{portfolio['last_updated']}")
    print(f"📊 美股持仓：{len(portfolio['accounts']['us_stocks']['holdings'])} 只股票 + {len(portfolio['options']['us_options'])} 个期权")
    
    return True

if __name__ == "__main__":
    success = update_portfolio()
    exit(0 if success else 1)
