#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""展示初选股票列表"""

import pandas as pd

# 读取选股结果
df = pd.read_csv('reports/stock_selection_HK_20260330.csv')

print('='*80)
print('📊 港股量化选股 - 初选条件详解')
print('='*80)
print()

# 筛选条件
print('【初选筛选条件】')
print('-'*80)
filters = {
    '市值': '> 50 亿港元',
    'PE (市盈率)': '< 30',
    'PB (市净率)': '> 0',
    '价格范围': '2-500 港元',
    '成交量': '> 50 万股',
}

for condition, value in filters.items():
    print(f'  {condition:15s}: {value}')

print()
print('-'*80)
print(f'✅ 符合初选条件的股票数量：{len(df)} 只')
print(f'📊 从 3623 只港股中筛选')
print(f'📈 筛选通过率：{len(df)/3623*100:.1f}%')
print()

# 统计分析
print('【统计数据】')
print('-'*80)
print(f'  PE 范围：{df["pe_ratio"].min():.2f} - {df["pe_ratio"].max():.2f} (平均：{df["pe_ratio"].mean():.2f})')
print(f'  PB 范围：{df["pb_ratio"].min():.2f} - {df["pb_ratio"].max():.2f} (平均：{df["pb_ratio"].mean():.2f})')
print(f'  价格范围：HK${df["last_price"].min():.2f} - HK${df["last_price"].max():.2f}')
print(f'  成交量范围：{df["volume"].min():,.0f} - {df["volume"].max():,.0f}')
print()

# 展示前 50 只
print('【Top 50 完整列表】')
print('-'*80)
print(f'{"排名":<4} {"代码":<12} {"名称":<20} {"价格":>8} {"PE":>6} {"PB":>6} {"成交量":>12} {"评分":>6}')
print('-'*80)

for idx, row in df.head(50).iterrows():
    code = row['code'].replace('HK.', '')
    name = row['name'][:18]
    price = row['last_price']
    pe = row['pe_ratio']
    pb = row['pb_ratio']
    volume = f"{row['volume']:,.0f}"
    score = row['total_score']
    print(f'{idx+1:<4} {code:<12} {name:<20} ${price:>7.2f} {pe:>6.2f} {pb:>6.2f} {volume:>12} {score:>6.2f}')

print()
print('-'*80)
print(f'共展示前 50 只，完整 {len(df)} 只股票数据已保存到 CSV 文件')
print()
print('【文件位置】')
print(f'  reports/stock_selection_HK_20260330.csv ({len(df)} 只股票)')
