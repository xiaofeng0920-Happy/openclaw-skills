#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""获取美股实时行情"""

from futu import *
import pandas as pd

# 连接 OpenD
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

# 获取热门美股行情
popular_codes = [
    'US.AAPL', 'US.MSFT', 'US.GOOGL', 'US.AMZN', 'US.NVDA',
    'US.META', 'US.TSLA', 'US.BRK.B', 'US.JPM', 'US.V'
]

print('='*80)
print('【热门美股实时行情】')
print('='*80)

ret, data = quote_ctx.get_market_snapshot(popular_codes)

if ret == RET_OK and not data.empty:
    print(f'{"代码":<12} {"名称":<20} {"价格 (USD)":>12} {"涨跌幅":>10} {"PE":>8} {"市值 (亿美元)":>14}')
    print('-'*80)
    
    for idx, row in data.iterrows():
        code = row['code'].replace('US.', '')
        name = row['name'][:18]
        price = row['last_price']
        change_rate = row.get('change_rate', 0)
        change_pct = change_rate * 100 if pd.notna(change_rate) else 0
        pe = row.get('pe_ratio', None)
        market_val = row.get('total_market_val', 0) / 1e9
        
        pe_str = f'{pe:.1f}' if isinstance(pe, (int, float)) else 'N/A'
        change_str = f'{change_pct:+.2f}%'
        
        print(f'{code:<12} {name:<20} ${price:>11.2f} {change_str:>10} {pe_str:>8} {market_val:>12.1f}')
    
    print('='*80)
else:
    print(f'获取失败：{data}')

quote_ctx.close()
