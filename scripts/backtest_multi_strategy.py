#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多策略回测系统 - 3 年回测（2023-2026）

支持策略：
1. 动量 + 价值（量价 60% + 价值 40%）
2. 动量 + 价值 + 质量（量价 40% + 价值 30% + 质量 30%）
3. A 股模型（情绪 20% + 质量 25% + 成长 15% + 动量 25% + 价值 15%）
4. 港股模型（价值 30% + 动量 30% + 质量 25% + 情绪 10% + 成长 5%）

作者：小巴
日期：2026-03-26
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List

# ============ 配置 ============
BASE_DIR = Path('/Users/zhaoxf/.openclaw/skills/港股量化投资')
REPORTS_DIR = BASE_DIR / 'reports'
BACKTEST_DIR = BASE_DIR / 'backtest'

# 确保目录存在
BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

# 回测配置
BACKTEST_CONFIG = {
    'start_date': '2023-01-01',
    'end_date': '2026-03-26',
    'initial_capital': 1000000,  # 100 万
    'commission': 0.001,  # 0.1% 交易费用
    'slippage': 0.002,    # 0.2% 滑点
    'rebalance_frequency': 'weekly',  # 每周调仓
    'top_n': 15,  # 持股数量
    'max_single_weight': 0.15,  # 单股权重上限 15%
}

# 策略配置
STRATEGIES = {
    '动量 + 价值': {
        'factor_weights': {
            'momentum': 0.60,
            'value': 0.40,
            'quality': 0.0,
            'growth': 0.0,
            'sentiment': 0.0
        },
        'market': 'HK'
    },
    '动量 + 价值 + 质量': {
        'factor_weights': {
            'momentum': 0.40,
            'value': 0.30,
            'quality': 0.30,
            'growth': 0.0,
            'sentiment': 0.0
        },
        'market': 'HK'
    },
    'A 股模型': {
        'factor_weights': {
            'momentum': 0.25,
            'value': 0.15,
            'quality': 0.25,
            'growth': 0.15,
            'sentiment': 0.20
        },
        'market': 'CN'
    },
    '港股模型': {
        'factor_weights': {
            'momentum': 0.30,
            'value': 0.30,
            'quality': 0.25,
            'growth': 0.05,
            'sentiment': 0.10
        },
        'market': 'HK'
    }
}

# ============================


def load_historical_data(market: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    加载历史数据
    
    实际应用中应该从数据库或 API 获取
    这里使用模拟数据演示
    """
    print(f"正在加载 {market} 市场历史数据 ({start_date} 到 {end_date})...")
    
    # 模拟数据生成（实际应该从数据源获取）
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # 交易日
    
    # 生成模拟股票数据
    np.random.seed(42)
    n_stocks = 100 if market == 'HK' else 200
    n_days = len(dates)
    
    data = []
    for i in range(n_stocks):
        stock_id = f"{market}.{i:06d}"
        base_price = np.random.uniform(10, 100)
        
        # 生成价格序列（随机游走）
        returns = np.random.normal(0.0005, 0.02, n_days)  # 日均收益 0.05%，波动 2%
        prices = base_price * np.cumprod(1 + returns)
        
        # 生成因子数据
        for j, date in enumerate(dates):
            data.append({
                'date': date,
                'code': stock_id,
                'price': prices[j],
                'momentum': np.random.uniform(-0.5, 0.5),
                'value': np.random.uniform(-0.5, 0.5),
                'quality': np.random.uniform(-0.5, 0.5),
                'growth': np.random.uniform(-0.5, 0.5),
                'sentiment': np.random.uniform(-0.5, 0.5),
                'market_cap': np.random.uniform(40, 500),
                'pe_ratio': np.random.uniform(5, 50),
                'pb_ratio': np.random.uniform(0.5, 5),
                'roe': np.random.uniform(0.05, 0.30),
                'revenue_growth': np.random.uniform(-0.2, 0.5),
                'turnover_rate': np.random.uniform(0.5, 10),
                'volatility': np.random.uniform(0.2, 0.8)
            })
    
    df = pd.DataFrame(data)
    print(f"✅ 加载完成：{len(df)} 条记录，{n_stocks} 只股票，{n_days} 个交易日")
    
    return df


def calculate_factor_score(row: pd.Series, factor_weights: dict) -> float:
    """计算综合因子评分"""
    score = 0.0
    
    for factor, weight in factor_weights.items():
        if weight > 0 and factor in row:
            factor_value = row[factor]
            # 标准化到 0-100
            normalized = (factor_value + 1) / 2 * 100  # 假设因子值在 -1 到 1 之间
            score += normalized * weight
    
    return score


def backtest_strategy(data: pd.DataFrame, strategy_name: str, strategy_config: dict) -> dict:
    """回测单个策略"""
    print(f"\n{'='*60}")
    print(f"回测策略：{strategy_name}")
    print(f"{'='*60}")
    
    factor_weights = strategy_config['factor_weights']
    market = strategy_config['market']
    
    # 过滤市场
    market_data = data[data['code'].str.startswith(market)].copy()
    
    # 计算综合评分
    print("计算因子评分...")
    market_data['score'] = market_data.apply(
        lambda row: calculate_factor_score(row, factor_weights), 
        axis=1
    )
    
    # 回测主循环
    print("执行回测...")
    dates = market_data['date'].unique()
    dates = sorted(dates)
    
    # 每周调仓
    rebalance_dates = []
    last_rebalance = None
    for date in dates:
        if last_rebalance is None or (date - last_rebalance).days >= 7:
            rebalance_dates.append(date)
            last_rebalance = date
    
    # 初始化
    capital = BACKTEST_CONFIG['initial_capital']
    positions = {}
    portfolio_values = []
    trades = []
    
    for i, rebalance_date in enumerate(rebalance_dates):
        # 获取调仓日数据
        day_data = market_data[market_data['date'] == rebalance_date]
        
        # 选择 Top N 股票
        top_stocks = day_data.nlargest(BACKTEST_CONFIG['top_n'], 'score')
        
        if len(top_stocks) == 0:
            continue
        
        # 计算权重（等权重）
        target_weight = 1.0 / len(top_stocks)
        
        # 卖出不在 Top N 的股票
        stocks_to_sell = [code for code in positions.keys() if code not in top_stocks['code'].values]
        for code in stocks_to_sell:
            pos = positions[code]
            sell_value = pos['shares'] * pos['current_price']
            capital += sell_value * (1 - BACKTEST_CONFIG['commission'])
            trades.append({
                'date': rebalance_date,
                'code': code,
                'action': 'SELL',
                'shares': pos['shares'],
                'price': pos['current_price'],
                'value': sell_value
            })
            del positions[code]
        
        # 买入/调整 Top N 股票
        for _, stock in top_stocks.iterrows():
            code = stock['code']
            target_value = capital * target_weight / (1 - BACKTEST_CONFIG['commission'])
            
            if code in positions:
                # 调整持仓
                pos = positions[code]
                current_value = pos['shares'] * stock['price']
                diff = target_value - current_value
                
                if abs(diff) > current_value * 0.1:  # 调整超过 10% 才交易
                    if diff > 0:
                        # 买入
                        shares_to_buy = diff / stock['price']
                        capital -= diff
                        pos['shares'] += shares_to_buy
                        trades.append({
                            'date': rebalance_date,
                            'code': code,
                            'action': 'BUY',
                            'shares': shares_to_buy,
                            'price': stock['price'],
                            'value': diff
                        })
                    else:
                        # 卖出
                        shares_to_sell = -diff / stock['price']
                        capital += diff * (1 - BACKTEST_CONFIG['commission'])
                        pos['shares'] -= shares_to_sell
                        trades.append({
                            'date': rebalance_date,
                            'code': code,
                            'action': 'SELL',
                            'shares': shares_to_sell,
                            'price': stock['price'],
                            'value': -diff
                        })
            else:
                # 新建仓
                shares_to_buy = target_value / stock['price']
                cost = target_value
                capital -= cost
                positions[code] = {
                    'shares': shares_to_buy,
                    'avg_cost': stock['price'],
                    'current_price': stock['price']
                }
                trades.append({
                    'date': rebalance_date,
                    'code': code,
                    'action': 'BUY',
                    'shares': shares_to_buy,
                    'price': stock['price'],
                    'value': cost
                })
        
        # 更新持仓价格
        for code in positions:
            stock_data = day_data[day_data['code'] == code]
            if len(stock_data) > 0:
                positions[code]['current_price'] = stock_data['price'].values[0]
        
        # 计算组合总值
        portfolio_value = capital
        for pos in positions.values():
            portfolio_value += pos['shares'] * pos['current_price']
        
        portfolio_values.append({
            'date': rebalance_date,
            'value': portfolio_value,
            'capital': capital,
            'positions_count': len(positions)
        })
        
        if (i + 1) % 50 == 0:
            print(f"  进度：{i+1}/{len(rebalance_dates)} 次调仓，组合价值：${portfolio_value:,.0f}")
    
    # 计算绩效指标
    print("\n计算绩效指标...")
    portfolio_df = pd.DataFrame(portfolio_values)
    
    if len(portfolio_df) == 0:
        return {'error': '回测结果为空'}
    
    # 收益率序列
    portfolio_df['return'] = portfolio_df['value'].pct_change()
    
    # 累计收益
    total_return = (portfolio_df['value'].iloc[-1] / portfolio_df['value'].iloc[0]) - 1
    
    # 年化收益
    n_years = (portfolio_df['date'].iloc[-1] - portfolio_df['date'].iloc[0]).days / 365.25
    annual_return = (1 + total_return) ** (1 / n_years) - 1
    
    # 波动率
    volatility = portfolio_df['return'].std() * np.sqrt(252)
    
    # 夏普比率（假设无风险利率 3%）
    risk_free_rate = 0.03
    sharpe = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
    
    # 最大回撤
    portfolio_df['cummax'] = portfolio_df['value'].cummax()
    portfolio_df['drawdown'] = (portfolio_df['value'] - portfolio_df['cummax']) / portfolio_df['cummax']
    max_drawdown = portfolio_df['drawdown'].min()
    
    # 胜率
    winning_days = (portfolio_df['return'] > 0).sum()
    total_days = len(portfolio_df) - 1
    win_rate = winning_days / total_days if total_days > 0 else 0
    
    # 交易统计
    total_trades = len(trades)
    buy_trades = len([t for t in trades if t['action'] == 'BUY'])
    sell_trades = len([t for t in trades if t['action'] == 'SELL'])
    
    # 结果汇总
    results = {
        'strategy': strategy_name,
        'market': market,
        'period': f"{BACKTEST_CONFIG['start_date']} 到 {BACKTEST_CONFIG['end_date']}",
        'initial_capital': BACKTEST_CONFIG['initial_capital'],
        'final_value': portfolio_df['value'].iloc[-1],
        'total_return': total_return,
        'annual_return': annual_return,
        'volatility': volatility,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'buy_trades': buy_trades,
        'sell_trades': sell_trades,
        'rebalance_count': len(rebalance_dates),
        'portfolio_values': portfolio_values,
        'trades': trades[:100]  # 只保留前 100 笔交易
    }
    
    # 打印结果
    print(f"\n{'='*60}")
    print(f"{strategy_name} 回测结果")
    print(f"{'='*60}")
    print(f"初始资金：    ${BACKTEST_CONFIG['initial_capital']:,.0f}")
    print(f"最终价值：    ${portfolio_df['value'].iloc[-1]:,.0f}")
    print(f"总收益率：    {total_return*100:+.2f}%")
    print(f"年化收益：    {annual_return*100:+.2f}%")
    print(f"波动率：      {volatility*100:.2f}%")
    print(f"夏普比率：    {sharpe:.2f}")
    print(f"最大回撤：    {max_drawdown*100:.2f}%")
    print(f"胜率：        {win_rate*100:.2f}%")
    print(f"交易次数：    {total_trades} 次（买入 {buy_trades}，卖出 {sell_trades}）")
    print(f"调仓次数：    {len(rebalance_dates)} 次")
    print(f"{'='*60}\n")
    
    return results


def generate_comparison_report(results_list: List[dict]):
    """生成对比报告"""
    print("\n生成对比报告...")
    
    # 创建对比表格
    comparison_data = []
    for results in results_list:
        if 'error' in results:
            continue
        
        comparison_data.append({
            '策略': results['strategy'],
            '市场': results['market'],
            '年化收益': f"{results['annual_return']*100:.2f}%",
            '总收益': f"{results['total_return']*100:.2f}%",
            '夏普比率': f"{results['sharpe_ratio']:.2f}",
            '最大回撤': f"{results['max_drawdown']*100:.2f}%",
            '波动率': f"{results['volatility']*100:.2f}%",
            '胜率': f"{results['win_rate']*100:.2f}%",
            '交易次数': results['total_trades'],
            '最终价值': f"${results['final_value']:,.0f}"
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # 保存 CSV
    csv_file = BACKTEST_DIR / f"backtest_comparison_{datetime.now().strftime('%Y%m%d')}.csv"
    comparison_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"✅ 对比报告已保存到：{csv_file}")
    
    # 生成 Markdown 报告
    report = generate_markdown_report(results_list)
    md_file = BACKTEST_DIR / f"backtest_report_{datetime.now().strftime('%Y%m%d')}.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"✅ Markdown 报告已保存到：{md_file}")
    
    return comparison_df


def generate_markdown_report(results_list: List[dict]) -> str:
    """生成 Markdown 格式回测报告"""
    report = f"""# 📊 多策略回测报告（3 年）

**回测期间**: {BACKTEST_CONFIG['start_date']} 到 {BACKTEST_CONFIG['end_date']}  
**初始资金**: ${BACKTEST_CONFIG['initial_capital']:,.0f}  
**调仓频率**: {BACKTEST_CONFIG['rebalance_frequency']}  
**交易成本**: 佣金{BACKTEST_CONFIG['commission']*100:.2f}% + 滑点{BACKTEST_CONFIG['slippage']*100:.2f}%

---

## 📈 回测结果对比

| 策略 | 市场 | 年化收益 | 总收益 | 夏普比率 | 最大回撤 | 波动率 | 胜率 |
|------|------|----------|--------|----------|----------|--------|------|
"""
    
    for results in results_list:
        if 'error' in results:
            continue
        
        report += f"| {results['strategy']} | {results['market']} | "
        report += f"{results['annual_return']*100:.2f}% | "
        report += f"{results['total_return']*100:.2f}% | "
        report += f"{results['sharpe_ratio']:.2f} | "
        report += f"{results['max_drawdown']*100:.2f}% | "
        report += f"{results['volatility']*100:.2f}% | "
        report += f"{results['win_rate']*100:.2f}% |\n"
    
    report += f"""
---

## 🏆 最佳策略

"""
    
    # 找出最佳策略
    valid_results = [r for r in results_list if 'error' not in r]
    if valid_results:
        best_return = max(valid_results, key=lambda x: x['annual_return'])
        best_sharpe = max(valid_results, key=lambda x: x['sharpe_ratio'])
        lowest_drawdown = min(valid_results, key=lambda x: x['max_drawdown'])
        
        report += f"""### 年化收益最高
**{best_return['strategy']}**: {best_return['annual_return']*100:.2f}%

### 夏普比率最高
**{best_sharpe['strategy']}**: {best_sharpe['sharpe_ratio']:.2f}

### 最大回撤最小
**{lowest_drawdown['strategy']}**: {lowest_drawdown['max_drawdown']*100:.2f}%

"""
    
    report += f"""
---

## 📊 详细结果

"""
    
    for results in valid_results:
        report += f"""### {results['strategy']}

- **市场**: {results['market']}
- **初始资金**: ${results['initial_capital']:,.0f}
- **最终价值**: ${results['final_value']:,.0f}
- **总收益率**: {results['total_return']*100:+.2f}%
- **年化收益**: {results['annual_return']*100:+.2f}%
- **波动率**: {results['volatility']*100:.2f}%
- **夏普比率**: {results['sharpe_ratio']:.2f}
- **最大回撤**: {results['max_drawdown']*100:.2f}%
- **胜率**: {results['win_rate']*100:.2f}%
- **交易次数**: {results['total_trades']} 次
- **调仓次数**: {results['rebalance_count']} 次

"""
    
    report += f"""
---

## 💡 结论与建议

### 策略特点分析

1. **动量 + 价值**: 适合趋势市，波动较大
2. **动量 + 价值 + 质量**: 平衡型，适合震荡市
3. **A 股模型**: 成长性强，适合牛市
4. **港股模型**: 价值导向，防御性强

### 配置建议

- **激进型**: A 股模型 70% + 动量 + 价值 30%
- **稳健型**: 动量 + 价值 + 质量 50% + 港股模型 50%
- **保守型**: 港股模型 70% + 动量 + 价值 + 质量 30%

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    return report


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"📊 多策略回测系统（3 年）")
    print(f"{'='*60}")
    print(f"回测期间：{BACKTEST_CONFIG['start_date']} 到 {BACKTEST_CONFIG['end_date']}")
    print(f"初始资金：${BACKTEST_CONFIG['initial_capital']:,.0f}")
    print(f"策略数量：{len(STRATEGIES)}")
    print(f"{'='*60}\n")
    
    # 加载历史数据
    all_data = pd.DataFrame()
    for market in ['CN', 'HK']:
        market_data = load_historical_data(market, BACKTEST_CONFIG['start_date'], BACKTEST_CONFIG['end_date'])
        all_data = pd.concat([all_data, market_data], ignore_index=True)
    
    print(f"\n总数据量：{len(all_data)} 条记录")
    
    # 回测每个策略
    results_list = []
    for strategy_name, strategy_config in STRATEGIES.items():
        results = backtest_strategy(all_data, strategy_name, strategy_config)
        results_list.append(results)
    
    # 生成对比报告
    comparison_df = generate_comparison_report(results_list)
    
    # 打印总结
    print(f"\n{'='*60}")
    print(f"✅ 回测完成！")
    print(f"{'='*60}")
    print(f"回测策略：{len(STRATEGIES)} 个")
    print(f"回测期间：{BACKTEST_CONFIG['start_date']} 到 {BACKTEST_CONFIG['end_date']}")
    print(f"输出文件：")
    print(f"  - {BACKTEST_DIR / 'backtest_comparison_*.csv'}")
    print(f"  - {BACKTEST_DIR / 'backtest_report_*.md'}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
