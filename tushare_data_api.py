#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare 数据接口模块
- 默认 A 股数据源
- 港股备份数据源
"""

import tushare as ts
from datetime import datetime
from pathlib import Path

# ============ 配置 ============
TUSHARE_TOKEN = '1dbdfba7c672d47f22db86f586d5aff9730124b321c2ebdda91890d3'

# 初始化
ts.set_token(TUSHARE_TOKEN)
pro = ts.pro_api()

# ============================


def get_cn_index(index_code='000001.SH'):
    """
    获取 A 股指数数据
    
    Args:
        index_code: 指数代码，默认上证指数
        
    Returns:
        dict: 指数数据
    """
    try:
        # 获取最近 5 天数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now()).strftime('%Y%m%d')
        
        df = pro.index_daily(ts_code=index_code, start_date=start_date, end_date=end_date)
        
        if df.empty:
            # 如果今天无数据，获取昨天
            from datetime import timedelta
            yesterday = (datetime.now() - timedelta(days=5)).strftime('%Y%m%d')
            df = pro.index_daily(ts_code=index_code, start_date=yesterday, end_date=end_date)
        
        if df.empty:
            return None
        
        latest = df.iloc[0]
        change_pct = (latest['close'] - latest['pre_close']) / latest['pre_close'] * 100
        
        return {
            'ts_code': index_code,
            'name': '上证指数' if index_code == '000001.SH' else '深证成指',
            'close': latest['close'],
            'change_pct': change_pct,
            'open': latest['open'],
            'high': latest['high'],
            'low': latest['low'],
            'pre_close': latest['pre_close'],
            'vol': latest['vol'],
            'amount': latest['amount'],
            'trade_date': latest['trade_date']
        }
    
    except Exception as e:
        print(f'❌ 获取 A 股指数失败：{e}')
        return None


def get_cn_stock_daily(ts_code, start_date=None, end_date=None):
    """
    获取 A 股个股日线数据
    
    Args:
        ts_code: 股票代码 (600519.SH)
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        DataFrame: 日线数据
    """
    try:
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            from datetime import timedelta
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df if not df.empty else None
    
    except Exception as e:
        print(f'❌ 获取 A 股日线失败：{e}')
        return None


def get_cn_stock_basic(ts_code=None):
    """
    获取 A 股股票基本信息
    
    Args:
        ts_code: 股票代码 (可选)
        
    Returns:
        DataFrame: 股票基本信息
    """
    try:
        if ts_code:
            df = pro.stock_basic(ts_code=ts_code, fields='ts_code,symbol,name,industry,list_date')
        else:
            df = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,industry,area')
        
        return df if not df.empty else None
    
    except Exception as e:
        print(f'❌ 获取 A 股基本信息失败：{e}')
        return None


def get_cn_financial_indicator(ts_code):
    """
    获取 A 股财务指标
    
    Args:
        ts_code: 股票代码
        
    Returns:
        dict: 最新财务指标
    """
    try:
        # 获取最近一期财务数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now()).strftime('%Y0101')
        
        df = pro.fina_indicator(ts_code=ts_code, start_date=start_date, end_date=end_date)
        
        if df.empty:
            return None
        
        latest = df.iloc[0]
        
        return {
            'ts_code': ts_code,
            'roe': latest.get('roe', None),
            'gross_margin': latest.get('gross_margin', None),
            'debt_to_assets': latest.get('debt_to_assets', None),
            'net_profit': latest.get('net_profit', None),
            'operating_revenue': latest.get('operating_revenue', None),
        }
    
    except Exception as e:
        print(f'❌ 获取财务指标失败：{e}')
        return None


def get_hk_daily(ts_code, start_date=None, end_date=None):
    """
    获取港股日线数据 (备份数据源)
    
    Args:
        ts_code: 股票代码 (00700.HK)
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        DataFrame: 日线数据
    """
    try:
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            from datetime import timedelta
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        df = pro.hk_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        return df if not df.empty else None
    
    except Exception as e:
        print(f'❌ 获取港股日线失败：{e}')
        return None


def get_hk_stock_basic():
    """
    获取港股股票基本信息 (备份数据源)
    
    Returns:
        DataFrame: 港股基本信息
    """
    try:
        df = pro.stock_basic(exchange='HK', list_status='L', fields='ts_code,symbol,name,industry,list_date')
        return df if not df.empty else None
    
    except Exception as e:
        print(f'❌ 获取港股基本信息失败：{e}')
        return None


# ============ 测试函数 ============
def test_all():
    """测试所有功能"""
    print('='*80)
    print('🇨🇳 Tushare 数据接口测试')
    print('='*80)
    print()
    
    # 1. A 股指数
    print('【1. A 股指数】')
    index_data = get_cn_index('000001.SH')
    if index_data:
        print(f'✅ 上证指数：{index_data["close"]:.2f} ({index_data["change_pct"]:+.2f}%)')
    else:
        print('❌ 获取失败')
    print()
    
    # 2. A 股个股
    print('【2. A 股个股 - 贵州茅台】')
    stock_df = get_cn_stock_daily('600519.SH')
    if stock_df is not None:
        latest = stock_df.iloc[0]
        change = (latest['close'] - latest['pre_close']) / latest['pre_close'] * 100
        print(f'✅ 贵州茅台：{latest["close"]:.2f} 元 ({change:+.2f}%)')
    else:
        print('❌ 获取失败')
    print()
    
    # 3. 财务指标
    print('【3. 财务指标 - 贵州茅台】')
    fina = get_cn_financial_indicator('600519.SH')
    if fina:
        print(f'✅ ROE: {fina["roe"]:.2f}%')
        print(f'✅ 资产负债率：{fina["debt_to_assets"]:.2f}%')
    else:
        print('❌ 获取失败')
    print()
    
    # 4. 港股 (备份)
    print('【4. 港股备份数据 - 腾讯控股】')
    hk_df = get_hk_daily('00700.HK')
    if hk_df is not None:
        latest = hk_df.iloc[0]
        print(f'✅ 腾讯控股：{latest["close"]:.2f} HKD (日期：{latest["trade_date"]})')
    else:
        print('❌ 获取失败')
    print()
    
    print('='*80)
    print('✅ Tushare 数据接口测试完成')
    print('='*80)


if __name__ == '__main__':
    test_all()
