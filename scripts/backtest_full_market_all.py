#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股全市场回测 (5494 只)
使用优化后的选股策略
"""

import pandas as pd
import tushare as ts
from datetime import datetime, timedelta
from pathlib import Path
import time

# Tushare 配置
TUSHARE_TOKEN = '1dbdfba7c672d47f22db86f586d5aff9730124b321c2ebdda91890d3'
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

print('='*80)
print('📊 A 股全市场回测 (5494 只)')
print('='*80)
print()

# 获取 A 股列表
print('【获取股票列表】')
df_basic = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,list_date')
print(f'总股票数：{len(df_basic)}')

# 筛选上市>8 年的股票 (2018 年前上市)
cutoff_date = '20180101'
df_basic['list_date'] = pd.to_datetime(df_basic['list_date'], format='%Y%m%d')
df_basic = df_basic[df_basic['list_date'] < pd.to_datetime(cutoff_date)]
print(f'上市>8 年：{len(df_basic)}只')
print()

# 分批回测
print('【全市场回测】')
print('周期：8 年 (2018-2026)')
print()

results = []
batch_size = 500
total_batches = (len(df_basic) + batch_size - 1) // batch_size

for batch_idx in range(total_batches):
    start_idx = batch_idx * batch_size
    end_idx = min((batch_idx + 1) * batch_size, len(df_basic))
    batch_df = df_basic.iloc[start_idx:end_idx]
    
    batch_results = []
    
    for idx, (_, row) in enumerate(batch_df.iterrows(), 1):
        ts_code = row['ts_code']
        
        try:
            # 获取历史数据
            df = pro.daily(ts_code=ts_code, start_date='20180101', end_date='20260330')
            
            if df.empty or len(df) < 100:
                continue
            
            # 计算收益
            df = df.sort_values('trade_date')
            start_price = df.iloc[0]['close']
            end_price = df.iloc[-1]['close']
            total_return = (end_price - start_price) / start_price * 100
            
            batch_results.append({
                'ts_code': ts_code,
                'name': row['name'],
                'industry': row['industry'],
                'total_return': total_return,
            })
        
        except:
            continue
    
    results.extend(batch_results)
    
    # 进度显示
    print(f'  进度：{end_idx}/{len(df_basic)} (已找到 {len(results)}只)')
    time.sleep(0.5)

# 保存结果
if results:
    result_df = pd.DataFrame(results)
    
    print(f'\n【回测结果】')
    print(f'有效股票：{len(result_df)}')
    print(f'平均收益：{result_df["total_return"].mean():+.1f}%')
    print(f'最佳股票：{result_df.loc[result_df["total_return"].idxmax()]["name"]} ({result_df["total_return"].max():+.1f}%)')
    
    # 统计分布
    high_performers = len(result_df[result_df['total_return'] > 200])
    mid_performers = len(result_df[(result_df['total_return'] > 50) & (result_df['total_return'] <= 200)])
    low_performers = len(result_df[result_df['total_return'] <= 50])
    
    print(f'\n收益分布:')
    print(f'  >200%: {high_performers}只 ({high_performers/len(result_df)*100:.1f}%)')
    print(f'  50-200%: {mid_performers}只 ({mid_performers/len(result_df)*100:.1f}%)')
    print(f'  <50%: {low_performers}只 ({low_performers/len(result_df)*100:.1f}%)')
    
    # 保存结果
    output_file = Path('reports/backtest_full_market_all_20260330.csv')
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f'\n✅ 结果已保存：{output_file}')

print('\n✅ 全市场回测完成')
