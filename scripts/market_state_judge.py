#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市场状态判断系统

根据技术指标判断市场状态（牛/熊/震荡）

作者：小巴
日期：2026-03-26
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# ============ 配置 ============
BASE_DIR = Path('/Users/zhaoxf/.openclaw/skills/港股量化投资')
DATA_DIR = BASE_DIR / 'data'

# ============================


def load_market_index_data() -> pd.DataFrame:
    """
    加载市场指数数据（恒生指数）
    
    实际应用中应该从数据源获取
    这里使用模拟数据演示
    """
    print("正在加载市场指数数据...")
    
    # 模拟恒生指数数据
    dates = pd.date_range(start='2023-01-01', end='2026-03-26', freq='B')
    np.random.seed(42)
    
    # 生成指数序列（随机游走 + 趋势）
    n_days = len(dates)
    trend = np.linspace(0, 0.2, n_days)  # 20% 长期趋势
    noise = np.random.normal(0, 0.02, n_days)  # 2% 日波动
    index_values = 20000 * (1 + trend + noise.cumsum() / 100)
    
    df = pd.DataFrame({
        'date': dates,
        'close': index_values,
        'volume': np.random.uniform(80e9, 120e9, n_days)
    })
    
    print(f"✅ 加载 {len(df)} 天数据")
    return df


def calculate_ma(df: pd.DataFrame, windows: list = [20, 50, 200]) -> pd.DataFrame:
    """计算移动平均线"""
    data = df.copy()
    
    for window in windows:
        data[f'ma{window}'] = data['close'].rolling(window=window).mean()
    
    return data


def judge_market_state(df: pd.DataFrame) -> dict:
    """
    判断市场状态
    
    基于：
    1. 均线系统（20/50/200 日）
    2. 波动率（VIX 类似指标）
    3. 成交量
    4. 市场宽度（上涨/下跌股票数）
    """
    
    # 计算均线
    data = calculate_ma(df)
    
    # 获取最新数据
    latest = data.iloc[-1]
    prev = data.iloc[-5]  # 5 日前
    
    # 1. 均线判断
    ma20 = latest['ma20']
    ma50 = latest['ma50']
    ma200 = latest['ma200']
    current_price = latest['close']
    
    # 均线多头排列
    bull_ma = (current_price > ma20 > ma50 > ma200)
    # 均线空头排列
    bear_ma = (current_price < ma20 < ma50 < ma200)
    
    # 2. 价格相对 200 日均线位置
    price_vs_ma200 = (current_price - ma200) / ma200 * 100
    
    # 3. 波动率（20 日收益率标准差）
    data['return'] = data['close'].pct_change()
    volatility_20d = data['return'].rolling(20).std().iloc[-1] * np.sqrt(252) * 100
    
    # 4. 成交量趋势
    volume_ma20 = data['volume'].rolling(20).mean().iloc[-1]
    volume_ma60 = data['volume'].rolling(60).mean().iloc[-1]
    volume_trend = (volume_ma20 - volume_ma60) / volume_ma60 * 100
    
    # 5. 短期趋势（5 日涨跌）
    short_term_trend = (latest['close'] - prev['close']) / prev['close'] * 100
    
    # 综合判断
    score = 0
    
    # 均线得分（-2 到 +2）
    if bull_ma:
        score += 2
    elif bear_ma:
        score -= 2
    else:
        if current_price > ma200:
            score += 1
        else:
            score -= 1
    
    # 价格位置得分（-1 到 +1）
    if price_vs_ma200 > 10:
        score += 1
    elif price_vs_ma200 < -10:
        score -= 1
    
    # 波动率得分（低波动 +1，高波动 -1）
    if volatility_20d < 15:
        score += 1
    elif volatility_20d > 25:
        score -= 1
    
    # 成交量得分
    if volume_trend > 10:
        score += 0.5
    elif volume_trend < -10:
        score -= 0.5
    
    # 市场状态分类
    if score >= 3:
        state = 'bull'
        state_name = '牛市'
        confidence = min(1.0, score / 5)
    elif score <= -3:
        state = 'bear'
        state_name = '熊市'
        confidence = min(1.0, abs(score) / 5)
    else:
        state = 'oscillating'
        state_name = '震荡市'
        confidence = 1.0 - abs(score) / 5
    
    result = {
        'state': state,
        'state_name': state_name,
        'score': score,
        'confidence': confidence,
        'indicators': {
            'price': current_price,
            'ma20': ma20,
            'ma50': ma50,
            'ma200': ma200,
            'price_vs_ma200': price_vs_ma200,
            'volatility_20d': volatility_20d,
            'volume_trend': volume_trend,
            'short_term_trend': short_term_trend,
            'bull_ma': bull_ma,
            'bear_ma': bear_ma
        }
    }
    
    return result


def get_dynamic_weights(market_state: str) -> dict:
    """
    根据市场状态获取动态因子权重
    
    牛市：侧重动量和成长
    震荡市：平衡配置
    熊市：侧重价值和质量
    """
    
    if market_state == 'bull':
        # 牛市：进攻型
        return {
            'momentum': 0.50,
            'growth': 0.25,
            'value': 0.10,
            'quality': 0.10,
            'sentiment': 0.05
        }
    
    elif market_state == 'bear':
        # 熊市：防御型
        return {
            'value': 0.40,
            'quality': 0.35,
            'momentum': 0.10,
            'sentiment': 0.10,
            'growth': 0.05
        }
    
    else:  # oscillating
        # 震荡市：平衡型
        return {
            'value': 0.30,
            'quality': 0.25,
            'momentum': 0.25,
            'sentiment': 0.10,
            'growth': 0.10
        }


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"📊 市场状态判断系统")
    print(f"{'='*60}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # 加载数据
    index_data = load_market_index_data()
    
    # 判断市场状态
    state_result = judge_market_state(index_data)
    
    # 显示结果
    print(f"\n{'='*60}")
    print(f"市场状态：{state_result['state_name']}")
    print(f"置信度：{state_result['confidence']*100:.1f}%")
    print(f"综合得分：{state_result['score']:+.1f}")
    print(f"{'='*60}")
    
    print(f"\n技术指标:")
    indicators = state_result['indicators']
    print(f"  指数点位：{indicators['price']:.0f}")
    print(f"  20 日均线：{indicators['ma20']:.0f}")
    print(f"  50 日均线：{indicators['ma50']:.0f}")
    print(f"  200 日均线：{indicators['ma200']:.0f}")
    print(f"  相对 200 日均线：{indicators['price_vs_ma200']:+.1f}%")
    print(f"  20 日波动率：{indicators['volatility_20d']:.1f}%")
    print(f"  成交量趋势：{indicators['volume_trend']:+.1f}%")
    print(f"  5 日趋势：{indicators['short_term_trend']:+.1f}%")
    
    # 获取动态权重
    dynamic_weights = get_dynamic_weights(state_result['state'])
    
    print(f"\n{'='*60}")
    print(f"推荐因子权重（{state_result['state_name']}）:")
    print(f"{'='*60}")
    for factor, weight in dynamic_weights.items():
        print(f"  {factor}: {weight*100:.0f}%")
    
    # 保存结果
    import json
    result_file = BASE_DIR / f'market_state_{datetime.now().strftime("%Y%m%d")}.json'
    
    result = {
        'date': datetime.now().isoformat(),
        'market_state': {
            'state': state_result['state'],
            'state_name': state_result['state_name'],
            'score': float(state_result['score']),
            'confidence': float(state_result['confidence']),
            'indicators': {k: float(v) for k, v in state_result['indicators'].items()}
        },
        'dynamic_weights': dynamic_weights
    }
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存：{result_file.name}")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
