#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股全市场选股 - 生成监控池 (简化版)
筛选标准:
1. 市值 > 100 亿人民币
2. PE < 30
3. 近 5 年 ROE > 8%
4. 资产负债率 < 60%
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
print('📊 A 股全市场选股 - 生成监控池 (简化版)')
print('='*80)
print()
print('【筛选标准】')
print('  ✅ 市值 > 100 亿人民币')
print('  ✅ PE < 30')
print('  ✅ 近 5 年 ROE > 8%')
print('  ✅ 资产负债率 < 60%')
print()

# ============ 获取 A 股股票列表 ============
print('获取 A 股股票列表...')
df_basic = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,list_date')
print(f'✅ 获取到 {len(df_basic)} 只 A 股')

# ============ 获取财务数据 ============
print('\n获取财务数据 (前 500 只测试)...')

qualified_stocks = []

# 只测试前 500 只，快速验证
test_stocks = df_basic.head(500)

for idx, row in test_stocks.iterrows():
    ts_code = row['ts_code']
    industry = row['industry']
    
    try:
        # 获取财务指标 (近 5 年)
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y%m%d')
        
        fina_df = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if fina_df.empty or len(fina_df) < 5:
            continue
        
        # 计算近 5 年平均 ROE 和负债率
        avg_roe = fina_df['roe'].mean() if 'roe' in fina_df.columns else 0
        avg_debt = fina_df['debt_to_assets'].mean() if 'debt_to_assets' in fina_df.columns else 100
        
        # 检查 ROE 和负债率
        if avg_roe < 8 or avg_debt > 60:
            continue
        
        # 获取估值数据
        stock_info = pro.daily_basic(ts_code=ts_code, start_date=end_date, end_date=end_date)
        
        if stock_info.empty:
            continue
        
        latest = stock_info.iloc[0]
        pe = latest.get('pe', None)
        total_mv = latest.get('total_mv', 0) / 10000  # 转换为亿
        
        # 检查 PE 和市值
        if pe is None or pe <= 0 or pe > 30:
            continue
        
        if total_mv < 100:
            continue
        
        # 符合条件
        qualified_stocks.append({
            'ts_code': ts_code,
            'name': row['name'],
            'industry': industry if industry else '其他',
            'pe': pe,
            'market_cap': total_mv,
            'avg_roe': avg_roe,
            'avg_debt_ratio': avg_debt,
        })
    
    except Exception as e:
        continue
    
    # 进度显示
    if (idx + 1) % 100 == 0:
        print(f'  进度：{idx+1}/{len(test_stocks)} (已找到 {len(qualified_stocks)} 只)')
        time.sleep(0.2)

print(f'\n✅ 初步筛选：{len(qualified_stocks)} 只股票符合标准')

# ============ 按行业分类 ============
if qualified_stocks:
    print('\n按行业分类，生成监控池...')
    
    qualified_df = pd.DataFrame(qualified_stocks)
    
    # 按行业分组
    industry_groups = qualified_df.groupby('industry')
    
    monitor_pool = []
    
    for industry, group in industry_groups:
        # 按 ROE 排序
        group_sorted = group.sort_values('avg_roe', ascending=False)
        
        # 选 Top 2
        top2 = group_sorted.head(2)
        
        for idx, row in top2.iterrows():
            monitor_pool.append({
                'ts_code': row['ts_code'],
                'name': row['name'],
                'industry': industry,
                'pe': row['pe'],
                'market_cap': row['market_cap'],
                'avg_roe': row['avg_roe'],
                'avg_debt_ratio': row['avg_debt_ratio'],
            })
    
    monitor_df = pd.DataFrame(monitor_pool)
    
    print(f'✅ 监控池股票：{len(monitor_df)} 只')
    print(f'✅ 覆盖行业：{len(monitor_df["industry"].unique())} 个')
    
    # 显示结果
    print('\n' + '='*80)
    print('【A 股监控池 - 行业分布】')
    print('='*80)
    
    for industry in sorted(monitor_df['industry'].unique()):
        stocks = monitor_df[monitor_df['industry'] == industry]
        print(f'\n【{industry}】({len(stocks)}只)')
        for idx, row in stocks.iterrows():
            print(f"  {row['ts_code']:<12} {row['name']:<15} PE:{row['pe']:>5.1f} ROE:{row['avg_roe']:>5.1f}%")
    
    # 保存结果
    output_file = Path('reports/monitor_pool_a_share_test_' + datetime.now().strftime('%Y%m%d_%H%M') + '.csv')
    monitor_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f'\n{"="*80}')
    print('✅ A 股监控池生成完成！')
    print(f'{"="*80}')
    print(f'\n文件已保存：{output_file}')
else:
    print('\n❌ 没有符合条件的股票')
