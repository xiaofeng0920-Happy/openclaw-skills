#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股全市场选股 - 多周期回测系统 (同花顺数据源)
使用 AKShare 获取同花顺数据
回测 5 年、8 年、10 年买入持有收益
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time

print('='*80)
print('📊 A 股全市场选股 - 多周期回测 (同花顺数据源)')
print('='*80)
print()
print('【回测策略】')
print('  策略：买入持有 (Buy & Hold)')
print('  回测周期：5 年、8 年、10 年')
print('  数据源：同花顺 (AKShare)')
print()

# ============ 读取 A 股监控池 ============
monitor_file = Path('reports/monitor_pool_a_share_test_20260330_1635.csv')
if not monitor_file.exists():
    print('❌ 监控池文件不存在')
    exit(1)

monitor_df = pd.read_csv(monitor_file)
print(f'监控股票：{len(monitor_df)} 只')
print(f'股票列表：{monitor_df["ts_code"].tolist()[:5]}...')
print()

# ============ 获取历史数据 ============
def get_historical_data_akshare(ts_code, years, max_retries=5):
    """使用 AKShare 获取 A 股历史数据 (带增强重试机制)"""
    for attempt in range(max_retries):
        try:
            # 转换代码格式 (600519.SH → 600519)
            code = ts_code.split('.')[0]
            
            # 计算日期范围
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=int(365.25*years))).strftime('%Y%m%d')
            
            # 使用 AKShare 获取历史数据
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            
            if df is None or df.empty:
                return None
            
            # 重命名列
            df = df.rename(columns={
                '日期': 'trade_date',
                '收盘': 'close',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'turnover'
            })
            
            # 按交易日期排序
            df = df.sort_values('trade_date')
            
            return df
        
        except Exception as e:
            if attempt < max_retries - 1:
                # 指数退避 + 随机抖动
                delay = (2 ** attempt) + (attempt * 0.5)
                time.sleep(delay)
                continue
            print(f'⚠️ 获取 {ts_code} 数据失败 (尝试{attempt+1}/{max_retries}): {e}')
            return None


# ============ 回测函数 ============
def backtest_buy_and_hold(stocks, years):
    """买入持有回测"""
    
    print(f'\n【回测】{years}年 买入持有策略')
    print('='*60)
    
    results = []
    
    for i, ts_code in enumerate(stocks, 1):
        # 获取历史数据
        data = get_historical_data_akshare(ts_code, years)
        
        if data is None or len(data) < 10:
            print(f'  {i:2d}. {ts_code}: ❌ 数据不足')
            continue
        
        # 获取最早和最晚价格
        start_price = data.iloc[0]['close']
        end_price = data.iloc[-1]['close']
        
        # 计算收益率
        total_return = (end_price - start_price) / start_price * 100
        
        # 年化收益
        start_dt = datetime.strptime(str(data.iloc[0]['trade_date']).replace('-', ''), '%Y%m%d')
        end_dt = datetime.strptime(str(data.iloc[-1]['trade_date']).replace('-', ''), '%Y%m%d')
        days = (end_dt - start_dt).days
        years_actual = days / 365.25
        annual_return = ((1 + total_return / 100) ** (1 / years_actual) - 1) * 100 if years_actual > 0 else 0
        
        # 最大回撤
        data['cummax'] = data['close'].cummax()
        data['drawdown'] = (data['close'] - data['cummax']) / data['cummax'] * 100
        max_drawdown = data['drawdown'].min()
        
        # 获取股票名称
        name = monitor_df[monitor_df['ts_code'] == ts_code]['name'].iloc[0] if not monitor_df[monitor_df['ts_code'] == ts_code].empty else ''
        
        results.append({
            'ts_code': ts_code,
            'name': name,
            'start_date': str(data.iloc[0]['trade_date']),
            'end_date': str(data.iloc[-1]['trade_date']),
            'start_price': start_price,
            'end_price': end_price,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'trading_days': len(data),
        })
        
        print(f'  {i:2d}. {ts_code} {name:<10}: ￥{start_price:.2f} → ￥{end_price:.2f} ({total_return:+.1f}%)')
        
        time.sleep(1.0)  # 10 年期需要更长延时，避免限流
    
    return results


# ============ 执行回测 ============
stocks = monitor_df['ts_code'].astype(str).tolist()
print(f'回测股票：{stocks[:5]}...')

# 回测配置
BACKTEST_PERIODS = [5, 8, 10]

all_results = {}

for years in BACKTEST_PERIODS:
    results = backtest_buy_and_hold(stocks, years)
    all_results[years] = results
    
    if results:
        # 计算平均收益
        avg_return = sum([r['total_return'] for r in results]) / len(results)
        avg_annual = sum([r['annual_return'] for r in results]) / len(results)
        avg_drawdown = sum([r['max_drawdown'] for r in results]) / len(results)
        
        print(f'\n【{years}年回测汇总】')
        print(f'  有效股票数：{len(results)}/{len(stocks)}')
        print(f'  平均总收益：{avg_return:+.1f}%')
        print(f'  平均年收益：{avg_annual:+.1f}%')
        print(f'  平均最大回撤：{avg_drawdown:.1f}%')

# ============ 保存结果 ============
print(f'\n{"="*80}')
print('✅ 回测完成！')
print(f'{"="*80}')

for years in BACKTEST_PERIODS:
    if all_results[years]:
        results_df = pd.DataFrame(all_results[years])
        
        output_file = Path(f'reports/backtest_iths_{years}y_buyhold_' + datetime.now().strftime('%Y%m%d_%H%M') + '.csv')
        results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f'\n【同花顺{years}年回测结果】已保存：{output_file}')
        print(f'  股票数：{len(results_df)}')
        print(f'  平均收益：{results_df["total_return"].mean():+.1f}%')
        if not results_df.empty:
            best_idx = results_df["total_return"].idxmax()
            print(f'  最佳股票：{results_df.loc[best_idx]["ts_code"]} {results_df.loc[best_idx]["name"]} ({results_df.loc[best_idx]["total_return"]:+.1f}%)')

print(f'\n{"="*80}')
print('✅ 同花顺数据源回测完成')
print(f'{"="*80}')
