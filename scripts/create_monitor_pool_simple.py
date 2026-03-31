#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建行业监控池 - 每个行业 Top 2
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

# 读取选股结果
df = pd.read_csv('reports/stock_selection_HK_20260330_enhanced.csv')

# 手动行业分类（根据股票名称和代码）
industry_map = {
    # 银行
    '00966': '保险', '02628': '保险', '01336': '保险', '06818': '银行',
    '02601': '保险', '01963': '银行', '01339': '保险', '01988': '银行',
    '02016': '银行', '03866': '银行', '00998': '银行', '03618': '银行',
    '00939': '银行', '01398': '银行', '03328': '银行', '01658': '银行',
    '03988': '银行', '01288': '银行', '00142': '综合', '00267': '综合',
    # 基建/建筑
    '01800': '基建', '01186': '基建', '00390': '基建', '03311': '建筑',
    '01114': '汽车', '01811': '能源', '00579': '能源',
    # 房地产
    '00373': '房地产', '00258': '房地产', '09890': '消费',
    # 其他
    '02598': '科技', '03698': '银行', '02510': '运输',
    '01478': '科技', '00363': '综合', '02678': '纺织',
    '00013': '医药', '02666': '医药', '00116': '消费',
    '00819': '能源', '02283': '纺织', '02219': '医药',
    '03933': '医药', '00546': '消费', '02580': '工业',
    '06806': '消费', '00836': '能源', '00293': '运输',
    '9961': '消费', '00392': '综合', '01919': '运输',
}

# 添加行业列
df['industry'] = df['code'].apply(lambda x: industry_map.get(x.replace('HK.', ''), '其他'))

# 按行业分组，每个行业选 Top 2 (按 PE 排序)
monitor_pool = []

for industry in df['industry'].unique():
    industry_df = df[df['industry'] == industry]
    # 按 PE 排序选前 2
    top2 = industry_df.sort_values('pe_ratio').head(2)
    
    for idx, row in top2.iterrows():
        monitor_pool.append({
            'code': row['code'].replace('HK.', ''),
            'name': row['name'],
            'industry': industry,
            'price': row['last_price'],
            'pe': row['pe_ratio'],
            'pb': row['pb_ratio'],
        })

# 转换为 DataFrame
monitor_df = pd.DataFrame(monitor_pool)

print('='*80)
print('📊 行业监控池 - 每个行业 Top 2')
print('='*80)
print(f'监控股票：{len(monitor_df)} 只')
industry_count = len(monitor_df['industry'].unique())
print(f'覆盖行业：{industry_count} 个')
print()

# 按行业显示
for industry in sorted(monitor_df['industry'].unique()):
    stocks = monitor_df[monitor_df['industry'] == industry]
    print(f'\n【{industry}】({len(stocks)}只)')
    for idx, row in stocks.iterrows():
        print(f"  {row['code']:<10} {row['name']:<20} ${row['price']:>7.2f}  PE:{row['pe']:>5.1f}")

# 保存
output_file = Path('reports/monitor_pool_HK_' + datetime.now().strftime('%Y%m%d_%H%M') + '.csv')
monitor_df.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f'\n✅ 已保存：{output_file}')
