#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 TwelveData 和 Finnhub 获取美股实时行情
"""

import requests
import json
from datetime import datetime

# API Keys
TWELVEDATA_API_KEY = '4e1f016330ba4aa5a5eef694a8564bc0'
FINNHUB_API_KEY = 'd6r9v6hr01qgdhqdor50d6r9v6hr01qgdhqdor5g'

# 热门美股列表
stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'JPM', 'V']

print('='*80)
print('🇺🇸 美股实时行情')
print('='*80)
print()

# ============ TwelveData ============
print('【TwelveData 数据】')
print('-'*80)

try:
    # 获取实时价格
    url = 'https://api.twelvedata.com/price'
    params = {'symbol': ','.join(stocks), 'apikey': TWELVEDATA_API_KEY}
    
    response = requests.get(url, params=params, timeout=10)
    data = response.json()
    
    if response.status_code == 200:
        print(f'{"代码":<12} {"价格 (USD)":>12} {"时间":>20}')
        print('-'*80)
        
        for symbol, price in data.items():
            if isinstance(price, (int, float)):
                print(f'{symbol:<12} ${price:>11.2f} {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    else:
        print(f'获取失败：{data}')

except Exception as e:
    print(f'TwelveData 请求失败：{e}')

print()

# ============ Finnhub ============
print('【Finnhub 数据】')
print('-'*80)

try:
    # 获取实时报价
    url = 'https://finnhub.io/api/v1/quote'
    
    print(f'{"代码":<12} {"现价":>10} {"涨跌%":>10} {"开盘":>10} {"最高":>10} {"最低":>10} {"昨收":>10}')
    print('-'*80)
    
    for symbol in stocks:
        params = {'symbol': symbol, 'token': FINNHUB_API_KEY}
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if response.status_code == 200 and data.get('c'):  # c = current price
            current = data['c']
            change = data['d']
            change_pct = (change / data['pc'] * 100) if data['pc'] > 0 else 0
            open_p = data['o']
            high = data['h']
            low = data['l']
            prev_close = data['pc']
            
            change_str = f'{change_pct:+.2f}%'
            print(f'{symbol:<12} ${current:>9.2f} {change_str:>9} ${open_p:>9.2f} ${high:>9.2f} ${low:>9.2f} ${prev_close:>9.2f}')
        else:
            print(f'{symbol:<12} 获取失败')

except Exception as e:
    print(f'Finnhub 请求失败：{e}')

print()
print('='*80)
print('✅ 数据获取完成')
print('='*80)
