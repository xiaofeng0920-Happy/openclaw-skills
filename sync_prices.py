#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓数据同步脚本 - 从富途 OpenD 获取真实价格更新配置文件
每天收盘后自动运行，保持配置文件数据最新
"""

import json
from datetime import datetime
from futu import *

# ============ 配置 ============
CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
BACKUP_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.backup.json"
# =============================

def load_portfolio():
    """加载持仓配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_portfolio(portfolio):
    """保存持仓配置（先备份）"""
    import shutil
    # 备份旧配置
    shutil.copy2(CONFIG_FILE, BACKUP_FILE)
    print(f"✅ 已备份配置文件")
    
    # 保存新配置
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)
    print(f"✅ 已保存新配置")

def get_realtime_prices(quote_ctx, symbols, market):
    """批量获取实时价格"""
    prices = {}
    try:
        codes = []
        for symbol in symbols:
            if market == 'US':
                codes.append(f"US.{symbol}")
            else:
                codes.append(f"HK.{symbol}")
        
        ret, data = quote_ctx.get_market_snapshot(codes)
        if ret == RET_OK:
            for i, code in enumerate(codes):
                symbol = code.split('.')[1]
                prices[symbol] = {
                    'price': float(data['last_price'][i]),
                    'timestamp': datetime.now().isoformat()
                }
                print(f"  {symbol}: ${prices[symbol]['price']:.2f}")
    except Exception as e:
        print(f"❌ 获取价格失败：{e}")
    
    return prices

def update_portfolio(prices, portfolio):
    """更新持仓配置中的价格"""
    updated_count = 0
    
    # 更新美股
    for holding in portfolio['accounts']['us_stocks']['holdings']:
        symbol = holding['symbol']
        if symbol in prices:
            old_price = holding.get('current_price_usd', 0)
            new_price = prices[symbol]['price']
            holding['current_price_usd'] = new_price
            
            # 重新计算盈亏
            value = holding['shares'] * new_price
            cost = holding['shares'] * holding['avg_cost_usd']
            pnl = value - cost
            pnl_pct = (pnl / cost) * 100 if cost != 0 else 0
            
            holding['value_usd'] = value
            holding['pnl_usd'] = pnl
            holding['pnl_percent'] = pnl_pct
            
            # 更新状态
            if pnl_pct >= 5:
                holding['status'] = "盈利"
                holding['suggestion'] = "继续持有"
            elif pnl_pct >= 0:
                holding['status'] = "持平"
                holding['suggestion'] = "继续持有"
            elif pnl_pct >= -5:
                holding['status'] = "小亏"
                holding['suggestion'] = "持有"
            else:
                holding['status'] = "亏损"
                holding['suggestion'] = "等待反弹"
            
            updated_count += 1
            print(f"  ✅ {symbol}: ${old_price:.2f} → ${new_price:.2f} ({pnl_pct:+.1f}%)")
    
    # 更新港股
    for holding in portfolio['accounts']['hk_stocks']['holdings']:
        symbol = holding['symbol'].replace('.HK', '')
        if symbol in prices:
            old_price = holding.get('current_price_hkd', 0)
            new_price = prices[symbol]['price']
            holding['current_price_hkd'] = new_price
            
            # 重新计算盈亏
            value = holding['shares'] * new_price
            cost = holding['shares'] * holding['avg_cost_hkd']
            pnl = value - cost
            pnl_pct = (pnl / cost) * 100 if cost != 0 else 0
            
            holding['value_hkd'] = value
            holding['pnl_hkd'] = pnl
            holding['pnl_percent'] = pnl_pct
            
            # 更新状态
            if pnl_pct >= 5:
                holding['status'] = "盈利"
            elif pnl_pct >= 0:
                holding['status'] = "持平"
            elif pnl_pct >= -5:
                holding['status'] = "小亏"
            else:
                holding['status'] = "亏损"
            
            updated_count += 1
            print(f"  ✅ {symbol}: ${old_price:.2f} → ${new_price:.2f} ({pnl_pct:+.1f}%)")
    
    return updated_count

def sync_prices():
    """主函数：同步价格"""
    print(f"[{datetime.now()}] 开始同步持仓价格...")
    
    # 连接 OpenD
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    # 验证连接
    ret, state = quote_ctx.get_global_state()
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！")
        return False
    
    print("✅ OpenD 连接成功")
    
    # 加载配置
    portfolio = load_portfolio()
    print(f"📊 加载配置：{len(portfolio['accounts']['us_stocks']['holdings'])} 只美股 + {len(portfolio['accounts']['hk_stocks']['holdings'])} 只港股")
    
    # 获取股票代码
    us_symbols = [h['symbol'] for h in portfolio['accounts']['us_stocks']['holdings']]
    hk_symbols = [h['symbol'].replace('.HK', '') for h in portfolio['accounts']['hk_stocks']['holdings']]
    
    print("\n🇺🇸 获取美股价格...")
    us_prices = get_realtime_prices(quote_ctx, us_symbols, 'US')
    
    print("\n🇭🇰 获取港股价格...")
    hk_prices = get_realtime_prices(quote_ctx, hk_symbols, 'HK')
    
    # 合并价格
    all_prices = {**us_prices, **hk_prices}
    print(f"\n✅ 获取到 {len(all_prices)} 只股票价格")
    
    # 更新配置
    print("\n📝 更新配置文件...")
    updated_count = update_portfolio(all_prices, portfolio)
    
    # 更新最后更新时间
    portfolio['last_updated'] = datetime.now().strftime('%Y-%m-%d')
    
    # 保存配置
    print("\n💾 保存配置...")
    save_portfolio(portfolio)
    
    quote_ctx.close()
    
    print(f"\n✅ 同步完成！更新 {updated_count} 只股票价格")
    return True

if __name__ == "__main__":
    success = sync_prices()
    exit(0 if success else 1)
