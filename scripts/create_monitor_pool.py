#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从选股结果中按行业分类，每个行业选 Top 2 形成监控池
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# 读取选股结果
csv_file = Path('reports/stock_selection_HK_20260330_enhanced.csv')
df = pd.read_csv(csv_file)

print('='*80)
print('📊 港股选股 - 行业分类监控池')
print('='*80)
print(f'原始数据：{len(df)} 只股票')
print()

# 获取行业信息（从富途）
print('获取行业信息...')
from futu import *
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

# 添加行业列
df['industry'] = ''

for idx, row in df.iterrows():
    code = row['code']
    try:
        # 获取股票资料
        ret, data = quote_ctx.get_stock_basicinfo(Market.HK, SecurityType.STOCK)
        if ret == RET_OK and not data.empty:
            stock_info = data[data['code'] == code]
            if not stock_info.empty:
                industry = stock_info.iloc[0].get('industry', '')
                df.at[idx, 'industry'] = industry
    except:
        pass
    
    if (idx + 1) % 50 == 0:
        print(f'  进度：{idx+1}/{len(df)}')

quote_ctx.close()

# 按行业分组
print('\n按行业分类...')
industry_groups = df.groupby('industry')

print(f'共 {len(industry_groups)} 个行业\n')

# 每个行业选 Top 2
monitor_pool = []

for industry, group in industry_groups:
    if pd.isna(industry) or industry == '':
        continue
    
    # 按综合评分排序
    group_sorted = group.sort_values('total_score', ascending=False)
    
    # 选 Top 2
    top2 = group_sorted.head(2)
    
    for idx, row in top2.iterrows():
        monitor_pool.append({
            'code': row['code'],
            'name': row['name'],
            'industry': industry,
            'price': row['last_price'],
            'pe': row['pe_ratio'],
            'pb': row['pb_ratio'],
            'score': row['total_score'],
        })

# 转换为 DataFrame
monitor_df = pd.DataFrame(monitor_pool)

print('='*80)
print('【行业监控池】')
print('='*80)
print(f'监控股票数：{len(monitor_df)} 只')
print(f'覆盖行业数：{len(monitor_df["industry"].unique())} 个')
print()

# 按行业显示
for industry in sorted(monitor_df['industry'].unique()):
    industry_stocks = monitor_df[monitor_df['industry'] == industry]
    print(f'\n【{industry}】')
    for idx, row in industry_stocks.iterrows():
        code = row['code'].replace('HK.', '')
        print(f"  {code:<10} {row['name']:<20} ${row['price']:>7.2f}  PE:{row['pe']:>5.1f}  评分:{row['score']:.1f}")

# 保存结果
output_file = Path('reports/monitor_pool_HK_' + datetime.now().strftime('%Y%m%d_%H%M') + '.csv')
monitor_df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f'\n✅ 监控池已保存：{output_file}')

print('\n' + '='*80)
print('✅ 行业分类完成')
print('='*80)
