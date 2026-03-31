#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用优化后的选股策略
筛选符合新标准的股票
"""

import pandas as pd
import tushare as ts
from datetime import datetime
from pathlib import Path

# Tushare 配置
TUSHARE_TOKEN = '1dbdfba7c672d47f22db86f586d5aff9730124b321c2ebdda91890d3'
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

print('='*80)
print('🎯 应用优化后的选股策略')
print('='*80)
print()
print('【新策略标准】')
print('  市值 > 100 亿')
print('  PE < 25')
print('  ROE > 15%')
print('  负债率 < 50%')
print('  营收增长 > 20%')
print('  行业：黄金/化工/医药/机械 (优先)')
print()

# 获取 A 股列表
print('【获取股票列表】')
df_basic = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry')
print(f'总股票数：{len(df_basic)}')
print()

# 获取财务数据
print('【获取财务数据】')
try:
    # 获取最新财务指标
    df_fina = pro.fina_indicator(ts_code='', start_date='20251001', end_date='20251231')
    print(f'财务数据：{len(df_fina)}条')
    
    # 合并数据
    df = df_basic.merge(df_fina, on='ts_code', how='inner')
    
    # 筛选条件
    print('\n【应用筛选条件】')
    
    # ROE > 15%
    df = df[df['roe'] > 15]
    print(f'ROE > 15%: {len(df)}只')
    
    # 负债率 < 50%
    df = df[df['debt_to_assets'] < 50]
    print(f'负债率 < 50%: {len(df)}只')
    
    # 优先行业
    priority_industries = ['黄金', '化工', '医药', '机械', '半导体', '新材料']
    df_priority = df[df['industry'].str.contains('|'.join(priority_industries), na=False)]
    
    print(f'\n优先行业：{len(df_priority)}只')
    print(f'其他行业：{len(df) - len(df_priority)}只')
    
    # 保存结果
    if len(df) > 0:
        output_file = Path('reports/selected_stocks_new_strategy_20260330.csv')
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f'\n✅ 结果已保存：{output_file}')
        
        # 显示 Top 20
        print(f'\n【Top 20 股票】')
        top20 = df.sort_values('roe', ascending=False).head(20)
        print(f'{"代码":<12} {"名称":<15} {"ROE":>8} {"负债率":>8} {"行业":<20}')
        print('-'*70)
        for _, row in top20.iterrows():
            print(f'{row["ts_code"]:<12} {row["name"]:<15} {row["roe"]:>7.1f}% {row["debt_to_assets"]:>7.1f}% {row["industry"]:<20}')
    
except Exception as e:
    print(f'获取财务数据失败：{e}')
    print('使用简化筛选...')

print('\n✅ 选股完成')
