#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略回测系统 - 基于 Backtrader 的历史回测框架
支持多种策略回测和绩效分析
"""

import json
import backtrader as bt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from futu import *

CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
BACKTEST_RESULTS_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/backtest_results.json"

# ============ 策略定义 ============

class SMAStrategy(bt.Strategy):
    """双均线策略"""
    params = (
        ('fast_period', 5),
        ('slow_period', 20),
    )
    
    def __init__(self):
        self.fast_ma = bt.ind.SMA(period=self.p.fast_period)
        self.slow_ma = bt.ind.SMA(period=self.p.slow_period)
        self.crossover = bt.ind.CrossOver(self.fast_ma, self.slow_ma)
    
    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()

class RSIStrategy(bt.Strategy):
    """RSI 超买超卖策略"""
    params = (
        ('rsi_period', 14),
        ('oversold', 30),
        ('overbought', 70),
    )
    
    def __init__(self):
        self.rsi = bt.ind.RSI(period=self.p.rsi_period)
    
    def next(self):
        if not self.position:
            if self.rsi < self.p.oversold:
                self.buy()
        elif self.rsi > self.p.overbought:
            self.close()

class MACDStrategy(bt.Strategy):
    """MACD 策略"""
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
    )
    
    def __init__(self):
        self.macd = bt.ind.MACD(
            period_me1=self.p.fast_period,
            period_me2=self.p.slow_period,
            period_signal=self.p.signal_period
        )
        self.crossover = bt.ind.CrossOver(self.macd.macd, self.macd.signal)
    
    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()

# ============ 回测引擎 ============

def get_kline_data(symbol, market='HK'):
    """获取历史 K 线数据（使用 yfinance）"""
    try:
        import yfinance as yf
        
        if market == 'US':
            ticker = yf.Ticker(symbol)
        else:
            ticker = yf.Ticker(f"{symbol.replace('.HK', '')}.HK")
        
        hist = ticker.history(period='1y')
        
        if len(hist) > 0:
            df = hist.copy()
            df.columns = [c.lower() for c in df.columns]
            df['openinterest'] = 0
            return df[['open', 'high', 'low', 'close', 'volume', 'openinterest']]
        return None
    except Exception as e:
        print(f"获取 K 线失败 {symbol}: {e}")
        return None

def run_backtest(symbol, data, strategy_class, strategy_params, initial_cash=100000):
    """运行回测"""
    cerebro = bt.Cerebro()
    
    # 添加数据
    data_feed = bt.feeds.PandasData(dataname=data)
    cerebro.adddata(data_feed)
    
    # 添加策略
    cerebro.addstrategy(strategy_class, **strategy_params)
    
    # 设置资金
    cerebro.broker.setcash(initial_cash)
    
    # 设置手续费
    cerebro.broker.setcommission(commission=0.001)  # 0.1%
    
    # 设置仓位大小
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)
    
    # 运行回测
    initial_value = cerebro.broker.getvalue()
    cerebro.run()
    final_value = cerebro.broker.getvalue()
    
    # 计算绩效
    total_return = ((final_value - initial_value) / initial_value) * 100
    
    return {
        'initial_cash': initial_cash,
        'final_value': round(final_value, 2),
        'total_return_percent': round(total_return, 2),
        'profit_loss': round(final_value - initial_value, 2)
    }

def compare_strategies(symbol, data):
    """对比多个策略"""
    strategies = [
        {'name': 'SMA 双均线', 'class': SMAStrategy, 'params': {'fast_period': 5, 'slow_period': 20}},
        {'name': 'RSI 超买超卖', 'class': RSIStrategy, 'params': {'rsi_period': 14, 'oversold': 30, 'overbought': 70}},
        {'name': 'MACD', 'class': MACDStrategy, 'params': {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}},
        {'name': '买入持有', 'class': bt.strategies.SMA, 'params': {'period': 1}},  # 简单替代
    ]
    
    results = []
    for strat in strategies:
        try:
            result = run_backtest(symbol, data, strat['class'], strat['params'])
            result['strategy_name'] = strat['name']
            results.append(result)
        except Exception as e:
            print(f"回测失败 {strat['name']}: {e}")
    
    return results

def save_results(results):
    """保存回测结果"""
    with open(BACKTEST_RESULTS_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'last_updated': datetime.now().isoformat(),
            'results': results
        }, f, ensure_ascii=False, indent=2)

def send_feishu(message):
    import subprocess
    cmd = [
        "openclaw", "message", "send",
        "--channel", "feishu",
        "--target", "ou_636c8e8b7ad36d7fc28e6cf90c350fdd",
        "--message", message
    ]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"发送失败：{e}")

def run_all_backtests():
    """运行所有持仓股票的回测"""
    print(f"[{datetime.now()}] 开始策略回测...")
    
    portfolio = load_portfolio()
    all_results = []
    
    # 重点股票
    key_stocks = [
        ('GOOGL', 'US'),
        ('00883.HK', 'HK'),
        ('00700.HK', 'HK'),
        ('09988.HK', 'HK'),
    ]
    
    for symbol, market in key_stocks:
        print(f"\n回测 {symbol}...")
        data = get_kline_data(symbol.replace('.HK', ''), market)
        
        if data is not None and len(data) > 200:
            results = compare_strategies(symbol, data)
            for result in results:
                result['symbol'] = symbol
                all_results.append(result)
    
    # 保存结果
    save_results(all_results)
    
    # 发送报告
    report_lines = ["📈 策略回测报告", f"📅 {datetime.now().strftime('%Y-%m-%d')}", ""]
    
    for result in all_results[:8]:  # 显示前 8 个
        emoji = "🟢" if result['total_return_percent'] > 0 else "🔴"
        report_lines.append(f"{emoji} {result['symbol']} - {result['strategy_name']}")
        report_lines.append(f"   收益率：{result['total_return_percent']:+.1f}% | 盈亏：${result['profit_loss']:+,.0f}")
        report_lines.append("")
    
    send_feishu("\n".join(report_lines))
    
    print(f"\n✅ 完成 {len(all_results)} 次回测")
    return True

def load_portfolio():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

if __name__ == "__main__":
    success = run_all_backtests()
    exit(0 if success else 1)
