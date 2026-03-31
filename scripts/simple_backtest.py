#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控池股票 - 简化回测系统 (买入持有策略)
不回测调仓，只测试 5 年/8 年/10 年的买入持有收益
数据源：富途 OpenD
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import time
from futu import *

print('='*80)
print('📊 监控池股票 - 简化回测 (买入持有策略)')
print('='*80)
print()
print('【回测策略】')
print('  策略：买入持有 (Buy & Hold)')
print('  不调仓，持有到期')
print('  回测周期：5 年、8 年、10 年')
print('  数据源：富途 OpenD')
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

# ============ 获取历史数据 ============
def get_historical_data(code, years):
    """获取指定年份的历史数据"""
    try:
        futu_code = 'HK.' + code
        
        # 计算需要获取的 K 线数量 (每年约 250 个交易日)
        num_klines = int(years * 250) + 100
        
        # 获取日 K 线
        ret, data = quote_ctx.get_cur_kline(
            futu_code, 
            num=num_klines,
            ktype=KLType.K_DAY, 
            autype=AuType.QFQ  # 前复权
        )
        
        if ret != RET_OK or data.empty:
            return None
        
        # 按时间排序
        data = data.sort_values('time_key')
        
        return data
    
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
        days = (datetime.strptime(data.iloc[-1]['time_key'], '%Y-%m-%d') - 
                datetime.strptime(data.iloc[0]['time_key'], '%Y-%m-%d')).days
        years_actual = days / 365.25
        annual_return = ((1 + total_return / 100) ** (1 / years_actual) - 1) * 100 if years_actual > 0 else 0
        
        # 最大回撤
        data['cummax'] = data['close'].cummax()
        data['drawdown'] = (data['close'] - data['cummax']) / data['cummax'] * 100
        max_drawdown = data['drawdown'].min()
        
        results.append({
            'code': code,
            'name': monitor_df[monitor_df['code'] == code]['name'].iloc[0] if not monitor_df[monitor_df['code'] == code].empty else '',
            'start_date': data.iloc[0]['time_key'],
            'end_date': data.iloc[-1]['time_key'],
            'start_price': start_price,
            'end_price': end_price,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'trading_days': len(data),
        })
        
        print(f'  {i:2d}. {code}: ${start_price:.2f} → ${end_price:.2f} ({total_return:+.1f}%)')
        
        time.sleep(0.1)  # 避免请求过快
    
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
        
        output_file = Path(f'reports/backtest_{years}y_buyhold_' + datetime.now().strftime('%Y%m%d_%H%M') + '.csv')
        results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f'\n【{years}年回测结果】已保存：{output_file}')
        print(f'  股票数：{len(results_df)}')
        print(f'  平均收益：{results_df["total_return"].mean():+.1f}%')
        print(f'  最佳股票：{results_df.loc[results_df["total_return"].idxmax()]["code"]} ({results_df["total_return"].max():+.1f}%)')

print(f'\n{"="*80}')
print('✅ 简化回测完成')
print(f'{"="*80}')

quote_ctx.close()
