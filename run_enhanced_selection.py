#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版港股选股 - 巴菲特财务指标
筛选标准:
1. 市值 > 50 亿港元
2. PE < 30
3. PB > 0
4. 价格 2-500 港元
5. 成交量 > 50 万股
6. ROE > 8%
7. 资产负债率 < 60%
"""

from futu import *
import pandas as pd
import time
from pathlib import Path

print('='*80)
print('📊 增强版港股选股 - 巴菲特财务指标')
print('='*80)
print()

# 连接 OpenD
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
time.sleep(1)
print('✅ OpenD 连接成功\n')

# 获取股票列表
print('获取港股列表...')
ret, stock_list = quote_ctx.get_stock_basicinfo(Market.HK, SecurityType.STOCK)
if ret != RET_OK:
    print('❌ 获取失败')
    exit(1)
print(f'✅ 共 {len(stock_list)} 只港股\n')

# 获取行情 (单只测试)
print('获取行情数据 (测试前 500 只)...')
test_codes = stock_list['code'].tolist()[:500]

all_data = []
for i, code in enumerate(test_codes, 1):
    ret, data = quote_ctx.get_market_snapshot(code)
    if ret == RET_OK and not data.empty:
        all_data.append(data)
    if i % 100 == 0:
        print(f'  进度：{i}/500')
    time.sleep(0.1)

if not all_data:
    print('❌ 获取行情失败')
    exit(1)

snapshot = pd.concat(all_data, ignore_index=True)
print(f'✅ 获取到 {len(snapshot)} 只股票行情\n')

# 筛选
print('='*80)
print('【筛选过程】')
print('='*80)

filtered = snapshot.copy()

# 市值 > 50 亿港元
if 'total_market_val' in filtered.columns:
    before = len(filtered)
    filtered = filtered[filtered['total_market_val'] >= 50 * 1e8]
    print(f'市值 > 50 亿港元：{before} → {len(filtered)}')

# PE < 30 且 > 0
if 'pe_ratio' in filtered.columns:
    before = len(filtered)
    filtered = filtered[(filtered['pe_ratio'] > 0) & (filtered['pe_ratio'] <= 30)]
    print(f'PE < 30: {before} → {len(filtered)}')

# PB > 0
if 'pb_ratio' in filtered.columns:
    before = len(filtered)
    filtered = filtered[filtered['pb_ratio'] > 0]
    print(f'PB > 0: {before} → {len(filtered)}')

# 价格 2-500
if 'last_price' in filtered.columns:
    before = len(filtered)
    filtered = filtered[(filtered['last_price'] >= 2) & (filtered['last_price'] <= 500)]
    print(f'价格 2-500 港元：{before} → {len(filtered)}')

# 成交量 > 50 万
if 'volume' in filtered.columns:
    before = len(filtered)
    filtered = filtered[filtered['volume'] >= 500000]
    print(f'成交量 > 50 万股：{before} → {len(filtered)}')

print(f'\n✅ 初步筛选：{len(filtered)} 只股票\n')

# 获取财务数据
print('='*80)
print('【财务筛选】(测试前 50 只)')
print('='*80)

test_codes = filtered['code'].tolist()[:50]
financial_stocks = []

for code in test_codes:
    ret, data = quote_ctx.get_financial_metrics(code)
    if ret == RET_OK and not data.empty:
        latest = data.iloc[0]
        roe = latest.get('roewa', None)
        debt = latest.get('gross_debt_ratio', None)
        
        # 筛选：ROE>8% 且 负债率<60%
        if roe and roe > 8 and debt and debt < 60:
            financial_stocks.append({
                'code': code,
                'roe': roe,
                'debt_ratio': debt,
            })
            print(f"  ✅ {code}: ROE={roe:.1f}%, 负债率={debt:.1f}%")
    
    time.sleep(0.3)

print(f'\n✅ 符合财务标准：{len(financial_stocks)} 只股票\n')

# 合并结果
if financial_stocks:
    fin_df = pd.DataFrame(financial_stocks)
    result = filtered.merge(fin_df, on='code', how='inner')
else:
    result = filtered
    print('⚠️ 无符合财务标准的股票，显示初步筛选结果')

# 保存
output_file = Path('reports/stock_selection_HK_20260330_enhanced.csv')
result.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f'✅ 保存到：{output_file}\n')

# 显示结果
if not result.empty:
    print('='*80)
    print('【最终结果 Top 20】')
    print('='*80)
    print(f'{"排名":<4} {"代码":<10} {"名称":<15} {"价格":>8} {"PE":>6} {"PB":>6} {"ROE":>8} {"负债率":>10}')
    print('-'*80)
    
    top20 = result.head(20)
    for idx, (_, row) in enumerate(top20.iterrows(), 1):
        code = row['code'].replace('HK.', '')
        name = row['name'][:13]
        price = row['last_price']
        pe = row['pe_ratio']
        pb = row['pb_ratio']
        roe = row.get('roe', None)
        debt = row.get('debt_ratio', None)
        
        roe_str = f"{roe:.1f}%" if roe else 'N/A'
        debt_str = f"{debt:.1f}%" if debt else 'N/A'
        
        print(f"{idx:<4} {code:<10} {name:<15} ${price:>7.2f} {pe:>6.1f} {pb:>6.2f} {roe_str:>8} {debt_str:>10}")

print('\n' + '='*80)
print('✅ 选股完成')
print('='*80)

quote_ctx.close()
