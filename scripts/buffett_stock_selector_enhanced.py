#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特选股策略 - 增强版
筛选标准:
1. 市值 > 50 亿港元
2. PE < 30
3. PB > 0
4. 价格 2-500 港元
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

# ============ 筛选条件 ============
FILTERS = {
    'min_market_cap': 50,        # 最小市值 50 亿港元
    'min_volume': 500000,        # 最小成交量 50 万
    'max_pe': 30,                # 最大 PE 30
    'min_price': 2,              # 最小价格 2 港元
    'max_price': 500,            # 最大价格 500 港元
    # 巴菲特财务指标
    'min_roe': 8,                # ROE > 8%
    'min_roic': 8,               # ROIC > 8%
    'max_debt_ratio': 60,        # 负债率 < 60%
    'min_fcf': 0,                # 自由现金流 > 0
}

print('='*80)
print('📈 巴菲特选股策略 - 增强版')
print('='*80)
print()
print('筛选条件:')
print('  ✅ 市值 > 50 亿港元')
print('  ✅ PE < 30')
print('  ✅ PB > 0')
print('  ✅ 价格 2-500 港元')
print('  ✅ 成交量 > 50 万股')
print('  ✅ 近 5 年 ROE > 8%')
print('  ✅ 近 5 年 ROIC > 8%')
print('  ✅ 资产负债率 < 60%')
print('  ✅ 自由现金流 > 0')
print()
print('='*80)
print()

# ============ 获取港股列表 ============
print('获取港股列表...')
try:
    from futu import *
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    ret, stock_list = quote_ctx.get_stock_basicinfo(Market.HK, SecurityType.STOCK)
    
    if ret != RET_OK or stock_list.empty:
        print('❌ 获取股票列表失败')
        exit(1)
    
    print(f'✅ 获取到 {len(stock_list)} 只港股\n')
    
except Exception as e:
    print(f'❌ 富途连接失败：{e}')
    exit(1)

# ============ 获取实时行情 ============
print('获取实时行情 (分批)...')
codes = stock_list['code'].tolist()
all_snapshot = []
batch_size = 300

for i in range(0, len(codes), batch_size):
    batch = codes[i:i+batch_size]
    ret, data = quote_ctx.get_market_snapshot(batch)
    
    if ret == RET_OK and not data.empty:
        all_snapshot.append(data)
        print(f'  进度：{min(i+batch_size, len(codes))}/{len(codes)}')
    
    time.sleep(0.3)

if not all_snapshot:
    print('❌ 获取行情失败')
    exit(1)

snapshot = pd.concat(all_snapshot, ignore_index=True)
print(f'✅ 获取到 {len(snapshot)} 只股票行情\n')

# ============ 初步筛选 ============
print('='*80)
print('【初步筛选】')
print('='*80)

filtered = snapshot.copy()
initial_count = len(filtered)

# 市值筛选
if 'total_market_val' in filtered.columns:
    before = len(filtered)
    filtered = filtered[filtered['total_market_val'] >= FILTERS['min_market_cap'] * 1e8]
    print(f'市值 > 50 亿港元：{before} → {len(filtered)}')

# PE 筛选
if 'pe_ratio' in filtered.columns:
    before = len(filtered)
    filtered = filtered[(filtered['pe_ratio'] > 0) & (filtered['pe_ratio'] <= FILTERS['max_pe'])]
    print(f'PE < 30: {before} → {len(filtered)}')

# PB 筛选
if 'pb_ratio' in filtered.columns:
    before = len(filtered)
    filtered = filtered[filtered['pb_ratio'] > 0]
    print(f'PB > 0: {before} → {len(filtered)}')

# 价格筛选
if 'last_price' in filtered.columns:
    before = len(filtered)
    filtered = filtered[(filtered['last_price'] >= FILTERS['min_price']) & (filtered['last_price'] <= FILTERS['max_price'])]
    print(f'价格 2-500 港元：{before} → {len(filtered)}')

# 成交量筛选
if 'volume' in filtered.columns:
    before = len(filtered)
    filtered = filtered[filtered['volume'] >= FILTERS['min_volume']]
    print(f'成交量 > 50 万股：{before} → {len(filtered)}')

print(f'\n✅ 初步筛选后剩余 {len(filtered)} 只股票 (通过率：{len(filtered)/initial_count*100:.1f}%)\n')

# ============ 财务指标筛选 ============
print('='*80)
print('【财务指标筛选】(Tushare 付费版)')
print('='*80)
print('获取近 5 年财务数据...\n')

# 转换股票代码格式 (HK.00700 → 00700.HK)
filtered['ts_code'] = filtered['code'].apply(lambda x: x.replace('HK.', '') + '.HK')
test_codes = filtered['ts_code'].tolist()[:50]  # 测试前 50 只

financial_stocks = []
not_enough_data = 0

for i, ts_code in enumerate(test_codes, 1):
    try:
        # 获取财务指标
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y%m%d')
        
        df = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df.empty:
            continue
        
        # 检查近 5 年数据
        if len(df) < 5:
            not_enough_data += 1
            continue
        
        # 计算近 5 年平均值
        avg_roe = df['roe'].mean() if 'roe' in df.columns else 0
        avg_roic = df['roic'].mean() if 'roic' in df.columns else 0
        avg_debt = df['debt_to_assets'].mean() if 'debt_to_assets' in df.columns else 100
        
        # 检查自由现金流 (最新一期)
        latest_fcf = df.iloc[0].get('free_cash_flow', 0) if 'free_cash_flow' in df.columns else 0
        
        # 应用筛选条件
        roe_ok = avg_roe > FILTERS['min_roe']
        roic_ok = avg_roic > FILTERS['min_roic']
        debt_ok = avg_debt < FILTERS['max_debt_ratio']
        fcf_ok = latest_fcf > FILTERS['min_fcf']
        
        if roe_ok and roic_ok and debt_ok and fcf_ok:
            # 找到对应的行情数据
            code = ts_code.replace('.HK', 'HK.')
            row = filtered[filtered['code'] == code]
            
            if not row.empty:
                stock_data = row.iloc[0].to_dict()
                stock_data.update({
                    'avg_roe': avg_roe,
                    'avg_roic': avg_roic,
                    'avg_debt_ratio': avg_debt,
                    'free_cash_flow': latest_fcf,
                })
                financial_stocks.append(stock_data)
                
                if len(financial_stocks) <= 10:
                    print(f"  ✅ {ts_code}: ROE={avg_roe:.1f}%, ROIC={avg_roic:.1f}%, 负债={avg_debt:.1f}%, FCF={latest_fcf:.0f}")
        
        if i % 10 == 0:
            print(f'  进度：{i}/{len(test_codes)}')
    
    except Exception as e:
        if i <= 10:
            print(f"  ⚠️ {ts_code}: 获取失败")

print(f'\n✅ 获取到 {len(financial_stocks)} 只股票符合财务标准')
print(f'⚠️ 数据不足 (少于 5 年): {not_enough_data} 只')

# ============ 显示结果 ============
if financial_stocks:
    print('\n' + '='*80)
    print('【巴菲特选股结果 Top 20】')
    print('='*80)
    
    # 转换为 DataFrame
    result_df = pd.DataFrame(financial_stocks)
    
    # 按综合评分排序 (ROE+ROIC)
    result_df['total_score'] = result_df['avg_roe'] + result_df['avg_roic']
    result_df = result_df.sort_values('total_score', ascending=False)
    
    print(f'{"排名":<4} {"代码":<12} {"名称":<15} {"价格":>8} {"PE":>6} {"ROE":>6} {"ROIC":>6} {"负债率":>8} {"FCF":>10}')
    print('-'*90)
    
    for idx, (_, row) in enumerate(result_df.head(20).iterrows(), 1):
        code = row['code'].replace('HK.', '')
        name = row.get('name', '')[:13]
        price = row['last_price']
        pe = row.get('pe_ratio', 'N/A')
        roe = row['avg_roe']
        roic = row['avg_roic']
        debt = row['avg_debt_ratio']
        fcf = row['free_cash_flow']
        
        pe_str = f'{pe:.1f}' if isinstance(pe, (int, float)) else 'N/A'
        fcf_str = f'{fcf:,.0f}' if isinstance(fcf, (int, float)) else 'N/A'
        
        print(f"{idx:<4} {code:<12} {name:<15} ${price:>7.2f} {pe_str:>6} {roe:>6.1f}% {roic:>6.1f}% {debt:>7.1f}% {fcf_str:>10}")

# ============ 保存结果 ============
if financial_stocks:
    output_file = Path('reports/buffett_selection_HK_' + datetime.now().strftime('%Y%m%d') + '.csv')
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f'\n✅ 结果已保存到：{output_file}')

print('\n' + '='*80)
print('✅ 巴菲特选股完成')
print('='*80)

quote_ctx.close()
