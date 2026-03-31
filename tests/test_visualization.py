#!/usr/bin/env python3
"""
可视化测试 - 生成对比图表
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import pandas as pd
import numpy as np
from datetime import datetime

print("=" * 80)
print("📈 锋哥量化策略 - 可视化报告生成")
print("=" * 80)
print(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 加载回测数据
print("【步骤 1】加载回测数据")
backtest_dir = os.path.join(os.path.dirname(__file__), '../config/backtest_data')

backtest_177 = pd.read_excel(os.path.join(backtest_dir, 'backtest_177.xlsx'))
backtest_60 = pd.read_excel(os.path.join(backtest_dir, 'backtest_60.xlsx'))
backtest_hs300 = pd.read_excel(os.path.join(backtest_dir, 'hs300_backtest.xlsx'))

print(f"✅ 177 支池：{len(backtest_177)} 行")
print(f"✅ 60 支池：{len(backtest_60)} 行")
print(f"✅ 沪深 300: {len(backtest_hs300)} 行")
print()

# 提取价格数据
def extract_prices(df):
    price_col = [col for col in df.columns if '每日收盘价' in col or col == 'Price'][0]
    prices = pd.to_numeric(df[price_col], errors='coerce').dropna()
    return prices

prices_177 = extract_prices(backtest_177)
prices_60 = extract_prices(backtest_60)
prices_hs300 = extract_prices(backtest_hs300)

# 归一化（以初始值为 100）
norm_177 = (prices_177 / prices_177.iloc[0]) * 100
norm_60 = (prices_60 / prices_60.iloc[0]) * 100
norm_hs300 = (prices_hs300 / prices_hs300.iloc[0]) * 100

print("【步骤 2】计算绩效指标")

def calculate_metrics(prices, name):
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

metrics_177 = calculate_metrics(prices_177, '177 支池')
metrics_60 = calculate_metrics(prices_60, '60 支池')
metrics_hs300 = calculate_metrics(prices_hs300, '沪深 300')

print()
print("【步骤 3】生成绩效汇总表")
print()
print(f"{'组合':<15} {'累计收益':>12} {'年化收益':>12} {'最大回撤':>12} {'夏普比率':>12}")
print("-" * 65)
print(f"{metrics_177['组合']:<15} {metrics_177['累计收益 (%)']:>11.2f}% {metrics_177['年化收益 (%)']:>11.2f}% {metrics_177['最大回撤 (%)']:>11.2f}% {metrics_177['夏普比率']:>12.3f}")
print(f"{metrics_60['组合']:<15} {metrics_60['累计收益 (%)']:>11.2f}% {metrics_60['年化收益 (%)']:>11.2f}% {metrics_60['最大回撤 (%)']:>11.2f}% {metrics_60['夏普比率']:>12.3f}")
print(f"{metrics_hs300['组合']:<15} {metrics_hs300['累计收益 (%)']:>11.2f}% {metrics_hs300['年化收益 (%)']:>11.2f}% {metrics_hs300['最大回撤 (%)']:>11.2f}% {metrics_hs300['夏普比率']:>12.3f}")

print()
print("【步骤 4】生成可视化图表（文本版）")
print()

# 净值曲线对比（文本版）
print("净值曲线对比（归一化=100）:")
print("-" * 60)

final_177 = norm_177.iloc[-1]
final_60 = norm_60.iloc[-1]
final_hs300 = norm_hs300.iloc[-1]

def draw_bar(name, value, max_value, width=50):
    bar_length = int((value / max_value) * width)
    bar = '█' * bar_length + '░' * (width - bar_length)
    return f"{name:<10} |{bar}| {value:.1f}"

max_final = max(final_177, final_60, final_hs300, 100)
print(draw_bar("177 支池", final_177, max_final))
print(draw_bar("60 支池", final_60, max_final))
print(draw_bar("沪深 300", final_hs300, max_final))

print()

# 回撤对比
print("最大回撤对比（越小越好）:")
print("-" * 60)

dd_177 = abs(metrics_177['最大回撤 (%)'])
dd_60 = abs(metrics_60['最大回撤 (%)'])
dd_hs300 = abs(metrics_hs300['最大回撤 (%)'])

max_dd = max(dd_177, dd_60, dd_hs300)
print(draw_bar("177 支池", dd_177, max_dd))
print(draw_bar("60 支池", dd_60, max_dd))
print(draw_bar("沪深 300", dd_hs300, max_dd))

print()

# 夏普比率对比
print("夏普比率对比（越高越好）:")
print("-" * 60)

sharpe_177 = metrics_177['夏普比率']
sharpe_60 = metrics_60['夏普比率']
sharpe_hs300 = metrics_hs300['夏普比率']

max_sharpe = max(sharpe_177, sharpe_60, sharpe_hs300, 0.5)
print(draw_bar("177 支池", sharpe_177, max_sharpe))
print(draw_bar("60 支池", sharpe_60, max_sharpe))
print(draw_bar("沪深 300", sharpe_hs300, max_sharpe))

print()
print("=" * 80)
print("✅ 可视化报告生成完成！")
print("=" * 80)
print()
print("💡 提示：完整图表版请运行:")
print("   python3 src/visualize.py")
