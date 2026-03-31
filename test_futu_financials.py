#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试获取港股财务数据
"""

from futu import *
import pandas as pd

# 连接 OpenD
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

# 测试股票：00700.HK 腾讯
code = 'HK.00700'

print(f'测试获取 {code} 的财务数据...\n')

# 1. 获取基本财务数据
print('【1. 基本财务数据】')
ret, data = quote_ctx.get_financial_metrics(code)
if ret == RET_OK and not data.empty:
    print(data.columns.tolist())
    print(data.head())
else:
    print(f'获取失败：{data}')

print('\n' + '='*80 + '\n')

# 2. 获取资产负债表
print('【2. 资产负债表】')
ret, data = quote_ctx.get_balance_sheet(code)
if ret == RET_OK and not data.empty:
    print(data.columns.tolist())
    if 'total_assets' in data.columns and 'total_liabilities' in data.columns:
        print(f"\n最新资产负债率：{data['total_liabilities'].iloc[0] / data['total_assets'].iloc[0] * 100:.2f}%")
    print(data.head(3))
else:
    print(f'获取失败：{data}')

print('\n' + '='*80 + '\n')

# 3. 获取利润表
print('【3. 利润表】')
ret, data = quote_ctx.get_income_statement(code)
if ret == RET_OK and not data.empty:
    print(data.columns.tolist())
    print(data.head(3))
else:
    print(f'获取失败：{data}')

print('\n' + '='*80 + '\n')

# 4. 获取现金流量表
print('【4. 现金流量表】')
ret, data = quote_ctx.get_cash_flow_statement(code)
if ret == RET_OK and not data.empty:
    print(data.columns.tolist())
    if 'free_cash_flow' in data.columns:
        print(f"\n最新自由现金流：{data['free_cash_flow'].iloc[0]:,.2f}")
    print(data.head(3))
else:
    print(f'获取失败：{data}')

quote_ctx.close()
print('\n✅ 测试完成')
