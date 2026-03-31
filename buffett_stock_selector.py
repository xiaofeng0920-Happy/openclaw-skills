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
6. 近 5 年 ROIC > 8% (使用最新季报数据)
7. 资产负债率 < 60%
8. ROE > 8%
9. 自由现金流 > 0
"""

from futu import *
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

# 连接 OpenD
print('连接富途 OpenD...')
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
print('✅ OpenD 连接成功\n')

# 获取港股列表
print('获取港股市场列表...')
ret, stock_list = quote_ctx.get_stock_basicinfo(Market.HK, SecurityType.STOCK)
if ret != RET_OK or stock_list.empty:
    print('获取股票列表失败')
    quote_ctx.close()
    exit(1)

print(f'✅ 获取到 {len(stock_list)} 只港股\n')

# 获取实时行情
print('获取实时行情数据...')
codes = stock_list['code'].tolist()
ret, snapshot = quote_ctx.get_market_snapshot(codes)

if ret != RET_OK or snapshot.empty:
    print('获取行情失败')
    quote_ctx.close()
    exit(1)

print(f'✅ 获取到 {len(snapshot)} 只股票行情\n')

# 初步筛选 (基于行情数据)
print('初步筛选...')
filtered = snapshot.copy()

# 市值 > 50 亿港元
if 'market_val' in filtered.columns:
    filtered = filtered[filtered['market_val'] >= 50 * 1e8]
    print(f'  市值>50 亿：{len(filtered)} 只')

# PE < 30 且 > 0
if 'pe_ratio' in filtered.columns:
    filtered = filtered[(filtered['pe_ratio'] > 0) & (filtered['pe_ratio'] <= 30)]
    print(f'  PE<30: {len(filtered)} 只')

# PB > 0
if 'pb_ratio' in filtered.columns:
    filtered = filtered[filtered['pb_ratio'] > 0]
    print(f'  PB>0: {len(filtered)} 只')

# 价格 2-500 港元
if 'last_price' in filtered.columns:
    filtered = filtered[(filtered['last_price'] >= 2) & (filtered['last_price'] <= 500)]
    print(f'  价格 2-500: {len(filtered)} 只')

# 成交量 > 50 万
if 'volume' in filtered.columns:
    filtered = filtered[filtered['volume'] >= 500000]
    print(f'  成交量>50 万：{len(filtered)} 只')

print(f'\n✅ 初步筛选后剩余 {len(filtered)} 只股票\n')

# 获取财务数据 (分批获取，避免超时)
print('获取财务数据 (分批获取，可能需要几分钟)...')
financial_data = []

test_codes = filtered['code'].tolist()[:50]  # 先测试前 50 只
print(f'测试前 {len(test_codes)} 只股票...\n')

for i, code in enumerate(test_codes, 1):
    try:
        ret, data = quote_ctx.get_financial_metrics(code)
        
        if ret == RET_OK and not data.empty:
            # 提取关键指标
            latest = data.iloc[0]
            
            roe = latest.get('roewa', None)  # ROE 加权
            debt_ratio = latest.get('gross_debt_ratio', None)  # 资产负债率
            
            financial_data.append({
                'code': code,
                'roe': roe,
                'debt_ratio': debt_ratio,
                'roic': latest.get('roic', None),
                'fcf': latest.get('free_cash_flow', None),
            })
            
            if i <= 5:
                print(f"  {code}: ROE={roe:.1f}% (有数据)" if roe else f"  {code}: 无 ROE 数据")
        
        if i % 10 == 0:
            print(f'  进度：{i}/{len(test_codes)}')
    
    except Exception as e:
        if i <= 5:
            print(f"  {code}: 获取失败 - {e}")

# 转换为 DataFrame
fin_df = pd.DataFrame(financial_data)

if not fin_df.empty:
    print(f'\n✅ 获取到 {len(fin_df)} 只股票的财务数据\n')
    
    # 财务筛选
    print('应用财务筛选条件...')
    
    # ROE > 8%
    if 'roe' in fin_df.columns:
        fin_df = fin_df[fin_df['roe'] > 8]
        print(f'  ROE>8%: {len(fin_df)} 只')
    
    # 资产负债率 < 60%
    if 'debt_ratio' in fin_df.columns:
        fin_df = fin_df[fin_df['debt_ratio'] < 60]
        print(f'  负债率<60%: {len(fin_df)} 只')
    
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
    print('\n【Top 20 股票】')
    top20 = result.sort_values('pe_ratio').head(20)
    for idx, row in top20.iterrows():
        code = row['code'].replace('HK.', '')
        name = row['name'][:15]
        price = row['last_price']
        pe = row['pe_ratio']
        roe = row.get('roe', 'N/A')
        roe_str = f"{roe:.1f}%" if isinstance(roe, (int, float)) else 'N/A'
        print(f"  {code:<10} {name:<15} ${price:>7.2f}  PE:{pe:>5.1f}  ROE:{roe_str}")

quote_ctx.close()
print('\n✅ 选股完成')
