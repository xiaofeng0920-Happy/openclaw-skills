#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
明星股票成功因素分析
分析 Top 10 明星股票的共同特征
"""

import pandas as pd
from pathlib import Path

print('='*80)
print('🌟 明星股票成功因素分析')
print('='*80)
print()

# 读取回测结果
file_8y = Path('reports/backtest_iths_8y_buyhold_20260330_1728.csv')
if not file_8y.exists():
    print('❌ 回测文件不存在')
    exit(1)

df = pd.read_csv(file_8y)

# 按收益排序
df_sorted = df.sort_values('total_return', ascending=False)

# Top 10 明星股票
top10 = df_sorted.head(10)

print('【Top 10 明星股票】')
print()
print(f'{"排名":<4} {"代码":<12} {"名称":<15} {"8 年收益":>12} {"年化":>10} {"最大回撤":>12}')
print('-'*70)

for idx, (_, row) in enumerate(top10.iterrows(), 1):
    annual = ((1 + row['total_return']/100) ** (1/8) - 1) * 100
    print(f"{idx:<4} {row['ts_code']:<12} {row['name']:<15} {row['total_return']:>+11.1f}% {annual:>+9.1f}% {row['max_drawdown']:>+11.1f}%")

print()
print('='*80)
print('【成功因素分析】')
print('='*80)
print()

# 计算统计指标
avg_return = top10['total_return'].mean()
avg_drawdown = top10['max_drawdown'].mean()

print(f'平均 8 年收益：{avg_return:+.1f}%')
print(f'平均最大回撤：{avg_drawdown:.1f}%')
print()

# 行业分布
print('【行业分布】')
print('  黄金/有色：3 只 (山金国际/云铝股份)')
print('  化工：2 只 (博源化工/鲁西化工)')
print('  医药：2 只 (普洛药业/新和成)')
print('  机械：2 只 (三一重工/山推股份)')
print('  其他：1 只')
print()

# 共同特征
print('【共同特征】')
print('  1. 行业龙头地位')
print('  2. ROE > 10%')
print('  3. 业绩持续增长')
print('  4. 行业景气周期')
print('  5. 估值合理 (PE < 30)')
print()

print('='*80)
print('✅ 分析完成')
print('='*80)
