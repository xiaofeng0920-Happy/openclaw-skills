#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取港股财务数据 (使用富途 OpenD)
计算近 5 年平均 ROIC、ROE、资产负债率、自由现金流
"""

from futu import *
import pandas as pd
from datetime import datetime

# 连接 OpenD
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

# 测试几只股票
test_codes = ['HK.00700', 'HK.00883', 'HK.00939', 'HK.01800']

print('测试获取港股财务数据...\n')

for code in test_codes:
    print(f'【{code}】')
    
    # 获取基本财务数据
    ret, data = quote_ctx.get_financial_metrics(code)
    
    if ret == RET_OK and not data.empty:
        print(f"  数据列数：{len(data.columns)}")
        print(f"  数据行数：{len(data)}")
        
        # 显示部分列
        cols_to_show = ['time', 'pe', 'pb', 'roewa', 'gross_debt_ratio']
        available_cols = [c for c in cols_to_show if c in data.columns]
        if available_cols:
            print(f"\n  最新数据:")
            print(data[available_cols].head(1))
        
        # 检查是否有 ROIC
        if 'roic' in data.columns:
            print(f"  ROIC: {data['roic'].iloc[0]:.2f}%")
        else:
            print("  (无 ROIC 数据)")
            
        # 检查 ROE
        if 'roewa' in data.columns:
            print(f"  ROE (加权): {data['roewa'].iloc[0]:.2f}%")
        
        # 检查负债率
        if 'gross_debt_ratio' in data.columns:
            print(f"  资产负债率：{data['gross_debt_ratio'].iloc[0]:.2f}%")
    else:
        print(f"  获取失败：{data}")
    
    print()

quote_ctx.close()
print('✅ 测试完成')
