#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版港股选股 - 加入巴菲特财务指标

筛选标准:
1. 市值 > 50 亿港元
2. PE < 30
3. PB > 0
4. 价格 2-500 港元
5. 成交量 > 50 万股
6. ROE > 8% (最新财报)
7. 资产负债率 < 60%
"""

from futu import *
import pandas as pd
import time
from pathlib import Path
from datetime import datetime

# 连接 OpenD
print('='*80)
print('📊 增强版港股选股系统 - 巴菲特财务指标')
print('='*80)
print()

print('连接富途 OpenD...')
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
time.sleep(1)  # 等待连接稳定
print('✅ OpenD 连接成功\n')

# 获取港股列表
print('获取港股市场列表...')
ret, stock_list = quote_ctx.get_stock_basicinfo(Market.HK, SecurityType.STOCK)
if ret != RET_OK or stock_list.empty:
    print('❌ 获取股票列表失败')
    quote_ctx.close()
    exit(1)

print(f'✅ 获取到 {len(stock_list)} 只港股\n')

# 获取实时行情 (分批)
print('获取实时行情数据...')
codes = stock_list['code'].tolist()

# 分批获取，每批 500 只
all_snapshot = []
batch_size = 500

for i in range(0, len(codes), batch_size):
    batch = codes[i:i+batch_size]
    ret, data = quote_ctx.get_market_snapshot(batch)
    
    if ret == RET_OK and not data.empty:
        all_snapshot.append(data)
        print(f'  进度：{min(i+batch_size, len(codes))}/{len(codes)}')
    else:
        print(f'  批次 {i//batch_size + 1} 失败，跳过')
    
    time.sleep(0.5)  # 避免请求过快

if not all_snapshot:
    print('❌ 获取行情失败')
    quote_ctx.close()
    exit(1)

snapshot = pd.concat(all_snapshot, ignore_index=True)
print(f'✅ 获取到 {len(snapshot)} 只股票行情\n')

# 初步筛选
print('='*80)
print('【初步筛选】')
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

# 成交量 > 50 万
if 'volume' in filtered.columns:
    before = len(filtered)
    filtered = filtered[filtered['volume'] >= 500000]
    print(f'成交量 > 50 万股：{before} → {len(filtered)} (-{before-len(filtered)})')

print(f'\n✅ 初步筛选后剩余 {len(filtered)} 只股票 (通过率：{len(filtered)/initial_count*100:.1f}%)\n')

# 获取财务数据
print('='*80)
print('【财务数据筛选】')
print('='*80)
print('获取财务指标 (ROE、资产负债率)...')
print('注意：富途财务数据获取较慢，仅测试前 100 只股票\n')

test_codes = filtered['code'].tolist()[:100]  # 测试前 100 只
financial_data = []

for i, code in enumerate(test_codes, 1):
    try:
        ret, data = quote_ctx.get_financial_metrics(code)
        
        if ret == RET_OK and not data.empty:
            latest = data.iloc[0]
            
            roe = latest.get('roewa', None)
            debt_ratio = latest.get('gross_debt_ratio', None)
            
            # 检查是否符合财务标准
            roe_ok = roe is not None and roe > 8
            debt_ok = debt_ratio is not None and debt_ratio < 60
            
            financial_data.append({
                'code': code,
                'roe': roe,
                'debt_ratio': debt_ratio,
                'roe_ok': roe_ok,
                'debt_ok': debt_ok,
            })
            
            if i <= 10 or i % 20 == 0:
                status = '✅' if (roe_ok and debt_ok) else '⚠️'
                roe_str = f"{roe:.1f}%" if roe else 'N/A'
                debt_str = f"{debt_ratio:.1f}%" if debt_ratio else 'N/A'
                print(f"  {status} {code}: ROE={roe_str}, 负债率={debt_str}")
        
        if i % 20 == 0:
            print(f'  进度：{i}/{len(test_codes)}')
        
        time.sleep(0.3)  # 避免请求过快
    
    except Exception as e:
        if i <= 10:
            print(f"  ❌ {code}: 获取失败 - {str(e)[:50]}")

# 转换为 DataFrame
fin_df = pd.DataFrame(financial_data)

if not fin_df.empty:
    print(f'\n✅ 获取到 {len(fin_df)} 只股票的财务数据\n')
    
    # 财务筛选
    print('应用财务筛选条件:')
    before = len(fin_df)
    
    # ROE > 8%
    fin_df = fin_df[fin_df['roe_ok'] == True]
    print(f'  ROE > 8%: {before} → {len(fin_df)} (-{before-len(fin_df)})')
    
    # 资产负债率 < 60%
    before_debt = len(fin_df)
    fin_df = fin_df[fin_df['debt_ok'] == True]
    print(f'  资产负债率 < 60%: {before_debt} → {len(fin_df)} (-{before_debt-len(fin_df)})')
    
    # 合并数据
    if len(fin_df) > 0:
        result = filtered.merge(fin_df, on='code', how='inner')
        print(f'\n✅ 最终筛选结果：{len(result)} 只股票')
    else:
        print('\n⚠️ 财务筛选后无股票，显示初步筛选结果')
        result = filtered
else:
    print('\n⚠️ 无法获取财务数据，显示初步筛选结果')
    result = filtered

# 保存结果
output_file = Path('reports/stock_selection_HK_20260330_buffett.csv')
result.to_csv(output_file, index=False, encoding='utf-8-sig')
print(f'\n✅ 结果已保存到：{output_file}')

# 显示 Top 20
if not result.empty and 'pe_ratio' in result.columns:
    print('\n' + '='*80)
    print('【Top 20 股票】')
    print('='*80)
    
    # 按 PE 排序
    top20 = result.sort_values('pe_ratio').head(20)
    
    print(f'{"排名":<4} {"代码":<10} {"名称":<15} {"价格":>8} {"PE":>6} {"ROE":>8} {"负债率":>10}')
    print('-'*80)
    
    for idx, (_, row) in enumerate(top20.iterrows(), 1):
        code = row['code'].replace('HK.', '')
        name = row['name'][:13]
        price = row['last_price']
        pe = row['pe_ratio']
        roe = row.get('roe', None)
        debt = row.get('debt_ratio', None)
        
        roe_str = f"{roe:.1f}%" if isinstance(roe, (int, float)) else 'N/A'
        debt_str = f"{debt:.1f}%" if isinstance(debt, (int, float)) else 'N/A'
        
        print(f"{idx:<4} {code:<10} {name:<15} ${price:>7.2f} {pe:>6.1f} {roe_str:>8} {debt_str:>10}")

print('\n' + '='*80)
print('✅ 选股完成')
print('='*80)

quote_ctx.close()
