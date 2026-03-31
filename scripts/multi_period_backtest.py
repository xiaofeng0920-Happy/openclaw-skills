#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控池股票 - 多周期动态回测系统
回测周期：5 年、8 年、10 年
调仓频率：月度、季度、年度
"""

import pandas as pd
import tushare as ts
from datetime import datetime, timedelta
from pathlib import Path
import json

# Tushare 配置
TUSHARE_TOKEN = '1dbdfba7c672d47f22db86f586d5aff9730124b321c2ebdda91890d3'
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

print('='*80)
print('📊 监控池股票 - 多周期动态回测')
print('='*80)
print()

# 读取监控池
monitor_file = Path('reports/monitor_pool_HK_20260330_1542.csv')
if not monitor_file.exists():
    print('❌ 监控池文件不存在')
    exit(1)

monitor_df = pd.read_csv(monitor_file)
print(f'监控股票：{len(monitor_df)} 只')
print(f'股票列表：{monitor_df["code"].tolist()[:10]}...')
print()

# ============ 回测参数 ============
BACKTEST_PERIODS = [5, 8, 10]  # 年
REBALANCE_FREQS = ['monthly', 'quarterly', 'yearly']  # 调仓频率

# ============ 回测函数 ============
def get_historical_data(code, start_date, end_date):
    """获取历史行情数据"""
    try:
        # 转换代码格式 (00966 → 00966.HK)
        ts_code = code + '.HK'
        df = pro.hk_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df.empty:
            return None
        
        # 计算收益率
        df = df.sort_values('trade_date')
        df['daily_return'] = df['close'].pct_change()
        
        return df
    
    except Exception as e:
        return None


def backtest_strategy(stocks, start_date, end_date, rebalance_freq):
    """
    回测策略
    
    Args:
        stocks: 股票列表
        start_date: 开始日期
        end_date: 结束日期
        rebalance_freq: 调仓频率 (monthly/quarterly/yearly)
    
    Returns:
        dict: 回测结果
    """
    print(f'\n回测周期：{start_date} 至 {end_date}')
    print(f'调仓频率：{rebalance_freq}')
    
    # 获取所有股票数据
    stock_data = {}
    for code in stocks:
        data = get_historical_data(code, start_date, end_date)
        if data is not None and not data.empty:
            stock_data[code] = data
    
    if not stock_data:
        return None
    
    print(f'有效股票数：{len(stock_data)}')
    
    # 初始资金
    initial_capital = 1000000
    capital = initial_capital
    positions = {}
    portfolio_values = []
    rebalance_dates = []
    
    # 生成调仓日期
    start_dt = datetime.strptime(start_date, '%Y%m%d')
    end_dt = datetime.strptime(end_date, '%Y%m%d')
    
    rebalance_days = []
    current_dt = start_dt
    
    while current_dt <= end_dt:
        rebalance_days.append(current_dt.strftime('%Y%m%d'))
        
        if rebalance_freq == 'monthly':
            # 月度调仓 (每月第一个交易日)
            if current_dt.month == 12:
                current_dt = current_dt.replace(year=current_dt.year + 1, month=1, day=1)
            else:
                current_dt = current_dt.replace(month=current_dt.month + 1, day=1)
        elif rebalance_freq == 'quarterly':
            # 季度调仓 (每季度第一个交易日)
            if current_dt.month >= 10:
                current_dt = current_dt.replace(year=current_dt.year + 1, month=1, day=1)
            else:
                current_dt = current_dt.replace(month=current_dt.month + 3, day=1)
        else:  # yearly
            # 年度调仓
            current_dt = current_dt.replace(year=current_dt.year + 1, month=1, day=1)
    
    # 回测主循环
    trading_days = sorted(set([d for data in stock_data.values() for d in data['trade_date']]))
    
    for trade_date in trading_days:
        # 检查是否需要调仓
        if trade_date in rebalance_days:
            # 调仓日：卖出所有，买入 Top 5 (按 PE 最低)
            rebalance_dates.append(trade_date)
            
            # 计算当前组合价值
            total_value = capital
            for code, pos in positions.items():
                if code in stock_data:
                    price_data = stock_data[code][stock_data[code]['trade_date'] == trade_date]
                    if not price_data.empty:
                        total_value += pos * price_data.iloc[0]['close']
            
            # 重置持仓
            positions = {}
            capital = total_value
            
            # 等权重买入所有股票
            weight = 1.0 / len(stock_data)
            for code in stock_data.keys():
                price_data = stock_data[code][stock_data[code]['trade_date'] == trade_date]
                if not price_data.empty:
                    price = price_data.iloc[0]['close']
                    shares = int((capital * weight) / price)
                    if shares > 0:
                        positions[code] = shares
                        capital -= shares * price
        
        # 计算当日组合价值
        portfolio_value = capital
        for code, shares in positions.items():
            price_data = stock_data[code][stock_data[code]['trade_date'] == trade_date]
            if not price_data.empty:
                portfolio_value += shares * price_data.iloc[0]['close']
        
        portfolio_values.append({
            'trade_date': trade_date,
            'portfolio_value': portfolio_value,
            'return': (portfolio_value - initial_capital) / initial_capital * 100
        })
    
    # 计算回测指标
    result_df = pd.DataFrame(portfolio_values)
    
    if result_df.empty:
        return None
    
    # 回测指标
    total_return = result_df.iloc[-1]['return']
    max_value = result_df['portfolio_value'].max()
    min_value = result_df['portfolio_value'].min()
    max_drawdown = (max_value - min_value) / max_value * 100
    
    # 年化收益率
    days = (datetime.strptime(end_date, '%Y%m%d') - datetime.strptime(start_date, '%Y%m%d')).days
    years = days / 365.25
    annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0
    
    # 调仓次数
    rebalance_count = len(rebalance_dates)
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'rebalance_freq': rebalance_freq,
        'initial_capital': initial_capital,
        'final_value': result_df.iloc[-1]['portfolio_value'],
        'total_return': total_return,
        'annual_return': annual_return,
        'max_drawdown': max_drawdown,
        'rebalance_count': rebalance_count,
        'result_df': result_df
    }


# ============ 执行回测 ============
stocks = monitor_df['code'].astype(str).str.zfill(6).tolist()
print(f'回测股票：{stocks[:5]}...')

# 计算回测日期
end_date = datetime.now().strftime('%Y%m%d')
backtest_configs = []

for years in BACKTEST_PERIODS:
    start_date = (datetime.now() - timedelta(days=365*years)).strftime('%Y%m%d')
    for freq in REBALANCE_FREQS:
        backtest_configs.append({
            'years': years,
            'start_date': start_date,
            'end_date': end_date,
            'freq': freq
        })

print(f'\n共 {len(backtest_configs)} 个回测配置')
print()

# 存储回测结果
all_results = []

for config in backtest_configs:
    print("\n" + "="*80)
    print(f'【回测】{config["years"]}年 - {config["freq"]}调仓')
    print("="*80)
    
    result = backtest_strategy(
        stocks=stocks,
        start_date=config['start_date'],
        end_date=config['end_date'],
        rebalance_freq=config['freq']
    )
    
    if result:
        all_results.append({
            '回测周期': f"{config['years']}年",
            '调仓频率': config['freq'],
            '开始日期': config['start_date'],
            '结束日期': config['end_date'],
            '初始资金': result['initial_capital'],
            '最终价值': f"{result['final_value']:,.0f}",
            '总收益率': f"{result['total_return']:.2f}%",
            '年化收益': f"{result['annual_return']:.2f}%",
            '最大回撤': f"{result['max_drawdown']:.2f}%",
            '调仓次数': result['rebalance_count']
        })
        
        print(f'\n【回测结果】')
        print(f'  初始资金：¥{result["initial_capital"]:,.0f}')
        print(f'  最终价值：¥{result["final_value"]:,.0f}')
        print(f'  总收益率：{result["total_return"]:+.2f}%')
        print(f'  年化收益：{result["annual_return"]:+.2f}%')
        print(f'  最大回撤：{result["max_drawdown"]:.2f}%')
        print(f'  调仓次数：{result["rebalance_count"]}次')

# ============ 保存结果 ============
if all_results:
    results_df = pd.DataFrame(all_results)
    
    # 保存 CSV
    output_file = Path('reports/backtest_monitor_pool_' + datetime.now().strftime('%Y%m%d_%H%M') + '.csv')
    results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f'\n{"="*80}')
    print('✅ 回测完成！')
    print(f'{"="*80}')
    print(f'\n结果已保存：{output_file}')
    print()
    print('【回测结果汇总表】')
    print(results_df.to_string(index=False))
else:
    print('\n❌ 回测失败')

print(f'\n{"="*80}')
print('✅ 多周期动态回测完成')
print(f'{"="*80}')
