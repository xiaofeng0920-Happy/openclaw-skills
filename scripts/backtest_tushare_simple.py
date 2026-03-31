#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控池股票 - 简化回测系统 (Tushare 数据源)
使用 trade_date 参数获取历史数据
回测 5 年、8 年、10 年买入持有收益
"""

import pandas as pd
import tushare as ts
from datetime import datetime, timedelta
from pathlib import Path
import time

# Tushare 配置
TUSHARE_TOKEN = '1dbdfba7c672d47f22db86f586d5aff9730124b321c2ebdda91890d3'
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

print('='*80)
print('📊 监控池股票 - 简化回测 (Tushare 数据源)')
print('='*80)
print()
print('【回测策略】')
print('  策略：买入持有 (Buy & Hold)')
print('  不调仓，持有到期')
print('  回测周期：5 年、8 年、10 年')
print('  数据源：Tushare Pro (trade_date)')
print()

# ============ 读取监控池 ============
monitor_file = Path('reports/monitor_pool_HK_20260330_1542.csv')
if not monitor_file.exists():
    print('❌ 监控池文件不存在')
    exit(1)

monitor_df = pd.read_csv(monitor_file)
print(f'监控股票：{len(monitor_df)} 只')
print()

# ============ 获取历史数据 ============
def get_historical_data(code, years):
    """使用 Tushare 获取港股历史数据"""
    try:
        # 转换代码格式 (00966 → 00966.HK)
        ts_code = code + '.HK'
        
        # 计算日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=int(365.25*years))).strftime('%Y%m%d')
        
        # 使用 trade_date 参数获取历史数据
        df = pro.hk_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df is None or df.empty:
            return None
        
        # 按交易日期排序
        df = df.sort_values('trade_date')
        
        return df
    
    except Exception as e:
        print(f'⚠️ 获取 {code} 数据失败：{e}')
        return None


# ============ 回测函数 ============
def backtest_buy_and_hold(stocks, years):
    """买入持有回测"""
    
    print(f'\n【回测】{years}年 买入持有策略')
    print('='*60)
    
    results = []
    
    for i, code in enumerate(stocks, 1):
        # 获取历史数据
        data = get_historical_data(code, years)
        
        if data is None or len(data) < 10:
            print(f'  {i:2d}. {code}: ❌ 数据不足')
            continue
        
        # 获取最早和最晚价格
        start_price = data.iloc[0]['close']
        end_price = data.iloc[-1]['close']
        
        # 计算收益率
        total_return = (end_price - start_price) / start_price * 100
        
        # 年化收益
        start_dt = datetime.strptime(str(data.iloc[0]['trade_date']), '%Y%m%d')
        end_dt = datetime.strptime(str(data.iloc[-1]['trade_date']), '%Y%m%d')
        days = (end_dt - start_dt).days
        years_actual = days / 365.25
        annual_return = ((1 + total_return / 100) ** (1 / years_actual) - 1) * 100 if years_actual > 0 else 0
        
        # 最大回撤
        data['cummax'] = data['close'].cummax()
        data['drawdown'] = (data['close'] - data['cummax']) / data['cummax'] * 100
        max_drawdown = data['drawdown'].min()
        
        results.append({
            'code': code,
            'name': monitor_df[monitor_df['code'] == int(code)]['name'].iloc[0] if not monitor_df[monitor_df['code'] == int(code)].empty else '',
            'start_date': str(data.iloc[0]['trade_date']),
            'end_date': str(data.iloc[-1]['trade_date']),
            'start_price': start_price,
            'end_price': end_price,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'trading_days': len(data),
        })
        
        print(f'  {i:2d}. {code}: ${start_price:.2f} → ${end_price:.2f} ({total_return:+.1f}%)')
        
        time.sleep(0.1)  # 避免限流
    
    return results


# ============ 执行回测 ============
stocks = monitor_df['code'].astype(str).tolist()
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
        
        output_file = Path(f'reports/backtest_tushare_{years}y_buyhold_' + datetime.now().strftime('%Y%m%d_%H%M') + '.csv')
        results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f'\n【{years}年回测结果】已保存：{output_file}')
        print(f'  股票数：{len(results_df)}')
        print(f'  平均收益：{results_df["total_return"].mean():+.1f}%')
        if not results_df.empty:
            best_idx = results_df["total_return"].idxmax()
            print(f'  最佳股票：{results_df.loc[best_idx]["code"]} ({results_df.loc[best_idx]["total_return"]:+.1f}%)')

print(f'\n{"="*80}')
print('✅ Tushare 简化回测完成')
print(f'{"="*80}')
