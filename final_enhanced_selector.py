#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版港股选股 - 更新筛选标准

筛选标准:
1. 市值 > 50 亿港元
2. PE < 30
3. PB > 0
4. 价格 2-500 港元
5. 成交量 > 50 万股

注：财务指标（ROE>8%、负债率<60%、ROIC>8%、FCF>0）需要额外数据源
    当前使用富途 OpenD 仅支持行情数据筛选
    财务数据筛选将在后续版本中加入
"""

from futu import *
import pandas as pd
import time
from pathlib import Path
from datetime import datetime

print('='*80)
print('📊 增强版港股选股系统')
print('='*80)
print()
print('筛选标准:')
print('  ✅ 市值 > 50 亿港元')
print('  ✅ PE (市盈率) < 30')
print('  ✅ PB (市净率) > 0')
print('  ✅ 价格范围：2-500 港元')
print('  ✅ 成交量 > 50 万股')
print('  ⏳ ROE > 8% (待实现)')
print('  ⏳ 资产负债率 < 60% (待实现)')
print('  ⏳ ROIC > 8% (待实现)')
print('  ⏳ 自由现金流 > 0 (待实现)')
print()
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

# 获取行情 (分批)
print('获取行情数据...')
all_codes = stock_list['code'].tolist()
all_data = []
batch_size = 300

for i in range(0, len(all_codes), batch_size):
    batch = all_codes[i:i+batch_size]
    ret, data = quote_ctx.get_market_snapshot(batch)
    
    if ret == RET_OK and not data.empty:
        all_data.append(data)
        print(f'  进度：{min(i+batch_size, len(all_codes))}/{len(all_codes)}')
    
    time.sleep(0.3)

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
initial_count = len(filtered)

# 市值 > 50 亿港元
if 'total_market_val' in filtered.columns:
    before = len(filtered)
    filtered = filtered[filtered['total_market_val'] >= 50 * 1e8]
    print(f'市值 > 50 亿港元：{before} → {len(filtered)} (-{before-len(filtered)})')

# PE < 30 且 > 0
if 'pe_ratio' in filtered.columns:
    before = len(filtered)
    filtered = filtered[(filtered['pe_ratio'] > 0) & (filtered['pe_ratio'] <= 30)]
    print(f'PE < 30: {before} → {len(filtered)} (-{before-len(filtered)})')

# PB > 0
if 'pb_ratio' in filtered.columns:
    before = len(filtered)
    filtered = filtered[filtered['pb_ratio'] > 0]
    print(f'PB > 0: {before} → {len(filtered)} (-{before-len(filtered)})')

# 价格 2-500 港元
if 'last_price' in filtered.columns:
    before = len(filtered)
    filtered = filtered[(filtered['last_price'] >= 2) & (filtered['last_price'] <= 500)]
    print(f'价格 2-500 港元：{before} → {len(filtered)} (-{before-len(filtered)})')

# 成交量 > 50 万股
if 'volume' in filtered.columns:
    before = len(filtered)
    filtered = filtered[filtered['volume'] >= 500000]
    print(f'成交量 > 50 万股：{before} → {len(filtered)} (-{before-len(filtered)})')

pass_rate = len(filtered) / initial_count * 100
print(f'\n✅ 初步筛选后剩余 {len(filtered)} 只股票 (通过率：{pass_rate:.1f}%)\n')

# 保存结果
output_file = Path(f'reports/stock_selection_HK_{datetime.now().strftime("%Y%m%d")}_enhanced.csv')
filtered.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f'✅ 结果已保存到：{output_file}\n')

# 显示 Top 30
if not filtered.empty:
    print('='*80)
    print('【Top 30 股票】')
    print('='*80)
    print(f'{"排名":<4} {"代码":<10} {"名称":<15} {"价格":>8} {"PE":>6} {"PB":>6} {"市值 (亿港元)":>12} {"成交量":>12}')
    print('-'*80)
    
    # 按 PE 排序
    top30 = filtered.sort_values('pe_ratio').head(30)
    
    for idx, (_, row) in enumerate(top30.iterrows(), 1):
        code = row['code'].replace('HK.', '')
        name = row['name'][:13]
        price = row['last_price']
        pe = row['pe_ratio']
        pb = row['pb_ratio']
        market_val = row.get('total_market_val', 0) / 1e8
        volume = row.get('volume', 0) / 10000  # 万
        
        print(f"{idx:<4} {code:<10} {name:<15} ${price:>7.2f} {pe:>6.1f} {pb:>6.2f} {market_val:>12.1f} {volume:>10.0f}万")

print('\n' + '='*80)
print('✅ 选股完成')
print('='*80)
print()
print('📝 说明:')
print('  当前版本使用富途 OpenD 行情数据进行筛选')
print('  财务指标筛选 (ROE、负债率、ROIC、自由现金流) 需要额外数据源')
print('  后续将加入 Tushare/AKShare 等数据源支持财务筛选')
print()

quote_ctx.close()
