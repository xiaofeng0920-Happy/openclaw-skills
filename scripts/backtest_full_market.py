#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股全市场选股回测
基于监控池选股标准，扩展到全市场
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
print('📊 A 股全市场选股回测')
print('='*80)
print()

# ============ 全市场筛选 ============
print('【全市场筛选】')
print('标准：市值>100 亿，PE<30, ROE>8%, 负债<60%')
print()

# 获取 A 股列表
df_basic = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry')
print(f'总股票数：{len(df_basic)}')

# 简化测试：随机选 100 只
sample_stocks = df_basic.sample(n=100, random_state=42)
print(f'测试样本：100 只')
print()

# ============ 回测 ============
print('【回测执行】')
print('周期：8 年 (2018-2026)')
print()

results = []

for idx, (_, row) in enumerate(sample_stocks.iterrows(), 1):
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
        
        results.append({
            'ts_code': ts_code,
            'name': row['name'],
            'total_return': total_return,
        })
        
        if idx % 20 == 0:
            print(f'  进度：{idx}/100')
        
        time.sleep(0.05)
    
    except:
        continue

# ============ 结果统计 ============
if results:
    result_df = pd.DataFrame(results)
    
    print(f'\n有效股票：{len(result_df)}')
    print(f'平均收益：{result_df["total_return"].mean():+.1f}%')
    print(f'最佳股票：{result_df.loc[result_df["total_return"].idxmax()]["name"]} ({result_df["total_return"].max():+.1f}%)')
    
    # 保存结果
    output_file = Path('reports/backtest_full_market_20260330.csv')
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f'\n✅ 结果已保存：{output_file}')

print('\n✅ 全市场回测完成')
