#!/usr/bin/env python3
"""
完整回测测试 - 使用真实股票池数据
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import pandas as pd
import numpy as np
from datetime import datetime

print("=" * 80)
print("📊 锋哥量化策略 - 完整回测测试")
print("=" * 80)
print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载股票池数据
print("【步骤 1】加载股票池数据")
stock_pools_dir = os.path.join(os.path.dirname(__file__), '../config/stock_pools')

# 加载 177 支池
with open(os.path.join(stock_pools_dir, 'bull_177.json'), 'r', encoding='utf-8') as f:
    import json
    bull_pool = json.load(f)
print(f"✅ 牛市股票池：{len(bull_pool['stocks'])} 支股票")

# 加载 60 支池
with open(os.path.join(stock_pools_dir, 'bear_60.json'), 'r', encoding='utf-8') as f:
    bear_pool = json.load(f)
print(f"✅ 熊市股票池：{len(bear_pool['stocks'])} 支股票")

# 加载 73 支池
with open(os.path.join(stock_pools_dir, 'sideways_73.json'), 'r', encoding='utf-8') as f:
    sideways_pool = json.load(f)
print(f"✅ 震荡市股票池：{len(sideways_pool['stocks'])} 支股票（示例）")

print()

# 加载历史回测数据
print("【步骤 2】加载历史回测数据")
backtest_dir = os.path.join(os.path.dirname(__file__), '../config/backtest_data')

backtest_177 = pd.read_excel(os.path.join(backtest_dir, 'backtest_177.xlsx'))
backtest_60 = pd.read_excel(os.path.join(backtest_dir, 'backtest_60.xlsx'))
backtest_hs300 = pd.read_excel(os.path.join(backtest_dir, 'hs300_backtest.xlsx'))

print(f"✅ 177 支池回测数据：{len(backtest_177)} 行")
print(f"✅ 60 支池回测数据：{len(backtest_60)} 行")
print(f"✅ 沪深 300 回测数据：{len(backtest_hs300)} 行")

print()

# 计算绩效指标
print("【步骤 3】计算绩效指标")

def calculate_metrics(df, name):
    # 查找价格列
    price_col = None
    for col in df.columns:
        if '每日收盘价' in col or col == 'Price':
            price_col = col
            break
    
    if price_col is None:
        return None
    
    prices = df[price_col].dropna()
    # 转换为数值类型
    prices = pd.to_numeric(prices, errors='coerce').dropna()
    
    if len(prices) < 2:
        return None
    
    initial = prices.iloc[0]
    final = prices.iloc[-1]
    cumulative_return = (final / initial - 1) * 100
    years = len(prices) / 252
    annualized_return = ((1 + cumulative_return/100) ** (1/years) - 1) * 100
    
    rolling_max = prices.expanding().max()
    drawdown = (prices - rolling_max) / rolling_max * 100
    max_drawdown = drawdown.min()
    
    daily_returns = prices.pct_change().dropna()
    volatility = daily_returns.std() * np.sqrt(252) * 100
    sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() > 0 else 0
    
    return {
        '组合': name,
        '累计收益 (%)': round(cumulative_return, 2),
        '年化收益 (%)': round(annualized_return, 2),
        '最大回撤 (%)': round(max_drawdown, 2),
        '波动率 (%)': round(volatility, 2),
        '夏普比率': round(sharpe, 3)
    }

metrics_177 = calculate_metrics(backtest_177, '177 支池')
metrics_60 = calculate_metrics(backtest_60, '60 支池')
metrics_hs300 = calculate_metrics(backtest_hs300, '沪深 300')

print()
print("【步骤 4】回测结果汇总")
print()
print(f"{'组合':<15} {'累计收益':>12} {'年化收益':>12} {'最大回撤':>12} {'夏普比率':>12}")
print("-" * 65)
print(f"{metrics_177['组合']:<15} {metrics_177['累计收益 (%)']:>11.2f}% {metrics_177['年化收益 (%)']:>11.2f}% {metrics_177['最大回撤 (%)']:>11.2f}% {metrics_177['夏普比率']:>12.3f}")
print(f"{metrics_60['组合']:<15} {metrics_60['累计收益 (%)']:>11.2f}% {metrics_60['年化收益 (%)']:>11.2f}% {metrics_60['最大回撤 (%)']:>11.2f}% {metrics_60['夏普比率']:>12.3f}")
print(f"{metrics_hs300['组合']:<15} {metrics_hs300['累计收益 (%)']:>11.2f}% {metrics_hs300['年化收益 (%)']:>11.2f}% {metrics_hs300['最大回撤 (%)']:>11.2f}% {metrics_hs300['夏普比率']:>12.3f}")

print()
print("=" * 80)
print("✅ 完整回测测试完成！")
print("=" * 80)
