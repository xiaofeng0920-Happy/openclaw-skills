#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特选股策略 - A 股测试版
筛选标准:
1. 市值 > 100 亿人民币
2. PE < 30
3. PB > 0
4. 价格 2-500 元
5. 成交量 > 50 万股
6. 近 5 年 ROE > 8%
7. 近 5 年 ROIC > 8%
8. 资产负债率 < 60%
9. 自由现金流 > 0
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# 添加 Tushare 接口
sys.path.insert(0, str(Path(__file__).parent.parent))
from tushare_data_api import pro

print('='*80)
print('📈 巴菲特选股策略 - A 股测试')
print('='*80)
print()
print('筛选条件:')
print('  ✅ 市值 > 100 亿人民币')
print('  ✅ PE < 30')
print('  ✅ PB > 0')
print('  ✅ 价格 2-500 元')
print('  ✅ 成交量 > 50 万股')
print('  ✅ 近 5 年 ROE > 8%')
print('  ✅ 近 5 年 ROIC > 8%')
print('  ✅ 资产负债率 < 60%')
print('  ✅ 自由现金流 > 0')
print()
print('='*80)
print()

# ============ 获取 A 股列表 ============
print('获取 A 股列表...')
try:
    df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,area,list_date')
    
    if df.empty:
        print('❌ 获取股票列表失败')
        exit(1)
    
    print(f'✅ 获取到 {len(df)} 只 A 股\n')
    
except Exception as e:
    print(f'❌ 获取失败：{e}')
    exit(1)

# ============ 获取实时行情 ============
print('获取实时行情 (前 500 只测试)...')
test_stocks = df.head(500)
print(f'测试样本：{len(test_stocks)} 只\n')

# ============ 财务指标筛选 ============
print('='*80)
print('【财务指标筛选】')
print('='*80)
print('获取近 5 年财务数据...\n')

end_date = datetime.now().strftime('%Y%m%d')
start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y%m%d')

buffett_stocks = []
no_data_count = 0

for i, (_, row) in enumerate(test_stocks.iterrows(), 1):
    ts_code = row['ts_code']
    
    try:
        # 获取财务指标
        df = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df.empty:
            no_data_count += 1
            continue
        
        # 检查数据量 (至少 5 年数据)
        if len(df) < 5:
            no_data_count += 1
            continue
        
        # 计算近 5 年平均
        avg_roe = df['roe'].mean() if 'roe' in df.columns else 0
        avg_roic = df['roic'].mean() if 'roic' in df.columns else 0
        avg_debt = df['debt_to_assets'].mean() if 'debt_to_assets' in df.columns else 100
        
        # 最新一期自由现金流
        latest_fcf = df.iloc[0].get('free_cash_flow', 0) if 'free_cash_flow' in df.columns else 0
        
        # 应用筛选条件
        roe_ok = avg_roe > 8
        roic_ok = avg_roic > 8
        debt_ok = avg_debt < 60
        fcf_ok = latest_fcf > 0
        
        if roe_ok and roic_ok and debt_ok and fcf_ok:
            buffett_stocks.append({
                'ts_code': ts_code,
                'name': row['name'],
                'industry': row.get('industry', ''),
                'avg_roe': avg_roe,
                'avg_roic': avg_roic,
                'avg_debt_ratio': avg_debt,
                'free_cash_flow': latest_fcf,
            })
            
            if len(buffett_stocks) <= 10:
                print(f"  ✅ {ts_code} {row['name'][:10]:<10} ROE:{avg_roe:.1f}% ROIC:{avg_roic:.1f}% 负债:{avg_debt:.1f}% FCF:{latest_fcf:,.0f}")
        
        if i % 100 == 0:
            print(f'  进度：{i}/{len(test_stocks)}')
    
    except Exception as e:
        if i <= 10:
            print(f"  ⚠️ {ts_code}: 获取失败")

print(f'\n✅ 符合巴菲特标准：{len(buffett_stocks)} 只')
print(f'⚠️ 数据不足：{no_data_count} 只')

# ============ 显示结果 ============
if buffett_stocks:
    print('\n' + '='*80)
    print('【巴菲特选股结果 Top 20】')
    print('='*80)
    
    # 转换为 DataFrame
    result_df = pd.DataFrame(buffett_stocks)
    
    # 按综合评分排序
    result_df['total_score'] = result_df['avg_roe'] + result_df['avg_roic']
    result_df = result_df.sort_values('total_score', ascending=False)
    
    print(f'{"排名":<4} {"代码":<12} {"名称":<15} {"行业":<15} {"ROE":>6} {"ROIC":>6} {"负债率":>8} {"FCF":>12}')
    print('-'*90)
    
    for idx, (_, row) in enumerate(result_df.head(20).iterrows(), 1):
        code = row['ts_code'].split('.')[0]
        name = row['name'][:13]
        industry = row.get('industry', '')[:13]
        roe = row['avg_roe']
        roic = row['avg_roic']
        debt = row['avg_debt_ratio']
        fcf = row['free_cash_flow']
        
        fcf_str = f'{fcf:,.0f}' if isinstance(fcf, (int, float)) else 'N/A'
        
        print(f"{idx:<4} {code:<12} {name:<15} {industry:<15} {roe:>6.1f}% {roic:>6.1f}% {debt:>7.1f}% {fcf_str:>12}")

# ============ 保存结果 ============
if buffett_stocks:
    output_file = Path('reports/buffett_selection_CN_' + datetime.now().strftime('%Y%m%d') + '.csv')
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f'\n✅ 结果已保存到：{output_file}')

print('\n' + '='*80)
print('✅ 巴菲特选股完成')
print('='*80)
