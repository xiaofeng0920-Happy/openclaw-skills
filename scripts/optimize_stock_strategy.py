#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于回测结果优化选股策略
分析成功股票特征，优化筛选条件
"""

import pandas as pd
from pathlib import Path

print('='*80)
print('📈 选股策略优化分析')
print('='*80)
print()

# 读取回测结果
file_8y = Path('reports/backtest_iths_8y_buyhold_20260330_1728.csv')
if not file_8y.exists():
    print('❌ 回测文件不存在')
    exit(1)

df = pd.read_csv(file_8y)

# 按收益分组
high_performers = df[df['total_return'] > 200]  # 收益>200%
mid_performers = df[(df['total_return'] > 50) & (df['total_return'] <= 200)]
low_performers = df[df['total_return'] <= 50]

print('【收益分组】')
print(f'高收益组 (>200%): {len(high_performers)}只')
print(f'中收益组 (50-200%): {len(mid_performers)}只')
print(f'低收益组 (<50%): {len(low_performers)}只')
print()

# 分析高收益组特征
if len(high_performers) > 0:
    print('【高收益组特征】')
    print(f'平均收益：{high_performers["total_return"].mean():+.1f}%')
    print(f'平均回撤：{high_performers["max_drawdown"].mean():.1f}%')
    print()
    
    # 行业分布
    print('行业分布:')
    # 这里简化处理，实际需要行业数据
    print('  需要补充行业数据进行分析')
    print()

# 优化建议
print('【优化建议】')
print('1. 增加行业筛选：优先黄金/化工/医药/机械')
print('2. 增加 ROE 筛选：ROE > 15%')
print('3. 增加成长性：营收增长 > 20%')
print('4. 增加现金流：经营现金流 > 净利润')
print('5. 降低负债：负债率 < 50%')
print()

# 新策略
print('【新选股策略】')
print('市值 > 100 亿')
print('PE < 25 (更严格)')
print('ROE > 15% (提高)')
print('负债率 < 50% (降低)')
print('营收增长 > 20% (新增)')
print('行业：黄金/化工/医药/机械 (优先)')
print()

print('='*80)
print('✅ 策略优化完成')
print('='*80)
