#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一行情数据接口
- 实时行情：A 股/港股用富途，美股用 Finnhub
- 备份数据：A 股/港股用 Tushare
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# ============ 富途 OpenD 配置 ============
try:
    from futu import *
    FUTU_AVAILABLE = True
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
except Exception as e:
    FUTU_AVAILABLE = False
    print(f'⚠️ 富途 OpenD 不可用：{e}')
    quote_ctx = None

# ============ Tushare 配置 ============
try:
    import tushare as ts
    TUSHARE_TOKEN = '1dbdfba7c672d47f22db86f586d5aff9730124b321c2ebdda91890d3'
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    TUSHARE_AVAILABLE = True
except Exception as e:
    TUSHARE_AVAILABLE = False
    print(f'⚠️ Tushare 不可用：{e}')
    pro = None

# ============ Finnhub 配置 ============
try:
    import requests
    FINNHUB_API_KEY = 'd6r9v6hr01qgdhqdor50d6r9v6hr01qgdhqdor5g'
    FINNHUB_AVAILABLE = True
except Exception as e:
    FINNHUB_AVAILABLE = False
    print(f'⚠️ Finnhub 不可用：{e}')


# ============================

def get_realtime_quote(code):
    """
    获取实时行情 (主数据源 + 备份)
    
    Args:
        code: 股票代码 (HK.00700, 600519.SH, US.AAPL)
        
    Returns:
        dict: 实时行情数据
    """
    
    # 判断市场
    if code.startswith('HK.'):
        market = 'HK'
    elif code.startswith('US.'):
        market = 'US'
    elif '.SH' in code or '.SZ' in code:
        market = 'CN'
    else:
        market = 'UNKNOWN'
    
    # ============ A 股/港股：优先富途 ============
    if market in ['HK', 'CN']:
        # 主数据源：富途
        if FUTU_AVAILABLE and quote_ctx:
            try:
                ret, data = quote_ctx.get_market_snapshot(code)
                if ret == RET_OK and not data.empty:
                    row = data.iloc[0]
                    return {
                        'code': code,
                        'name': row.get('name', ''),
                        'price': row['last_price'],
                        'change_pct': row.get('change_rate', 0) * 100 if 'change_rate' in row else 0,
                        'pe': row.get('pe_ratio', None),
                        'pb': row.get('pb_ratio', None),
                        'volume': row.get('volume', 0),
                        'market_val': row.get('total_market_val', 0),
                        'source': '富途 OpenD (实时)',
                        'timestamp': datetime.now()
                    }
            except Exception as e:
                print(f'⚠️ 富途获取 {code} 失败，切换到 Tushare: {e}')
        
        # 备份数据源：Tushare
        if TUSHARE_AVAILABLE and pro:
            try:
                if market == 'CN':
                    # A 股
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=5)).strftime('%Y%m%d')
                    df = pro.daily(ts_code=code, start_date=start_date, end_date=end_date)
                    
                    if not df.empty:
                        latest = df.iloc[0]
                        change_pct = (latest['close'] - latest['pre_close']) / latest['pre_close'] * 100
                        return {
                            'code': code,
                            'name': code.split('.')[0],
                            'price': latest['close'],
                            'change_pct': change_pct,
                            'pe': None,
                            'pb': None,
                            'volume': latest.get('vol', 0),
                            'amount': latest.get('amount', 0),
                            'source': 'Tushare (备份)',
                            'timestamp': datetime.now()
                        }
                
                elif market == 'HK':
                    # 港股
                    hk_code = code.replace('.', '')  # HK.00700 → HK00700
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=5)).strftime('%Y%m%d')
                    df = pro.hk_daily(ts_code=hk_code, start_date=start_date, end_date=end_date)
                    
                    if not df.empty:
                        latest = df.iloc[0]
                        return {
                            'code': code,
                            'name': code.split('.')[1] if '.' in code else code,
                            'price': latest['close'],
                            'change_pct': 0,  # Tushare 港股需要计算
                            'pe': None,
                            'pb': None,
                            'volume': latest.get('vol', 0),
                            'source': 'Tushare (备份)',
                            'timestamp': datetime.now()
                        }
            except Exception as e:
                print(f'⚠️ Tushare 获取 {code} 失败：{e}')
        
        return None
    
    # ============ 美股：Finnhub ============
    elif market == 'US':
        if FINNHUB_AVAILABLE:
            try:
                symbol = code.replace('US.', '')
                url = 'https://finnhub.io/api/v1/quote'
                params = {'symbol': symbol, 'token': FINNHUB_API_KEY}
                response = requests.get(url, params=params, timeout=5)
                data = response.json()
                
                if response.status_code == 200 and data.get('c'):
                    current = data['c']
                    change = data['d']
                    change_pct = (change / data['pc'] * 100) if data['pc'] > 0 else 0
                    
                    return {
                        'code': code,
                        'name': symbol,
                        'price': current,
                        'change_pct': change_pct,
                        'pe': None,
                        'pb': None,
                        'open': data['o'],
                        'high': data['h'],
                        'low': data['l'],
                        'prev_close': data['pc'],
                        'source': 'Finnhub (实时)',
                        'timestamp': datetime.now()
                    }
            except Exception as e:
                print(f'⚠️ Finnhub 获取 {code} 失败：{e}')
        
        return None
    
    else:
        print(f'❌ 不支持的市场：{market}')
        return None


def get_index_quote(index_code):
    """
    获取指数行情
    
    Args:
        index_code: 指数代码 (HK.HSI, 000001.SH, ^GSPC)
        
    Returns:
        dict: 指数数据
    """
    
    if index_code == 'HK.HSI':
        # 恒生指数 - 富途
        if FUTU_AVAILABLE and quote_ctx:
            ret, data = quote_ctx.get_market_snapshot(index_code)
            if ret == RET_OK and not data.empty:
                row = data.iloc[0]
                return {
                    'code': index_code,
                    'name': '恒生指数',
                    'price': row['last_price'],
                    'change_pct': row.get('change_rate', 0) * 100,
                    'source': '富途 OpenD'
                }
    
    elif index_code == '000001.SH':
        # 上证指数 - 富途优先
        if FUTU_AVAILABLE and quote_ctx:
            # 富途获取 A 股指数
            ret, data = quote_ctx.get_market_snapshot('SH.000001')
            if ret == RET_OK and not data.empty:
                row = data.iloc[0]
                return {
                    'code': index_code,
                    'name': '上证指数',
                    'price': row['last_price'],
                    'change_pct': row.get('change_rate', 0) * 100,
                    'source': '富途 OpenD'
                }
        
        # Tushare 备份
        if TUSHARE_AVAILABLE and pro:
            df = pro.index_daily(ts_code=index_code, start_date='20260325', end_date='20260330')
            if not df.empty:
                latest = df.iloc[0]
                change_pct = (latest['close'] - latest['pre_close']) / latest['pre_close'] * 100
                return {
                    'code': index_code,
                    'name': '上证指数',
                    'price': latest['close'],
                    'change_pct': change_pct,
                    'source': 'Tushare (备份)'
                }
    
    return None


def test_all_sources():
    """测试所有数据源"""
    print('='*80)
    print('📊 数据源测试')
    print('='*80)
    print()
    
    # 测试富途
    print(f'富途 OpenD: {"✅ 可用" if FUTU_AVAILABLE else "❌ 不可用"}')
    
    # 测试 Tushare
    print(f'Tushare: {"✅ 可用" if TUSHARE_AVAILABLE else "❌ 不可用"}')
    
    # 测试 Finnhub
    print(f'Finnhub: {"✅ 可用" if FINNHUB_AVAILABLE else "❌ 不可用"}')
    
    print()
    print('-'*80)
    print('实时行情测试:')
    print('-'*80)
    
    # 测试港股
    print('\n【港股 - 腾讯控股】')
    data = get_realtime_quote('HK.00700')
    if data:
        print(f'✅ {data["code"]}: ${data["price"]:.2f} ({data["change_pct"]:+.2f}%) - {data["source"]}')
    else:
        print('❌ 获取失败')
    
    # 测试 A 股
    print('\n【A 股 - 贵州茅台】')
    data = get_realtime_quote('600519.SH')
    if data:
        print(f'✅ {data["code"]}: ¥{data["price"]:.2f} ({data["change_pct"]:+.2f}%) - {data["source"]}')
    else:
        print('❌ 获取失败')
    
    # 测试美股
    print('\n【美股 - 苹果】')
    data = get_realtime_quote('US.AAPL')
    if data:
        print(f'✅ {data["code"]}: ${data["price"]:.2f} ({data["change_pct"]:+.2f}%) - {data["source"]}')
    else:
        print('❌ 获取失败')
    
    print()
    print('='*80)
    print('✅ 数据源测试完成')
    print('='*80)


if __name__ == '__main__':
    test_all_sources()
