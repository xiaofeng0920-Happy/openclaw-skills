#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Tushare 获取港股财务数据
测试 ROIC、ROE、资产负债率、自由现金流
"""

import tushare as ts
import pandas as pd
from datetime import datetime

# 配置
TUSHARE_TOKEN = '4965cd353fccdbd111701a07ad3501f2b310f8d00e1240b0c0cfc3fe'
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

# 测试股票：腾讯控股
ts_code = '00700.HK'

print(f'测试获取 {ts_code} 的财务数据...\n')

# 1. 获取财务指标
print('【1. 财务指标 (ROE/ROIC 等)】')
try:
    df = pro.fina_indicator(ts_code=ts_code, start_date='20220101', end_date=datetime.now().strftime('%Y%m%d'))
    if not df.empty:
        print(f'数据列：{df.columns.tolist()}')
        print(f'\n最新数据 (报告期：{df["ann_date"].iloc[0]}):')
        
        # 检查是否有 ROE/ROIC
        if 'roe' in df.columns:
            print(f"  ROE (加权): {df['roe'].iloc[0]:.2f}%")
        if 'roic' in df.columns:
            print(f"  ROIC: {df['roic'].iloc[0]:.2f}%")
        if 'debt_to_assets' in df.columns:
            print(f"  资产负债率：{df['debt_to_assets'].iloc[0]:.2f}%")
        
        print(f'\n近 5 年数据:')
        print(df[['ann_date', 'roe', 'roic', 'debt_to_assets']].head(20))
    else:
        print('无数据')
except Exception as e:
    print(f'获取失败：{e}')

print('\n' + '='*80 + '\n')

# 2. 获取利润表
print('【2. 利润表】')
try:
    df = pro.income(ts_code=ts_code, start_date='20220101', end_date=datetime.now().strftime('%Y%m%d'))
    if not df.empty:
        print(f'数据列：{df.columns.tolist()[:20]}...')
        print(f'\n最新数据 (报告期：{df["ann_date"].iloc[0]}):')
        if 'net_profit' in df.columns:
            print(f"  净利润：{df['net_profit'].iloc[0]:,.2f} 万元")
        if 'operating_revenue' in df.columns:
            print(f"  营业收入：{df['operating_revenue'].iloc[0]:,.2f} 万元")
    else:
        print('无数据')
except Exception as e:
    print(f'获取失败：{e}')

print('\n' + '='*80 + '\n')

# 3. 获取资产负债表
print('【3. 资产负债表】')
try:
    df = pro.balancesheet(ts_code=ts_code, start_date='20220101', end_date=datetime.now().strftime('%Y%m%d'))
    if not df.empty:
        print(f'数据列：{df.columns.tolist()[:20]}...')
        print(f'\n最新数据 (报告期：{df["ann_date"].iloc[0]}):')
        if 'total_assets' in df.columns:
            print(f"  总资产：{df['total_assets'].iloc[0]:,.2f} 万元")
        if 'total_liability' in df.columns:
            print(f"  总负债：{df['total_liability'].iloc[0]:,.2f} 万元")
            assets = df['total_assets'].iloc[0]
            liability = df['total_liability'].iloc[0]
            if assets > 0:
                print(f"  资产负债率：{liability / assets * 100:.2f}%")
    else:
        print('无数据')
except Exception as e:
    print(f'获取失败：{e}')

print('\n' + '='*80 + '\n')

# 4. 获取现金流量表
print('【4. 现金流量表】')
try:
    df = pro.cashflow(ts_code=ts_code, start_date='20220101', end_date=datetime.now().strftime('%Y%m%d'))
    if not df.empty:
        print(f'数据列：{df.columns.tolist()[:20]}...')
        print(f'\n最新数据 (报告期：{df["ann_date"].iloc[0]}):')
        if 'free_cash_flow' in df.columns:
            print(f"  自由现金流：{df['free_cash_flow'].iloc[0]:,.2f} 万元")
        elif 'oper_cash_flow' in df.columns:
            print(f"  经营现金流：{df['oper_cash_flow'].iloc[0]:,.2f} 万元")
        if 'invest_cash_flow' in df.columns:
            print(f"  投资现金流：{df['invest_cash_flow'].iloc[0]:,.2f} 万元")
    else:
        print('无数据')
except Exception as e:
    print(f'获取失败：{e}')

print('\n✅ 测试完成')
