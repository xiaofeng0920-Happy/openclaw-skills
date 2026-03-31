#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术指标计算 - 自动计算 MA/MACD/RSI 等技术指标
为持仓股票提供技术分析数据
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from futu import *

CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
TECH_CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/config/tech_indicators.json"

def load_portfolio():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_tech_config(config):
    import os
    os.makedirs(os.path.dirname(TECH_CONFIG_FILE), exist_ok=True)
    with open(TECH_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_kline_data(symbol, market='HK', days=200):
    """获取 K 线数据（使用富途 OpenD）"""
    try:
        from futu import OpenQuoteContext, RET_OK
        
        quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
        
        code = f"{market}.{symbol.replace('.HK', '')}"
        
        # 获取历史 K 线（日 K）
        ret, data = quote_ctx.get_history_kline(
            code=code,
            ktype='KL_D',
            autype='QFQ',
            max_count=days
        )
        
        quote_ctx.close()
        
        if ret == RET_OK and len(data) > 0:
            import pandas as pd
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'])
            df['open'] = pd.to_numeric(df['open'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['volume'] = pd.to_numeric(df['volume'])
            return df
        return None
    except Exception as e:
        print(f"获取 K 线失败 {symbol}: {e}")
        return None

def calculate_ma(data, periods=[5, 10, 20, 60]):
    """计算移动平均线"""
    result = {}
    for period in periods:
        result[f'MA{period}'] = round(data['close'].rolling(window=period).mean().iloc[-1], 2)
    return result

def calculate_macd(data):
    """计算 MACD"""
    exp1 = data['close'].ewm(span=12, adjust=False).mean()
    exp2 = data['close'].ewm(span=26, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        'MACD': round(macd_line.iloc[-1], 2),
        'Signal': round(signal_line.iloc[-1], 2),
        'Histogram': round(histogram.iloc[-1], 2)
    }

def calculate_rsi(data, period=14):
    """计算 RSI"""
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return {'RSI': round(rsi.iloc[-1], 2)}

def calculate_bollinger(data, period=20):
    """计算布林带"""
    middle = data['close'].rolling(window=period).mean()
    std = data['close'].rolling(window=period).std()
    upper = middle + (std * 2)
    lower = middle - (std * 2)
    
    current_price = data['close'].iloc[-1]
    
    return {
        'Upper': round(upper.iloc[-1], 2),
        'Middle': round(middle.iloc[-1], 2),
        'Lower': round(lower.iloc[-1], 2),
        'Position': '上轨' if current_price > upper.iloc[-1] else ('下轨' if current_price < lower.iloc[-1] else '中轨')
    }

def analyze_trend(data):
    """分析趋势"""
    current_price = data['close'].iloc[-1]
    ma20 = data['close'].rolling(window=20).mean().iloc[-1]
    ma60 = data['close'].rolling(window=60).mean().iloc[-1]
    
    if current_price > ma20 > ma60:
        trend = "多头排列 🟢"
    elif current_price < ma20 < ma60:
        trend = "空头排列 🔴"
    else:
        trend = "震荡 ⚪"
    
    return {'Trend': trend}

def calculate_all_indicators(symbol, market):
    """计算所有技术指标"""
    data = get_kline_data(symbol, market)
    
    if data is None or len(data) < 60:
        return None
    
    # 转换为 DataFrame
    df = pd.DataFrame(data)
    df['close'] = pd.to_numeric(df['close'])
    
    # 计算各项指标
    indicators = {
        'symbol': symbol,
        'timestamp': datetime.now().isoformat(),
        'current_price': round(df['close'].iloc[-1], 2)
    }
    
    indicators.update(calculate_ma(df))
    indicators.update(calculate_macd(df))
    indicators.update(calculate_rsi(df))
    indicators.update(calculate_bollinger(df))
    indicators.update(analyze_trend(df))
    
    return indicators

def send_feishu(message):
    import subprocess
    cmd = [
        "openclaw", "message", "send",
        "--channel", "feishu",
        "--target", "ou_636c8e8b7ad36d7fc28e6cf90c350fdd",
        "--message", message
    ]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"发送失败：{e}")

def generate_tech_report():
    print(f"[{datetime.now()}] 计算技术指标...")
    
    portfolio = load_portfolio()
    tech_config = {
        'last_updated': datetime.now().isoformat(),
        'indicators': {}
    }
    
    # 重点股票（持仓大的）
    key_stocks = [
        ('GOOGL', 'US'),
        ('BRK.B', 'US'),
        ('KO', 'US'),
        ('00883.HK', 'HK'),
        ('07709.HK', 'HK'),
        ('00700.HK', 'HK'),
    ]
    
    report_lines = ["📊 技术指标日报", f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    
    for symbol, market in key_stocks:
        print(f"  计算 {symbol}...")
        indicators = calculate_all_indicators(symbol, market)
        
        if indicators:
            tech_config['indicators'][symbol] = indicators
            
            # 生成简报
            report_lines.append(f"**{symbol}** ${indicators['current_price']}")
            report_lines.append(f"  趋势：{indicators['Trend']}")
            report_lines.append(f"  RSI: {indicators['RSI']} | MACD: {indicators['MACD']}")
            report_lines.append(f"  布林带：{indicators['Position']} (上{indicators['Upper']} 中{indicators['Middle']} 下{indicators['Lower']})")
            report_lines.append("")
    
    # 保存配置
    save_tech_config(tech_config)
    
    # 发送飞书
    if len(report_lines) > 3:
        send_feishu("\n".join(report_lines))
    
    print(f"✅ 已计算 {len(tech_config['indicators'])} 只股票技术指标")
    return True

if __name__ == "__main__":
    success = generate_tech_report()
    exit(0 if success else 1)
