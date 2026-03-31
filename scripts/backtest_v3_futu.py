#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控池股票 - 多周期动态回测系统 v3.0 (富途数据源)
建仓规则:
- 持有 10 支股票
- 行业集中度 ≤ 15%
- 单票集中度 ≤ 15%
- 根据估值 (PE/PB) + 技术指标 (RSI/20 日涨幅) 筛选
数据源：富途 OpenD
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import time
from futu import *

# ============ 回测参数 ============
HOLDINGS_COUNT = 10  # 持有股票数
MAX_INDUSTRY_WEIGHT = 0.15  # 行业集中度 ≤ 15%
MAX_SINGLE_WEIGHT = 0.15  # 单票集中度 ≤ 15%
INITIAL_CAPITAL = 1000000  # 初始资金 100 万

print('='*80)
print('📊 监控池股票 - 多周期动态回测 v3.0 (富途数据源)')
print('='*80)
print()
print('【建仓规则】')
print(f'  持有股票数：{HOLDINGS_COUNT} 支')
print(f'  行业集中度：≤ {MAX_INDUSTRY_WEIGHT*100:.0f}%')
print(f'  单票集中度：≤ {MAX_SINGLE_WEIGHT*100:.0f}%')
print(f'  筛选标准：估值 (PE/PB) + 技术指标 (RSI/20 日涨幅)')
print(f'  数据源：富途 OpenD')
print()

# ============ 读取监控池 ============
monitor_file = Path('reports/monitor_pool_HK_20260330_1542.csv')
if not monitor_file.exists():
    print('❌ 监控池文件不存在')
    exit(1)

monitor_df = pd.read_csv(monitor_file)
print(f'监控股票：{len(monitor_df)} 只')
print()

# ============ 连接富途 ============
print('连接富途 OpenD...')
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
print('✅ 连接成功\n')

# ============ 获取历史 K 线数据 ============
def get_historical_kline(code, start_date, end_date):
    """获取富途历史 K 线数据"""
    try:
        # 转换代码格式 (00966 → HK.00966)
        futu_code = 'HK.' + code
        
        # 获取日 K 线
        ret, data = quote_ctx.get_cur_kline(
            futu_code, 
            num=3000,  # 获取 3000 天数据
            ktype=KLType.K_DAY, 
            autype=AuType.QFQ  # 前复权
        )
        
        if ret != RET_OK or data.empty:
            return None
        
        # 计算技术指标
        data = data.sort_values('time_key').reset_index(drop=True)
        
        # 20 日均线
        data['ma20'] = data['close'].rolling(window=20).mean()
        
        # 20 日涨幅
        data['change_20d'] = data['close'].pct_change(20) * 100
        
        # RSI (14 日)
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        return data
    
    except Exception as e:
        print(f'⚠️ 获取 {code} 数据失败：{e}')
        return None


# ============ 选股函数 ============
def select_stocks(stock_data, industries, current_date):
    """
    根据估值和技术指标选股
    
    规则:
    1. 按 PE 从低到高排序
    2. 按 RSI 从低到高排序 (避免追高)
    3. 按 20 日涨幅排序 (选择趋势向好)
    4. 行业分散 (单行业≤15%)
    5. 等权重配置 (单票≤15%)
    """
    
    scores = []
    
    for code, data in stock_data.items():
        # 获取最接近当前日期的数据
        data_on_date = data[data['time_key'] <= current_date]
        if data_on_date.empty:
            continue
        
        latest = data_on_date.iloc[-1]
        
        # 获取估值 (从 monitor_df)
        pe = monitor_df[monitor_df['code'].str.contains(code)]['pe'].iloc[0] if not monitor_df[monitor_df['code'].str.contains(code)].empty else 10
        pb = monitor_df[monitor_df['code'].str.contains(code)]['pb'].iloc[0] if not monitor_df[monitor_df['code'].str.contains(code)].empty else 1.0
        
        # 技术指标
        rsi = latest.get('rsi', 50)
        change_20d = latest.get('change_20d', 0)
        
        # 综合评分 (PE 越低越好，RSI 越低越好，20 日涨幅适中最好)
        pe_score = (30 - pe) / 30 * 40 if pe > 0 else 20  # PE 评分 (40 分)
        rsi_score = (70 - rsi) / 70 * 30 if pd.notna(rsi) and rsi < 70 else 0  # RSI 评分 (30 分)
        trend_score = min(change_20d, 20) / 20 * 30 if pd.notna(change_20d) and change_20d > 0 else 0  # 趋势评分 (30 分)
        
        total_score = pe_score + rsi_score + trend_score
        
        industry = industries.get(code, '其他')
        
        scores.append({
            'code': code,
            'industry': industry,
            'pe': pe,
            'pb': pb,
            'rsi': rsi,
            'change_20d': change_20d,
            'score': total_score,
        })
    
    # 按评分排序
    scores_df = pd.DataFrame(scores)
    if scores_df.empty:
        return []
    
    scores_df = scores_df.sort_values('score', ascending=False)
    
    # 选股逻辑 (行业分散)
    selected = []
    industry_count = {}
    
    for _, row in scores_df.iterrows():
        if len(selected) >= HOLDINGS_COUNT:
            break
        
        industry = row['industry']
        
        # 检查行业集中度
        current_industry_count = industry_count.get(industry, 0)
        if current_industry_count >= 2:  # 单行业最多 2 只
            continue
        
        # 选中
        selected.append(row)
        industry_count[industry] = current_industry_count + 1
    
    return selected


# ============ 回测主函数 ============
def backtest(stocks, industries, start_date, end_date, rebalance_freq):
    """执行回测"""
    
    print(f'\n回测周期：{start_date} 至 {end_date}')
    print(f'调仓频率：{rebalance_freq}')
    
    # 获取所有股票历史数据
    print('获取历史 K 线数据...')
    stock_data = {}
    for i, code in enumerate(stocks, 1):
        data = get_historical_kline(code, start_date, end_date)
        if data is not None and not data.empty:
            stock_data[code] = data
        if i % 5 == 0:
            print(f'  进度：{i}/{len(stocks)}')
        time.sleep(0.2)  # 避免请求过快
    
    print(f'有效数据：{len(stock_data)} 只股票')
    
    if not stock_data:
        return None
    
    # 生成调仓日期
    start_dt = datetime.strptime(start_date, '%Y-%m-%d')
    end_dt = datetime.strptime(end_date, '%Y-%m-%d')
    
    rebalance_dates = []
    current_dt = start_dt
    
    while current_dt <= end_dt:
        rebalance_dates.append(current_dt.strftime('%Y-%m-%d'))
        
        if rebalance_freq == 'monthly':
            if current_dt.month == 12:
                current_dt = current_dt.replace(year=current_dt.year + 1, month=1, day=1)
            else:
                current_dt = current_dt.replace(month=current_dt.month + 1, day=1)
        elif rebalance_freq == 'quarterly':
            if current_dt.month >= 10:
                current_dt = current_dt.replace(year=current_dt.year + 1, month=1, day=1)
            else:
                current_dt = current_dt.replace(month=current_dt.month + 3, day=1)
        else:  # yearly
            current_dt = current_dt.replace(year=current_dt.year + 1, month=1, day=1)
    
    # 回测主循环
    capital = INITIAL_CAPITAL
    positions = {}  # {code: shares}
    portfolio_values = []
    rebalance_log = []
    
    # 获取所有交易日
    all_dates = set()
    for data in stock_data.values():
        all_dates.update(data['time_key'].tolist())
    trading_days = sorted(all_dates)
    
    print(f'\n开始回测...')
    print(f'交易日数：{len(trading_days)}')
    
    for trade_date in trading_days:
        # 检查是否调仓日
        if trade_date in rebalance_dates:
            # 调仓：卖出所有，重新选股
            positions = {}
            
            # 选股
            selected_stocks = select_stocks(stock_data, industries, trade_date)
            
            if selected_stocks:
                # 等权重买入
                weight = 1.0 / len(selected_stocks)
                for stock in selected_stocks:
                    code = stock['code']
                    
                    # 获取价格
                    price_data = stock_data[code][stock_data[code]['time_key'] == trade_date]
                    if price_data.empty:
                        continue
                    
                    price = price_data.iloc[0]['close']
                    shares = int((capital * weight) / price)
                    
                    if shares > 0:
                        positions[code] = shares
                        capital -= shares * price
                
                # 记录调仓日志
                rebalance_log.append({
                    'date': trade_date,
                    'count': len(selected_stocks),
                    'stocks': [s['code'] for s in selected_stocks],
                })
        
        # 计算组合价值
        portfolio_value = capital
        for code, shares in positions.items():
            price_data = stock_data[code][stock_data[code]['time_key'] == trade_date]
            if not price_data.empty:
                portfolio_value += shares * price_data.iloc[0]['close']
        
        portfolio_values.append({
            'time_key': trade_date,
            'portfolio_value': portfolio_value,
            'return_pct': (portfolio_value - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100,
        })
    
    # 计算回测指标
    result_df = pd.DataFrame(portfolio_values)
    
    if result_df.empty:
        return None
    
    # 回测指标
    final_value = result_df.iloc[-1]['portfolio_value']
    total_return = result_df.iloc[-1]['return_pct']
    
    max_value = result_df['portfolio_value'].max()
    min_value = result_df['portfolio_value'].min()
    max_drawdown = (max_value - min_value) / max_value * 100
    
    # 年化收益
    days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days
    years = days / 365.25
    annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0
    
    # 调仓次数
    rebalance_count = len(rebalance_log)
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'rebalance_freq': rebalance_freq,
        'initial_capital': INITIAL_CAPITAL,
        'final_value': final_value,
        'total_return': total_return,
        'annual_return': annual_return,
        'max_drawdown': max_drawdown,
        'rebalance_count': rebalance_count,
        'result_df': result_df,
        'rebalance_log': rebalance_log,
    }


# ============ 执行回测 ============
stocks = monitor_df['code'].astype(str).tolist()
industries = dict(zip(monitor_df['code'].astype(str), monitor_df['industry']))

print(f'\n回测股票：{stocks[:5]}...')
print(f'行业分布：{set(industries.values())}')

# 回测配置
BACKTEST_PERIODS = [5, 8, 10]
REBALANCE_FREQS = ['monthly', 'quarterly', 'yearly']

end_date = datetime.now().strftime('%Y-%m-%d')
all_results = []

for years in BACKTEST_PERIODS:
    start_date = (datetime.now() - timedelta(days=int(365.25*years))).strftime('%Y-%m-%d')
    
    for freq in REBALANCE_FREQS:
        print(f"\n{'='*80}")
        print(f'【回测】{years}年 - {freq}调仓')
        print('='*80)
        
        result = backtest(
            stocks=stocks,
            industries=industries,
            start_date=start_date,
            end_date=end_date,
            rebalance_freq=freq
        )
        
        if result:
            all_results.append({
                '回测周期': f'{years}年',
                '调仓频率': freq,
                '开始日期': result['start_date'],
                '结束日期': result['end_date'],
                '初始资金': result['initial_capital'],
                '最终价值': f"{result['final_value']:,.0f}",
                '总收益率': f"{result['total_return']:.2f}%",
                '年化收益': f"{result['annual_return']:.2f}%",
                '最大回撤': f"{result['max_drawdown']:.2f}%",
                '调仓次数': result['rebalance_count'],
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
    
    output_file = Path('reports/backtest_monitor_pool_v3_' + datetime.now().strftime('%Y%m%d_%H%M') + '.csv')
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
print('✅ 多周期动态回测 v3.0 完成')
print(f'{"="*80}')

quote_ctx.close()
