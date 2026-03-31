#!/usr/bin/env python3
"""
模拟交易测试 - 生成调仓指令
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

import json
from datetime import datetime

print("=" * 80)
print("💼 锋哥量化策略 - 模拟交易测试")
print("=" * 80)
print(f"测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 测试 1：市场状态判断
print("【测试 1】当前市场状态判断")
print("-" * 80)

from market_state_classifier import MarketStateClassifier
import pandas as pd
import numpy as np

# 使用真实数据测试（从回测数据中获取）
backtest_dir = os.path.join(os.path.dirname(__file__), '../config/backtest_data')
backtest_hs300 = pd.read_excel(os.path.join(backtest_dir, 'hs300_backtest.xlsx'))
price_col = [col for col in backtest_hs300.columns if '每日收盘价' in col][0]
prices = pd.to_numeric(backtest_hs300[price_col], errors='coerce').dropna()
dates = pd.to_datetime(backtest_hs300['日期'], errors='coerce').dropna()
price_df = pd.DataFrame({'close': prices.values}, index=dates)

# 获取最新数据
latest_date = price_df.index[-1]
latest_price = price_df['close'].iloc[-1]
ma250 = price_df['close'].rolling(250).mean().iloc[-1]
ma250_slope = ma250 - price_df['close'].rolling(250).mean().iloc[-5]

# 模拟 RSI 和市场广度
rsi = 55.0  # 中性
breadth = 0.55  # 中性

classifier = MarketStateClassifier()
result = classifier.classify_with_details(
    price_data=price_df,
    rsi=rsi,
    market_breadth=breadth
)

print(f"最新日期：{latest_date.strftime('%Y-%m-%d')}")
print(f"沪深 300 点位：{latest_price:.2f}")
print(f"MA250: {ma250:.2f}")
print(f"MA250 斜率：{ma250_slope:.6f}")
print(f"RSI: {rsi}")
print(f"市场广度：{breadth:.2%}")
print()
print(f"📊 当前市场状态：{result['market_state']}")
print(f"   牛市条件：{result['bull_count']}/4")
print(f"   熊市条件：{result['bear_count']}/4")

print()

# 测试 2：生成投资组合
print("【测试 2】生成投资组合配置")
print("-" * 80)

from portfolio_constructor import PortfolioConstructor

# 加载股票池
stock_pools_dir = os.path.join(os.path.dirname(__file__), '../config/stock_pools')
with open(os.path.join(stock_pools_dir, 'bear_60.json'), 'r', encoding='utf-8') as f:
    bear_pool = json.load(f)

constructor = PortfolioConstructor()

# 根据市场状态选择股票池
market_state = result['market_state']
if market_state == '牛市':
    with open(os.path.join(stock_pools_dir, 'bull_177.json'), 'r', encoding='utf-8') as f:
        stock_pool_data = json.load(f)
elif market_state == '熊市':
    stock_pool_data = bear_pool
else:
    with open(os.path.join(stock_pools_dir, 'sideways_73.json'), 'r', encoding='utf-8') as f:
        stock_pool_data = json.load(f)

portfolio = constructor.generate_target_portfolio(
    market_state=market_state,
    stock_pool=stock_pool_data['stocks'][:20],  # 取前 20 支测试
    total_capital=1000000  # 100 万测试资金
)

print(f"市场状态：{market_state}")
print(f"目标仓位：{portfolio['target_position_ratio']:.1%}")
print(f"股票数量：{portfolio['target_stock_count']}")
print(f"现金比例：{portfolio['cash_ratio']:.1%}")
print(f"单只上限：{portfolio['risk_control']['single_stock_max']:.1%}")
print()

# 测试 3：生成调仓指令
print("【测试 3】生成调仓指令（模拟）")
print("-" * 80)

# 模拟当前持仓
current_positions = {
    '600519.SH': {'shares': 100, 'price': 1750.0},
    '000858.SZ': {'shares': 500, 'price': 140.0},
}

# 生成调仓建议
print(f"当前市场状态：{market_state}")
print(f"建议仓位：{portfolio['target_position_ratio']:.1%}")
print()
print("调仓建议:")
print(f"  1. 根据{market_state}配置，建议使用{portfolio['target_position_ratio']:.1%}仓位")
print(f"  2. 股票池：{stock_pool_data['name']}")
print(f"  3. 持仓股票数：{portfolio['target_stock_count']} 支")
print(f"  4. 单只上限：{portfolio['risk_control']['single_stock_max']:.1%}")
print(f"  5. 行业上限：{portfolio['risk_control']['industry_max']:.1%}")
print()

# 测试 4：获取实时价格（如果 OpenD 已连接）
print("【测试 4】获取实时价格")
print("-" * 80)

from data_loader import FutuDataLoader

loader = FutuDataLoader()
success, message = loader.connect()

if success:
    print(f"✅ 已连接到富途 OpenD")
    
    # 获取股票池价格
    test_stocks = bear_pool['stocks'][:5]  # 取前 5 支测试
    updated_stocks = loader.get_stock_pool_prices(test_stocks)
    
    print(f"获取到 {len(updated_stocks)} 支股票价格:")
    for stock in updated_stocks:
        print(f"  {stock['symbol']} {stock['name']}: ¥{stock.get('price', 'N/A')}")
    
    loader.disconnect()
else:
    print(f"⏳ OpenD 未连接：{message}")
    print(f"   使用模拟价格")

print()
print("=" * 80)
print("✅ 模拟交易测试完成！")
print("=" * 80)
