#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股监控池 - 多周期回测系统
使用 Tushare A 股数据验证回测逻辑
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
print('📊 A 股监控池 - 多周期回测系统')
print('='*80)
print()
print('【回测策略】')
print('  策略：买入持有 (Buy & Hold)')
print('  回测周期：5 年、8 年、10 年')
print('  数据源：Tushare A 股 (完整数据)')
print()

# ============ 创建 A 股监控池 ============
# 从港股监控池映射到 A 股同行业股票
print('【创建 A 股监控池】')
print('基于港股 26 只股票的行业，选择 A 股同行业龙头')
print()

# A 股监控池 (按行业对应港股)
a_share_pool = [
    # 银行
    '601398.SH',  # 工商银行
    '601288.SH',  # 农业银行
    # 保险
    '601318.SH',  # 中国平安
    '601628.SH',  # 中国人寿
    # 基建/建筑
    '601390.SH',  # 中国中铁
    '601668.SH',  # 中国建筑
    # 能源
    '601857.SH',  # 中国石油
    '600028.SH',  # 中国石化
    # 消费
    '600519.SH',  # 贵州茅台
    '000858.SZ',  # 五粮液
    # 医药
    '000538.SZ',  # 云南白药
    '600276.SH',  # 恒瑞医药
    # 科技
    '002415.SZ',  # 海康威视
    '300750.SZ',  # 宁德时代
    # 房地产
    '000002.SZ',  # 万科 A
    '600048.SH',  # 保利发展
    # 运输
    '601111.SH',  # 中国国航
    '600026.SH',  # 中远海能
    # 工业
    '601369.SH',  # 陕鼓动力
    '000425.SZ',  # 徐工机械
    # 纺织
    '002042.SZ',  # 华孚时尚
    '600307.SH',  # 酒钢宏兴
    # 汽车
    '000625.SZ',  # 长安汽车
    '002594.SZ',  # 比亚迪
    # 综合
    '600036.SH',  # 招商银行
    '601328.SH',  # 交通银行
]

print(f'A 股监控池：{len(a_share_pool)} 只')
print(f'股票列表：{a_share_pool[:5]}...')
print()

# ============ 获取股票名称 ============
def get_stock_name(ts_code):
    """获取股票名称"""
    try:
        df = pro.stock_basic(ts_code=ts_code, fields='ts_code,name')
        if not df.empty:
            return df.iloc[0]['name']
    except:
        pass
    return ''

# ============ 获取历史数据 ============
def get_historical_data(ts_code, years):
    """获取 A 股历史数据"""
    try:
        # 计算日期范围
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=int(365.25*years))).strftime('%Y%m%d')
        
        # 获取日线数据
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df is None or df.empty:
            return None
        
        # 按交易日期排序
        df = df.sort_values('trade_date')
        
        return df
    
    except Exception as e:
        print(f'⚠️ 获取 {ts_code} 数据失败：{e}')
        return None


# ============ 回测函数 ============
def backtest_buy_and_hold(stocks, years):
    """买入持有回测"""
    
    print(f'\n【回测】{years}年 买入持有策略')
    print('='*60)
    
    results = []
    
    for i, ts_code in enumerate(stocks, 1):
        # 获取历史数据
        data = get_historical_data(ts_code, years)
        
        if data is None or len(data) < 10:
            print(f'  {i:2d}. {ts_code}: ❌ 数据不足')
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
        
        # 获取股票名称
        name = get_stock_name(ts_code)
        
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
        
        time.sleep(0.05)  # 避免限流
    
    return results


# ============ 执行回测 ============
print(f'回测股票：{a_share_pool[:5]}...')

# 回测配置
BACKTEST_PERIODS = [5, 8, 10]

all_results = {}

for years in BACKTEST_PERIODS:
    results = backtest_buy_and_hold(a_share_pool, years)
    all_results[years] = results
    
    if results:
        # 计算平均收益
        avg_return = sum([r['total_return'] for r in results]) / len(results)
        avg_annual = sum([r['annual_return'] for r in results]) / len(results)
        avg_drawdown = sum([r['max_drawdown'] for r in results]) / len(results)
        
        print(f'\n【{years}年回测汇总】')
        print(f'  有效股票数：{len(results)}/{len(a_share_pool)}')
        print(f'  平均总收益：{avg_return:+.1f}%')
        print(f'  平均年收益：{avg_annual:+.1f}%')
        print(f'  平均最大回撤：{avg_drawdown:.1f}%')

# ============ 保存结果 ============
print(f'\n{"="*80}')
print('✅ 回测完成！')
print(f'{"="*80}')

# 保存港股监控池清单
monitor_file = Path('reports/monitor_pool_hk_26stocks.csv')
monitor_df = pd.read_csv('reports/monitor_pool_HK_20260330_1542.csv')
monitor_df.to_csv(monitor_file, index=False, encoding='utf-8-sig')
print(f'\n✅ 港股监控池清单已保存：{monitor_file}')

# 保存 A 股监控池
a_share_file = Path('reports/monitor_pool_a_share_26stocks.csv')
a_share_df = pd.DataFrame({'ts_code': a_share_pool})
a_share_df['name'] = a_share_df['ts_code'].apply(get_stock_name)
a_share_df.to_csv(a_share_file, index=False, encoding='utf-8-sig')
print(f'✅ A 股监控池清单已保存：{a_share_file}')

# 保存回测结果
for years in BACKTEST_PERIODS:
    if all_results[years]:
        results_df = pd.DataFrame(all_results[years])
        
        output_file = Path(f'reports/backtest_ashare_{years}y_buyhold_' + datetime.now().strftime('%Y%m%d_%H%M') + '.csv')
        results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f'\n【A 股{years}年回测结果】已保存：{output_file}')
        print(f'  股票数：{len(results_df)}')
        print(f'  平均收益：{results_df["total_return"].mean():+.1f}%')
        if not results_df.empty:
            best_idx = results_df["total_return"].idxmax()
            print(f'  最佳股票：{results_df.loc[best_idx]["ts_code"]} {results_df.loc[best_idx]["name"]} ({results_df.loc[best_idx]["total_return"]:+.1f}%)')

print(f'\n{"="*80}')
print('✅ A 股回测完成')
print(f'{"="*80}')
