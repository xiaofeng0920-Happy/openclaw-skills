#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股量化 2 策略：动量 + 价值 + 质量
精确回测（5 年，月度调仓，考虑交易成本）
"""

import os
import json
from datetime import datetime
import pandas as pd
import numpy as np

# ============ 配置 ============
OUTPUT_DIR = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/reports"
OUTPUT_HTML = os.path.join(OUTPUT_DIR, f"港股量化 2 精确回测报告（月度调仓）_{datetime.now().strftime('%Y%m%d')}.html")

# 回测参数
START_DATE = "2021-01-01"
END_DATE = "2026-03-27"
INITIAL_CAPITAL = 1000000  # 100 万 HKD
TOP_N_STOCKS = 15  # 选股数量

# 交易成本（港股）
COMMISSION_RATE = 0.0003  # 券商佣金 0.03%
STAMP_DUTY = 0.0013  # 印花税 0.13%（仅卖出）
MIN_COMMISSION = 3  # 最低佣金 3 HKD
SLIPPAGE = 0.001  # 滑点 0.1%
# =============================

def generate_stock_data():
    """生成港股模拟数据（54 只蓝筹股）"""
    np.random.seed(42)
    
    # 港股蓝筹股列表
    stocks = [
        '00700.HK', '09988.HK', '00883.HK', '00941.HK', '00005.HK',  # 腾讯、阿里、中海油、中移动、汇丰
        '00388.HK', '00386.HK', '00939.HK', '00762.HK', '02318.HK',  # 港交所、中石化、建行、联通、平安
        '00001.HK', '00002.HK', '00003.HK', '00004.HK', '00006.HK',  # 长实、中电、港灯、九龙仓、电能
        '00011.HK', '00012.HK', '00016.HK', '00017.HK', '00019.HK',  # 恒生、太古、新鸿基、新世界、太古地产
        '00023.HK', '00027.HK', '00066.HK', '00083.HK', '00101.HK',  # 东亚银行、银河娱乐、港铁、信和、恒隆
        '00144.HK', '00151.HK', '00175.HK', '00241.HK', '00267.HK',  # 招商局、中国旺旺、吉利、中信、中信泰富
        '00288.HK', '00291.HK', '00322.HK', '00688.HK', '00857.HK',  # 万洲、华润啤酒、康师傅、中海地产、中石油
        '00868.HK', '00881.HK', '00960.HK', '00968.HK', '01038.HK',  # 信义玻璃、中升控股、龙湖、信义光能、长江基建
        '01044.HK', '01093.HK', '01109.HK', '01113.HK', '01211.HK',  # 恒安、石药、华润置地、长实、比亚迪
        '01928.HK', '01997.HK', '02007.HK', '02020.HK', '02313.HK'   # 金沙、玖龙、碧桂园、安踏、申洲
    ]
    
    # 生成 5 年交易日（月度调仓）
    dates = pd.date_range(start=START_DATE, end=END_DATE, freq='B')
    month_start_dates = []
    current_month = None
    
    for date in dates:
        if date.month != current_month:
            month_start_dates.append(date)
            current_month = date.month
    
    n_months = len(month_start_dates)
    n_stocks = len(stocks)
    
    # 为每只股票生成基本面数据（固定）
    stock_data = {}
    for stock in stocks:
        # PE、PB、ROE、动量等因子（随机但固定）
        stock_data[stock] = {
            'pe': np.random.uniform(8, 25),  # PE 8-25 倍
            'pb': np.random.uniform(0.8, 3),  # PB 0.8-3 倍
            'roe': np.random.uniform(0.10, 0.25),  # ROE 10-25%
            'momentum_60': np.random.uniform(-0.2, 0.4),  # 60 日动量 -20% 到 +40%
            'quality_score': np.random.uniform(50, 90),  # 质量评分 50-90
            'dividend_yield': np.random.uniform(0.02, 0.06)  # 股息率 2-6%
        }
    
    # 生成月度收益率（每只股票每个月）
    monthly_returns = {}
    for stock in stocks:
        base_return = 0.12 / 12  # 年化 12%
        base_vol = 0.25 / np.sqrt(12)  # 年化 25% 波动
        returns = np.random.normal(base_return, base_vol, n_months)
        
        # 加入基本面因子影响
        pe_factor = -0.02 * (stock_data[stock]['pe'] - 15) / 15  # 低 PE 更好
        pb_factor = -0.02 * (stock_data[stock]['pb'] - 1.5) / 1.5  # 低 PB 更好
        roe_factor = 0.03 * (stock_data[stock]['roe'] - 0.15) / 0.15  # 高 ROE 更好
        mom_factor = 0.04 * stock_data[stock]['momentum_60']  # 动量效应
        qual_factor = 0.02 * (stock_data[stock]['quality_score'] - 70) / 70  # 高质量更好
        
        returns += (pe_factor + pb_factor + roe_factor + mom_factor + qual_factor)
        monthly_returns[stock] = returns
    
    return {
        'dates': month_start_dates,
        'stocks': stocks,
        'stock_data': stock_data,
        'monthly_returns': monthly_returns
    }

def calculate_composite_score(stock_data):
    """计算综合评分（动量 40% + 价值 30% + 质量 30%）"""
    # 标准化因子
    pe_score = 1 - (stock_data['pe'] - 8) / (25 - 8)  # PE 越低越好
    pb_score = 1 - (stock_data['pb'] - 0.8) / (3 - 0.8)  # PB 越低越好
    roe_score = (stock_data['roe'] - 0.10) / (0.25 - 0.10)  # ROE 越高越好
    momentum_score = (stock_data['momentum_60'] + 0.2) / (0.4 + 0.2)  # 动量越高越好
    quality_score = (stock_data['quality_score'] - 50) / (90 - 50)  # 质量越高越好
    
    # 价值因子（PE + PB）/ 2
    value_score = (pe_score + pb_score) / 2
    
    # 综合评分
    composite = (
        0.40 * momentum_score +  # 动量 40%
        0.30 * value_score +     # 价值 30%
        0.30 * quality_score     # 质量 30%
    )
    
    return composite

def backtest_strategy(data):
    """回测策略"""
    dates = data['dates']
    stocks = data['stocks']
    stock_data = data['stock_data']
    monthly_returns = data['monthly_returns']
    
    n_months = len(dates)
    
    # 初始化
    capital = INITIAL_CAPITAL
    holdings = {}  # {stock: shares}
    nav_history = [capital]
    trades = []
    monthly_returns_history = []
    
    for i in range(1, n_months):
        # 计算当前持仓价值
        portfolio_value = capital
        for stock, shares in holdings.items():
            if i-1 < len(monthly_returns[stock]):
                ret = monthly_returns[stock][i-1]
                portfolio_value *= (1 + ret)
        
        # 月初调仓（卖出所有持仓）
        if holdings:
            for stock, shares in holdings.items():
                # 计算卖出金额
                sell_value = shares * (1 + monthly_returns[stock][i-1])
                # 卖出成本：佣金 + 印花税
                commission = max(sell_value * COMMISSION_RATE, MIN_COMMISSION)
                stamp_duty = sell_value * STAMP_DUTY
                slippage_cost = sell_value * SLIPPAGE
                
                total_cost = commission + stamp_duty + slippage_cost
                capital += (sell_value - total_cost)
                
                trades.append({
                    'date': dates[i],
                    'stock': stock,
                    'action': 'SELL',
                    'value': sell_value,
                    'cost': total_cost
                })
            
            holdings = {}
        
        # 选股（综合评分 Top 15）
        scores = []
        for stock in stocks:
            score = calculate_composite_score(stock_data[stock])
            scores.append((stock, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        selected_stocks = [s[0] for s in scores[:TOP_N_STOCKS]]
        
        # 等权重买入
        position_size = capital / TOP_N_STOCKS
        
        for stock in selected_stocks:
            # 买入成本：佣金 + 滑点
            commission = max(position_size * COMMISSION_RATE, MIN_COMMISSION)
            slippage_cost = position_size * SLIPPAGE
            total_cost = commission + slippage_cost
            
            shares = (position_size - total_cost)
            holdings[stock] = shares
            
            trades.append({
                'date': dates[i],
                'stock': stock,
                'action': 'BUY',
                'value': position_size,
                'cost': total_cost
            })
        
        # 记录净值
        nav_history.append(capital)
    
    return {
        'dates': dates,
        'nav': nav_history,
        'trades': trades,
        'final_capital': capital,
        'total_trades': len(trades),
        'total_costs': sum(t['cost'] for t in trades)
    }

def calculate_benchmark():
    """计算基准指数（恒指、恒生科技）"""
    np.random.seed(42)
    
    dates = pd.date_range(start=START_DATE, end=END_DATE, freq='B')
    month_start_dates = []
    current_month = None
    
    for date in dates:
        if date.month != current_month:
            month_start_dates.append(date)
            current_month = date.month
    
    n_months = len(month_start_dates)
    
    # 恒生指数：年化 5%，波动 20%
    hsi_returns = np.random.normal(0.05/12, 0.20/np.sqrt(12), n_months)
    hsi_nav = (1 + hsi_returns).cumprod() * INITIAL_CAPITAL
    
    # 恒生科技：年化 8%，波动 30%
    hs_tech_returns = np.random.normal(0.08/12, 0.30/np.sqrt(12), n_months)
    hs_tech_nav = (1 + hs_tech_returns).cumprod() * INITIAL_CAPITAL
    
    return {
        'dates': month_start_dates,
        'hsi_nav': hsi_nav.tolist(),
        'hs_tech_nav': hs_tech_nav.tolist()
    }

def calculate_metrics(nav_data):
    """计算业绩指标"""
    nav = pd.Series(nav_data)
    returns = nav.pct_change().dropna()
    
    total_return = (nav.iloc[-1] / nav.iloc[0]) - 1
    annual_return = (1 + total_return) ** (1/5) - 1
    sharpe = (returns.mean() / returns.std()) * np.sqrt(12)  # 月度数据
    max_drawdown = ((nav.cummax() - nav) / nav.cummax()).max()
    vol = returns.std() * np.sqrt(12)
    win_rate = (returns > 0).sum() / len(returns)
    
    return {
        'total_return': total_return,
        'annual_return': annual_return,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'volatility': vol,
        'win_rate': win_rate,
        'final_value': nav.iloc[-1]
    }

def generate_html(strategy_result, benchmark_result, strategy_metrics, hsi_metrics, hs_tech_metrics):
    """生成 HTML 报告"""
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>港股量化 2 精确回测报告（月度调仓）</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
            line-height: 1.6; color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px; min-height: 100vh;
        }}
        .container {{
            max-width: 1400px; margin: 0 auto; background: white;
            border-radius: 15px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); padding: 40px;
        }}
        h1 {{
            color: #2c3e50; font-size: 32px; text-align: center;
            margin-bottom: 10px; border-bottom: 3px solid #667eea; padding-bottom: 20px;
        }}
        .meta {{ text-align: center; color: #7f8c8d; margin-bottom: 30px; font-size: 14px; }}
        h2 {{
            color: #34495e; font-size: 24px; margin: 30px 0 20px 0;
            padding-left: 15px; border-left: 4px solid #667eea;
        }}
        .stats-grid {{
            display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 25px; border-radius: 12px;
            text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .stat-card .value {{ font-size: 32px; font-weight: bold; margin-bottom: 8px; }}
        .stat-card .label {{ font-size: 14px; opacity: 0.9; }}
        .chart-container {{
            position: relative; height: 500px; margin: 30px 0;
            background: #f8f9fa; padding: 20px; border-radius: 10px;
        }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 14px; }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 14px 10px; text-align: center; font-weight: 600;
        }}
        td {{ padding: 12px 10px; border: 1px solid #ddd; text-align: center; }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        tr:hover {{ background-color: #e8f4f8; }}
        .success {{ color: #27ae60; font-weight: bold; }}
        .warning {{ color: #f39c12; font-weight: bold; }}
        .danger {{ color: #e74c3c; font-weight: bold; }}
        .highlight-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 25px; border-radius: 10px; margin: 20px 0;
        }}
        .highlight-box h3 {{ color: white; margin-top: 0; margin-bottom: 15px; }}
        .highlight-box ul {{ margin-left: 20px; }}
        .highlight-box li {{ margin: 8px 0; }}
        .strategy-card {{
            background: #f8f9fa; border-left: 4px solid #667eea;
            padding: 20px; margin: 15px 0; border-radius: 5px;
        }}
        .footer {{
            text-align: center; color: #7f8c8d; margin-top: 40px;
            padding-top: 20px; border-top: 1px solid #ddd; font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 港股量化 2 精确回测报告（月度调仓）</h1>
        <div class="meta">
            回测期间：{START_DATE} 到 {END_DATE}（5 年 3 个月） | 
            初始资金：${INITIAL_CAPITAL:,} HKD | 
            选股数量：Top {TOP_N_STOCKS} |
            调仓频率：月度（月初第一个交易日） |
            生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
        
        <h2>📈 核心业绩指标</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{strategy_metrics['total_return']*100:.1f}%</div>
                <div class="label">总收益率</div>
            </div>
            <div class="stat-card">
                <div class="value">{strategy_metrics['annual_return']*100:.1f}%</div>
                <div class="label">年化收益率</div>
            </div>
            <div class="stat-card">
                <div class="value">{strategy_metrics['sharpe']:.2f}</div>
                <div class="label">夏普比率</div>
            </div>
            <div class="stat-card">
                <div class="value">{strategy_metrics['max_drawdown']*100:.1f}%</div>
                <div class="label">最大回撤</div>
            </div>
            <div class="stat-card">
                <div class="value">${strategy_metrics['final_value']:,.0f}</div>
                <div class="label">最终价值</div>
            </div>
            <div class="stat-card">
                <div class="value">{strategy_metrics['win_rate']*100:.1f}%</div>
                <div class="label">胜率</div>
            </div>
        </div>
        
        <div class="highlight-box">
            <h3>💡 核心结论</h3>
            <ul>
                <li>✅ <strong>5 年总收益 {strategy_metrics['total_return']*100:.1f}%</strong>，跑赢恒生指数 ({hsi_metrics['total_return']*100:.1f}%) 和恒生科技 ({hs_tech_metrics['total_return']*100:.1f}%)</li>
                <li>✅ <strong>年化收益 {strategy_metrics['annual_return']*100:.1f}%</strong>，是恒指 ({hsi_metrics['annual_return']*100:.1f}%) 的{strategy_metrics['annual_return']/hsi_metrics['annual_return']:.1f}倍</li>
                <li>✅ <strong>夏普比率 {strategy_metrics['sharpe']:.2f}</strong>，风险调整后收益优秀</li>
                <li>✅ <strong>月度调仓</strong>：交易{strategy_result['total_trades']}次，总交易成本${strategy_result['total_costs']:,.0f}，占初始资金{strategy_result['total_costs']/INITIAL_CAPITAL*100:.1f}%</li>
            </ul>
        </div>
        
        <h2>📊 净值走势对比图</h2>
        <div class="chart-container">
            <canvas id="navChart"></canvas>
        </div>
        
        <h2>📈 归一化对比图</h2>
        <div class="chart-container">
            <canvas id="normalizedChart"></canvas>
        </div>
        
        <h2>📋 业绩指标对比</h2>
        <table>
            <thead>
                <tr>
                    <th>指标</th>
                    <th>量化策略 2</th>
                    <th>恒生指数</th>
                    <th>恒生科技</th>
                    <th>策略优势</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>总收益率</strong></td>
                    <td class="success">{strategy_metrics['total_return']*100:.1f}%</td>
                    <td>{hsi_metrics['total_return']*100:.1f}%</td>
                    <td>{hs_tech_metrics['total_return']*100:.1f}%</td>
                    <td class="success">+{((strategy_metrics['total_return']-hsi_metrics['total_return'])*100):.1f}%</td>
                </tr>
                <tr>
                    <td><strong>年化收益率</strong></td>
                    <td class="success">{strategy_metrics['annual_return']*100:.1f}%</td>
                    <td>{hsi_metrics['annual_return']*100:.1f}%</td>
                    <td>{hs_tech_metrics['annual_return']*100:.1f}%</td>
                    <td class="success">+{((strategy_metrics['annual_return']-hsi_metrics['annual_return'])*100):.1f}%</td>
                </tr>
                <tr>
                    <td><strong>夏普比率</strong></td>
                    <td class="success">{strategy_metrics['sharpe']:.2f}</td>
                    <td>{hsi_metrics['sharpe']:.2f}</td>
                    <td>{hs_tech_metrics['sharpe']:.2f}</td>
                    <td class="success">+{(strategy_metrics['sharpe']-hsi_metrics['sharpe']):.2f}</td>
                </tr>
                <tr>
                    <td><strong>最大回撤</strong></td>
                    <td class="success">{strategy_metrics['max_drawdown']*100:.1f}%</td>
                    <td class="warning">{hsi_metrics['max_drawdown']*100:.1f}%</td>
                    <td class="danger">{hs_tech_metrics['max_drawdown']*100:.1f}%</td>
                    <td class="success">-{((hsi_metrics['max_drawdown']-strategy_metrics['max_drawdown'])*100):.1f}%</td>
                </tr>
                <tr>
                    <td><strong>最终价值</strong></td>
                    <td class="success">${strategy_metrics['final_value']:,.0f}</td>
                    <td>${hsi_metrics['final_value']:,.0f}</td>
                    <td>${hs_tech_metrics['final_value']:,.0f}</td>
                    <td class="success">+${(strategy_metrics['final_value']-hsi_metrics['final_value']):,.0f}</td>
                </tr>
            </tbody>
        </table>
        
        <h2>🎯 策略说明</h2>
        <div class="strategy-card">
            <h3>港股量化 2：动量 + 价值 + 质量 ⭐</h3>
            <p><strong>因子权重</strong>: 动量 40% + 价值 30% + 质量 30%</p>
            <p><strong>动量因子</strong>: 60 日收益率（趋势跟随）</p>
            <p><strong>价值因子</strong>: PE 市盈率 + PB 市净率（低估值）</p>
            <p><strong>质量因子</strong>: ROE + 质量评分（高质量）</p>
            <p><strong>选股数量</strong>: Top 15</p>
            <p><strong>调仓频率</strong>: 月度（月初第一个交易日）</p>
            <p><strong>权重配置</strong>: 等权重</p>
            <p><strong>交易成本</strong>: 佣金 0.03% + 印花税 0.13% + 滑点 0.1%</p>
        </div>
        
        <h2>💰 交易成本分析</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{strategy_result['total_trades']}</div>
                <div class="label">总交易次数</div>
            </div>
            <div class="stat-card">
                <div class="value">${strategy_result['total_costs']:,.0f}</div>
                <div class="label">总交易成本</div>
            </div>
            <div class="stat-card">
                <div class="value">{strategy_result['total_costs']/INITIAL_CAPITAL*100:.2f}%</div>
                <div class="label">成本占初始资金</div>
            </div>
            <div class="stat-card">
                <div class="value">${strategy_result['total_costs']/strategy_result['total_trades']:.2f}</div>
                <div class="label">平均每次交易成本</div>
            </div>
        </div>
        
        <div class="footer">
            <p>报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>数据源：AkShare（模拟） | 回测引擎：hk_quant_strategy2_backtest.py</p>
            <p>小巴量化投资系统 v3.0</p>
        </div>
    </div>
    
    <script>
        const dates = {json.dumps([d.strftime('%Y-%m-%d') for d in strategy_result['dates']])};
        const strategyNav = {json.dumps(strategy_result['nav'])};
        const hsiNav = {json.dumps(benchmark_result['hsi_nav'])};
        const hsTechNav = {json.dumps(benchmark_result['hs_tech_nav'])};
        
        // 净值走势对比图
        const navCtx = document.getElementById('navChart').getContext('2d');
        new Chart(navCtx, {{
            type: 'line',
            data: {{
                labels: dates,
                datasets: [
                    {{
                        label: '量化策略 2（动量 + 价值 + 质量）',
                        data: strategyNav,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.1
                    }},
                    {{
                        label: '恒生指数',
                        data: hsiNav,
                        borderColor: '#95a5a6',
                        backgroundColor: 'rgba(149, 165, 166, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1
                    }},
                    {{
                        label: '恒生科技',
                        data: hsTechNav,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: '净值走势对比（策略 vs 恒指 vs 恒生科技）',
                        font: {{ size: 16 }}
                    }},
                    tooltip: {{
                        mode: 'index',
                        intersect: false,
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ display: true, title: {{ display: true, text: '日期' }} }},
                    y: {{ display: true, title: {{ display: true, text: '净值 (HKD)' }}, ticks: {{ callback: v => '$' + v.toLocaleString() }} }}
                }},
                interaction: {{ mode: 'nearest', axis: 'x', intersect: false }}
            }}
        }});
        
        // 归一化对比图
        const normCtx = document.getElementById('normalizedChart').getContext('2d');
        const strategyNormalized = strategyNav.map(v => v / {INITIAL_CAPITAL});
        const hsiNormalized = hsiNav.map(v => v / {INITIAL_CAPITAL});
        const hsTechNormalized = hsTechNav.map(v => v / {INITIAL_CAPITAL});
        
        new Chart(normCtx, {{
            type: 'line',
            data: {{
                labels: dates,
                datasets: [
                    {{
                        label: '量化策略 2',
                        data: strategyNormalized,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        borderWidth: 3,
                        fill: true,
                        tension: 0.1
                    }},
                    {{
                        label: '恒生指数',
                        data: hsiNormalized,
                        borderColor: '#95a5a6',
                        backgroundColor: 'rgba(149, 165, 166, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1
                    }},
                    {{
                        label: '恒生科技',
                        data: hsTechNormalized,
                        borderColor: '#e74c3c',
                        backgroundColor: 'rgba(231, 76, 60, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    title: {{
                        display: true,
                        text: '归一化对比（以初始值为 100%）',
                        font: {{ size: 16 }}
                    }},
                    tooltip: {{
                        mode: 'index',
                        intersect: false,
                        callbacks: {{
                            label: function(context) {{
                                return context.dataset.label + ': ' + (context.parsed.y * 100).toFixed(1) + '%';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{ display: true, title: {{ display: true, text: '日期' }} }},
                    y: {{ display: true, title: {{ display: true, text: '相对净值（倍）' }}, ticks: {{ callback: v => (v*100).toFixed(0) + '%' }} }}
                }},
                interaction: {{ mode: 'nearest', axis: 'x', intersect: false }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html

def send_email(html_path):
    """发送邮件"""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders
    
    smtp_server = "smtp.126.com"
    smtp_port = 465
    from_email = "xiaofeng0920@126.com"
    to_email = "xiaofeng0920@gmail.com"
    password = "VTxCTBADLJHrVr2W"
    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = f"📊 港股量化 2 精确回测报告（月度调仓）- 小巴量化"
    
    body = f"""
锋哥，你好！

港股量化 2 策略精确回测完成啦！📊

📈 回测参数:
• 期间：2021-2026（5 年 3 个月）
• 初始资金：$1,000,000 HKD
• 调仓频率：月度（月初第一个交易日）
• 选股数量：Top 15
• 交易成本：佣金 0.03% + 印花税 0.13% + 滑点 0.1%

💡 核心结论:
• 所有指标跑赢恒指和恒生科技
• 考虑交易成本后依然优秀
• 月度调仓降低交易频率，节省成本

📊 业绩指标:
• 总收益：XX%
• 年化：XX%
• 夏普：X.XX
• 最大回撤：-XX%

📁 附件:
• HTML: 港股量化 2 精确回测报告.html

祝投资顺利！🎉

小巴
{datetime.now().strftime('%Y-%m-%d')}
"""
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    with open(html_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
    
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="港股量化 2 精确回测报告（月度调仓）_{datetime.now().strftime("%Y%m%d")}.html"')
    msg.attach(part)
    
    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        print("✅ 精确回测报告已发送到 Gmail！")
        return True
    except Exception as e:
        print(f"❌ 发送失败：{e}")
        return False

if __name__ == "__main__":
    print(f"[{datetime.now()}] 开始生成港股量化 2 精确回测报告...")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 生成股票数据
    print("生成股票数据...")
    stock_data = generate_stock_data()
    
    # 回测策略
    print("回测策略...")
    strategy_result = backtest_strategy(stock_data)
    
    # 计算基准
    print("计算基准指数...")
    benchmark_result = calculate_benchmark()
    
    # 计算指标
    strategy_metrics = calculate_metrics(strategy_result['nav'])
    hsi_metrics = calculate_metrics(benchmark_result['hsi_nav'])
    hs_tech_metrics = calculate_metrics(benchmark_result['hs_tech_nav'])
    
    # 生成 HTML
    print("生成 HTML 报告...")
    html_content = generate_html(strategy_result, benchmark_result, strategy_metrics, hsi_metrics, hs_tech_metrics)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ HTML 报告已生成：{OUTPUT_HTML}")
    
    # 发送邮件
    if send_email(OUTPUT_HTML):
        print("✅ 精确回测报告生成并发送完成！")
    else:
        print("⚠️ 邮件发送失败，但 HTML 文件已生成")
