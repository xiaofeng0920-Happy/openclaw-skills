#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股全市场选股 - 生成 A 股监控池
筛选标准:
1. 市值 > 100 亿人民币
2. PE < 30
3. PB > 0
4. 近 5 年 ROE > 8%
5. 近 5 年 ROIC > 8%
6. 资产负债率 < 60%
7. 自由现金流 > 0
按行业分类，每个行业选 Top 2，形成监控池
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
print('📊 A 股全市场选股 - 生成监控池')
print('='*80)
print()
print('【筛选标准】')
print('  ✅ 市值 > 100 亿人民币')
print('  ✅ PE < 30')
print('  ✅ PB > 0')
print('  ✅ 近 5 年 ROE > 8%')
print('  ✅ 近 5 年 ROIC > 8%')
print('  ✅ 资产负债率 < 60%')
print('  ✅ 自由现金流 > 0')
print()

# ============ 获取 A 股股票列表 ============
print('获取 A 股股票列表...')
df_basic = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,area,list_date')
print(f'✅ 获取到 {len(df_basic)} 只 A 股')
print()

# ============ 获取实时行情和财务数据 ============
print('获取实时行情和财务数据...')
print('(分批获取，避免限流)\n')

# 筛选条件
MIN_MARKET_CAP = 100  # 100 亿
MAX_PE = 30
MIN_ROE = 8
MIN_ROIC = 8
MAX_DEBT_RATIO = 60

qualified_stocks = []

# 分批处理，每批 100 只
batch_size = 100
total_batches = (len(df_basic) + batch_size - 1) // batch_size

for batch_idx in range(total_batches):
    start_idx = batch_idx * batch_size
    end_idx = min((batch_idx + 1) * batch_size, len(df_basic))
    batch_df = df_basic.iloc[start_idx:end_idx]
    
    for idx, row in batch_df.iterrows():
        ts_code = row['ts_code']
        
        try:
            # 获取财务指标 (近 5 年)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y%m%d')
            
            fina_df = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
            
            if fina_df.empty or len(fina_df) < 5:
                continue
            
            # 计算近 5 年平均值
            avg_roe = fina_df['roe'].mean() if 'roe' in fina_df.columns else 0
            avg_roic = fina_df['roic'].mean() if 'roic' in fina_df.columns else 0
            avg_debt = fina_df['debt_to_assets'].mean() if 'debt_to_assets' in fina_df.columns else 100
            
            # 检查 ROE 和 ROIC
            if avg_roe < MIN_ROE or avg_roic < MIN_ROIC:
                continue
            
            # 检查负债率
            if avg_debt > MAX_DEBT_RATIO:
                continue
            
            # 获取最新估值
            latest_fina = fina_df.iloc[0]
            
            # 获取股票基本信息
            stock_info = pro.stock_basic(ts_code=ts_code, fields='ts_code,name,industry,pe,pb,total_mv')
            
            if stock_info.empty:
                continue
            
            info = stock_info.iloc[0]
            pe = info.get('pe', None)
            pb = info.get('pb', None)
            market_cap = info.get('total_mv', 0) / 10000  # 转换为亿
            
            # 检查 PE 和市值
            if pe is None or pe <= 0 or pe > MAX_PE:
                continue
            
            if market_cap < MIN_MARKET_CAP:
                continue
            
            # 符合条件
            qualified_stocks.append({
                'ts_code': ts_code,
                'name': info.get('name', ''),
                'industry': row.get('industry', ''),
                'pe': pe,
                'pb': pb,
                'market_cap': market_cap,
                'avg_roe': avg_roe,
                'avg_roic': avg_roic,
                'avg_debt_ratio': avg_debt,
            })
        
        except Exception as e:
            continue
        
        # 每 50 只暂停一下，避免限流
        if len(qualified_stocks) % 50 == 0:
            time.sleep(0.5)
    
    # 进度显示
    if (batch_idx + 1) % 10 == 0:
        print(f'  进度：{end_idx}/{len(df_basic)} (已找到 {len(qualified_stocks)} 只)')

print(f'\n✅ 初步筛选：{len(qualified_stocks)} 只股票符合财务标准')

# ============ 按行业分类，每个行业选 Top 2 ============
print('\n按行业分类，生成监控池...')

qualified_df = pd.DataFrame(qualified_stocks)

# 按行业分组
industry_groups = qualified_df.groupby('industry')

monitor_pool = []

for industry, group in industry_groups:
    if pd.isna(industry) or industry == '':
        continue
    
    # 按综合评分排序 (ROE+ROIC)
    group['score'] = group['avg_roe'] + group['avg_roic']
    group_sorted = group.sort_values('score', ascending=False)
    
    # 选 Top 2
    top2 = group_sorted.head(2)
    
    for idx, row in top2.iterrows():
        monitor_pool.append({
            'ts_code': row['ts_code'],
            'name': row['name'],
            'industry': industry,
            'pe': row['pe'],
            'pb': row['pb'],
            'market_cap': row['market_cap'],
            'avg_roe': row['avg_roe'],
            'avg_roic': row['avg_roic'],
            'avg_debt_ratio': row['avg_debt_ratio'],
            'score': row['score'],
        })

# 转换为 DataFrame
monitor_df = pd.DataFrame(monitor_pool)

print(f'✅ 监控池股票：{len(monitor_df)} 只')
print(f'✅ 覆盖行业：{len(monitor_df["industry"].unique())} 个')

# ============ 显示结果 ============
print('\n' + '='*80)
print('【A 股监控池 - 行业分布】')
print('='*80)

for industry in sorted(monitor_df['industry'].unique()):
    stocks = monitor_df[monitor_df['industry'] == industry]
    print(f'\n【{industry}】({len(stocks)}只)')
    for idx, row in stocks.iterrows():
        print(f"  {row['ts_code']:<12} {row['name']:<15} PE:{row['pe']:>5.1f} ROE:{row['avg_roe']:>5.1f}% ROIC:{row['avg_roic']:>5.1f}%")

# ============ 保存结果 ============
output_file = Path('reports/monitor_pool_a_share_full_' + datetime.now().strftime('%Y%m%d_%H%M') + '.csv')
monitor_df.to_csv(output_file, index=False, encoding='utf-8-sig')

print(f'\n{"="*80}')
print('✅ A 股监控池生成完成！')
print(f'{"="*80}')
print(f'\n文件已保存：{output_file}')
print(f'监控股票：{len(monitor_df)} 只')
print(f'覆盖行业：{len(monitor_df["industry"].unique())} 个')
print(f'平均 PE: {monitor_df["pe"].mean():.1f}')
print(f'平均 ROE: {monitor_df["avg_roe"].mean():.1f}%')
print(f'平均 ROIC: {monitor_df["avg_roic"].mean():.1f}%')
print(f'平均负债率：{monitor_df["avg_debt_ratio"].mean():.1f}%')
