#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全球市场概览
- 港股：富途 OpenD (主) + Tushare (备份)
- 美股：Finnhub API
- A 股：Tushare (默认)
"""

import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

print('='*80)
print('🌍 全球市场概览')
print('='*80)
print(f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print()

# ============ 港股 ============
print('【🇭🇰 港股市场】')
print('-'*80)
print('数据源：富途 OpenD (主) + Tushare (备份)')
print()

hk_data_success = False

# 主数据源：富途 OpenD
try:
    from futu import *
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    # 获取热门港股
    hot_hk = ['HK.00700', 'HK.09988', 'HK.00883', 'HK.02338', 'HK.00939']
    ret, data = quote_ctx.get_market_snapshot(hot_hk)
    
    if ret == RET_OK and not data.empty:
        print(f'热门港股 (富途实时):')
        print(f'{"代码":<12} {"名称":<15} {"价格":>10} {"涨跌%":>10} {"PE":>8}')
        print('-'*60)
        
        for _, row in data.iterrows():
            code = row['code'].replace('HK.', '')
            name = row['name'][:13]
            price = row['last_price']
            change = row.get('change_rate', 0) * 100 if pd.notna(row.get('change_rate', 0)) else 0
            pe = row.get('pe_ratio', 'N/A')
            
            pe_str = f'{pe:.1f}' if isinstance(pe, (int, float)) else 'N/A'
            print(f'{code:<12} {name:<15} ${price:>9.2f} {change:>9.2f}% {pe_str:>8}')
        
        hk_data_success = True
    
    quote_ctx.close()

except Exception as e:
    print(f'富途 OpenD 获取失败，切换到 Tushare 备份：{e}')

# 备份数据源：Tushare
if not hk_data_success:
    print('\n切换到 Tushare 备份数据源...\n')
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from tushare_data_api import get_hk_daily
        
        hot_hk_codes = ['00700.HK', '09988.HK', '00883.HK', '02338.HK', '00939.HK']
        print(f'热门港股 (Tushare 备份):')
        print(f'{"代码":<12} {"名称":<15} {"收盘":>10} {"日期":>12}')
        print('-'*60)
        
        for code in hot_hk_codes:
            df = get_hk_daily(code)
            if df is not None:
                latest = df.iloc[0]
                name = code  # Tushare 港股需要另外获取名称
                print(f'{code:<12} {name:<15} ${latest["close"]:>9.2f} {latest["trade_date"]:>12}')
            else:
                print(f'{code:<12} {"N/A":<15} {"N/A":>10} {"N/A":>12}')
    
    except Exception as e:
        print(f'Tushare 备份数据获取失败：{e}')

print()

# ============ 美股 ============
print('【🇺🇸 美股市场】')
print('-'*80)

try:
    # 获取主要指数
    indices = {
        '^GSPC': '标普 500',
        '^DJI': '道琼斯',
        '^IXIC': '纳斯达克'
    }
    
    FINNHUB_API_KEY = 'd6r9v6hr01qgdhqdor50d6r9v6hr01qgdhqdor5g'
    
    # 获取热门美股
    hot_us = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']
    url = 'https://finnhub.io/api/v1/quote'
    
    print(f'{"代码":<12} {"名称":<15} {"价格":>10} {"涨跌%":>10} {"PE":>8}')
    print('-'*60)
    
    names = {
        'AAPL': '苹果', 'MSFT': '微软', 'GOOGL': '谷歌',
        'AMZN': '亚马逊', 'NVDA': '英伟达', 'META': '元',
        'TSLA': '特斯拉'
    }
    
    for symbol in hot_us:
        params = {'symbol': symbol, 'token': FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if response.status_code == 200 and data.get('c'):
            current = data['c']
            change = data['d']
            change_pct = (change / data['pc'] * 100) if data['pc'] > 0 else 0
            
            print(f'{symbol:<12} {names.get(symbol, ""):<15} ${current:>9.2f} {change_pct:>9.2f}% {"N/A":>8}')

except Exception as e:
    print(f'美股数据获取失败：{e}')

print()

# ============ A 股 ============
print('【🇨🇳 A 股市场】')
print('-'*80)
print('数据源：Tushare 付费版 (默认)')
print()

try:
    # 导入 Tushare 接口
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from tushare_data_api import get_cn_index
    
    # 获取主要指数
    indices = [
        ('000001.SH', '上证指数'),
        ('399001.SZ', '深证成指'),
        ('399006.SZ', '创业板指')
    ]
    
    print(f'{"代码":<12} {"名称":<15} {"收盘":>10} {"涨跌%":>10}')
    print('-'*60)
    
    for ts_code, name in indices:
        data = get_cn_index(ts_code)
        
        if data:
            print(f'{ts_code.split(".")[0]:<12} {name:<15} {data["close"]:>10.2f} {data["change_pct"]:>9.2f}%')
        else:
            print(f'{ts_code.split(".")[0]:<12} {name:<15} {"N/A":>10} {"N/A":>10}')

except Exception as e:
    print(f'A 股数据获取失败：{e}')

print()

# ============ 商品 ============
print('【🛢️ 大宗商品】')
print('-'*80)

try:
    # 原油
    url = 'https://finnhub.io/api/v1/quote'
    params = {'symbol': 'USO', 'token': FINNHUB_API_KEY}
    response = requests.get(url, params=params, timeout=5)
    data = response.json()
    
    if response.status_code == 200 and data.get('c'):
        oil_price = data['c']
        oil_change = data['d'] / data['pc'] * 100 if data['pc'] > 0 else 0
        print(f'WTI 原油：${oil_price:.2f}/桶 ({oil_change:+.2f}%)')
    
    # 黄金
    params = {'symbol': 'GLD', 'token': FINNHUB_API_KEY}
    response = requests.get(url, params=params, timeout=5)
    data = response.json()
    
    if response.status_code == 200 and data.get('c'):
        gold_price = data['c']
        gold_change = data['d'] / data['pc'] * 100 if data['pc'] > 0 else 0
        print(f'黄金 ETF: ${gold_price:.2f} ({gold_change:+.2f}%)')

except Exception as e:
    print(f'商品数据获取失败：{e}')

print()

# ============ 加密货币 ============
print('【₿ 加密货币】')
print('-'*80)

try:
    url = 'https://api.coingecko.com/api/v3/simple/price'
    params = {
        'ids': 'bitcoin,ethereum',
        'vs_currencies': 'usd',
        'include_24hr_change': 'true'
    }
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    if 'bitcoin' in data:
        btc_price = data['bitcoin']['usd']
        btc_change = data['bitcoin']['usd_24h_change']
        print(f'比特币：${btc_price:,.0f} ({btc_change:+.2f}%)')
    
    if 'ethereum' in data:
        eth_price = data['ethereum']['usd']
        eth_change = data['ethereum']['usd_24h_change']
        print(f'以太坊：${eth_price:,.0f} ({eth_change:+.2f}%)')

except Exception as e:
    print(f'加密货币数据获取失败：{e}')

print()
print('='*80)
print('✅ 全球市场概览完成')
print('='*80)
