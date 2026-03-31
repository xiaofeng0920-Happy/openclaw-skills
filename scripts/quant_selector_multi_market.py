#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多市场量化选股系统 - 支持 A 股/港股/美股
根据市场自动加载对应模型配置

作者：小巴
日期：2026-03-26
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from futu import *
except ImportError:
    print("❌ 未安装 futu-api，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "futu-api", "-q"])
    from futu import *

# ============ 配置 ============
BASE_DIR = Path(__file__).parent
CONFIG_DIR = BASE_DIR.parent / 'config'
REPORTS_DIR = BASE_DIR.parent / 'reports'

OPEND_HOST = '127.0.0.1'
OPEND_PORT = 11111

# ============================


def load_market_model(market: str) -> dict:
    """加载市场专用模型配置"""
    model_file = CONFIG_DIR / f'model_{market}.json'
    
    if not model_file.exists():
        print(f"⚠️ 模型配置文件不存在：{model_file}")
        print("使用默认配置")
        return get_default_config(market)
    
    with open(model_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_default_config(market: str) -> dict:
    """默认配置"""
    if market == 'CN':
        return {
            "market": "CN",
            "factor_weights": {
                "momentum": 0.25,
                "value": 0.15,
                "quality": 0.25,
                "growth": 0.15,
                "sentiment": 0.20
            }
        }
    elif market == 'HK':
        return {
            "market": "HK",
            "factor_weights": {
                "momentum": 0.30,
                "value": 0.30,
                "quality": 0.25,
                "growth": 0.05,
                "sentiment": 0.10
            }
        }
    else:
        return {
            "market": "US",
            "factor_weights": {
                "momentum": 0.40,
                "value": 0.30,
                "quality": 0.30
            }
        }


def connect_opend() -> OpenQuoteContext:
    """连接 OpenD"""
    quote_ctx = OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    ret, state = quote_ctx.get_global_state()
    
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！")
        sys.exit(1)
    
    print("✅ OpenD 连接成功")
    return quote_ctx


def get_stock_list(quote_ctx: OpenQuoteContext, market: str) -> pd.DataFrame:
    """获取股票列表"""
    market_map = {
        'HK': Market.HK,
        'US': Market.US,
        'CN': Market.SH
    }
    
    print(f"正在获取 {market} 股市场列表...")
    
    if market == 'CN':
        ret_sh, data_sh = quote_ctx.get_stock_basicinfo(Market.SH, SecurityType.STOCK)
        ret_sz, data_sz = quote_ctx.get_stock_basicinfo(Market.SZ, SecurityType.STOCK)
        
        data_list = []
        if ret_sh == RET_OK and not data_sh.empty:
            data_list.append(data_sh)
            print(f"  沪市：{len(data_sh)} 只")
        if ret_sz == RET_OK and not data_sz.empty:
            data_list.append(data_sz)
            print(f"  深市：{len(data_sz)} 只")
        
        if data_list:
            data = pd.concat(data_list, ignore_index=True)
            print(f"✅ 获取到 {len(data)} 只 A 股")
            return data
        else:
            return pd.DataFrame()
    else:
        ret, data = quote_ctx.get_stock_basicinfo(market_map[market], SecurityType.STOCK)
        
        if ret != RET_OK or data.empty:
            return pd.DataFrame()
        
        print(f"✅ 获取到 {len(data)} 只 {market}股")
        return data


def calculate_score_by_market(row: pd.Series, model: dict, market: str) -> float:
    """根据市场模型计算综合评分"""
    score = 0.0
    factor_weights = model.get('factor_weights', {})
    
    # 动量因子
    if 'momentum' in factor_weights and factor_weights['momentum'] > 0:
        momentum_score = calculate_momentum_score(row, market)
        score += momentum_score * factor_weights['momentum']
    
    # 价值因子
    if 'value' in factor_weights and factor_weights['value'] > 0:
        value_score = calculate_value_score(row, market)
        score += value_score * factor_weights['value']
    
    # 质量因子
    if 'quality' in factor_weights and factor_weights['quality'] > 0:
        quality_score = calculate_quality_score(row, market)
        score += quality_score * factor_weights['quality']
    
    # 成长因子
    if 'growth' in factor_weights and factor_weights['growth'] > 0:
        growth_score = calculate_growth_score(row, market)
        score += growth_score * factor_weights['growth']
    
    # 情绪因子
    if 'sentiment' in factor_weights and factor_weights['sentiment'] > 0:
        sentiment_score = calculate_sentiment_score(row, market)
        score += sentiment_score * factor_weights['sentiment']
    
    return score


def calculate_momentum_score(row: pd.Series, market: str) -> float:
    """动量因子评分"""
    score = 0.0
    
    # 20 日涨幅
    if 'change_20d' in row and row['change_20d']:
        change = row['change_20d']
        if 10 <= change <= 50:
            score += 40
        elif change > 0:
            score += max(0, 20 - abs(change - 30))
    
    # RSI
    if 'rsi_14' in row and row['rsi_14']:
        rsi = row['rsi_14']
        if 50 <= rsi <= 70:
            score += 30
        elif 30 <= rsi < 50 or 70 < rsi <= 80:
            score += 15
    
    # 成交量
    if 'volume_ratio' in row and row['volume_ratio']:
        vol = row['volume_ratio']
        if 1.5 <= vol <= 3:
            score += 30
        elif vol > 1:
            score += 15
    
    return score


def calculate_value_score(row: pd.Series, market: str) -> float:
    """价值因子评分"""
    score = 0.0
    
    # PE
    if row.get('pe_ratio', None) and row['pe_ratio'] > 0:
        pe = row['pe_ratio']
        if market == 'CN':
            pe_max = 50
        else:
            pe_max = 30
        
        if pe < 5:
            score += 40
        elif pe < pe_max:
            score += 40 * (1 - (pe - 5) / (pe_max - 5))
    
    # PB
    if row.get('pb_ratio', None) and row['pb_ratio'] > 0:
        pb = row['pb_ratio']
        if pb < 1:
            score += 35
        elif pb < 5:
            score += 35 * (1 - (pb - 1) / 4)
    
    # 股息率
    if row.get('dividend_ratio', None) and row['dividend_ratio'] > 0:
        div = row['dividend_ratio']
        score += min(25, div * 5)
    
    return score


def calculate_quality_score(row: pd.Series, market: str) -> float:
    """质量因子评分"""
    score = 0.0
    
    # ROE
    if row.get('roe', None) and row['roe'] > 0:
        roe = row['roe']
        if roe >= 20:
            score += 45
        elif roe >= 10:
            score += 45 * (roe / 20)
        else:
            score += 45 * (roe / 10) * 0.5
    
    # 毛利率
    if row.get('gross_margin', None) and row['gross_margin'] > 0:
        gm = row['gross_margin']
        if gm >= 40:
            score += 30
        elif gm >= 20:
            score += 30 * (gm / 40)
        else:
            score += 30 * (gm / 20) * 0.5
    
    # 负债率
    if row.get('debt_ratio', None) and row['debt_ratio'] > 0:
        dr = row['debt_ratio']
        if dr <= 30:
            score += 25
        elif dr <= 60:
            score += 25 * (1 - (dr - 30) / 30)
        else:
            score += max(0, 25 * (1 - dr / 100))
    
    return score


def calculate_growth_score(row: pd.Series, market: str) -> float:
    """成长因子评分"""
    score = 0.0
    
    # 营收增长
    if row.get('revenue_growth', None):
        rev_g = row['revenue_growth']
        if rev_g >= 30:
            score += 50
        elif rev_g >= 15:
            score += 50 * (rev_g / 30)
        elif rev_g > 0:
            score += 50 * (rev_g / 15) * 0.5
    
    # 利润增长
    if row.get('earnings_growth', None):
        earn_g = row['earnings_growth']
        if earn_g >= 30:
            score += 50
        elif earn_g >= 15:
            score += 50 * (earn_g / 30)
        elif earn_g > 0:
            score += 50 * (earn_g / 15) * 0.5
    
    return score


def calculate_sentiment_score(row: pd.Series, market: str) -> float:
    """情绪因子评分"""
    score = 0.0
    
    # 换手率
    if row.get('turnover_rate', None):
        tr = row['turnover_rate']
        if 3 <= tr <= 10:
            score += 40
        elif tr > 0:
            score += 20
    
    # 波动率
    if row.get('volatility', None):
        vol = row['volatility']
        if vol < 0.3:
            score += 30
        elif vol < 0.5:
            score += 20
        else:
            score += 10
    
    return score


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='多市场量化选股系统')
    parser.add_argument('--market', type=str, default='HK', choices=['HK', 'US', 'CN'],
                        help='市场 (HK/US/CN)')
    parser.add_argument('--top', type=int, default=20, help='显示前 N 只股票')
    parser.add_argument('--output', type=str, default=None, help='输出文件路径')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"📊 多市场量化选股系统")
    print(f"{'='*60}")
    print(f"市场：{args.market}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # 加载市场模型
    model = load_market_model(args.market)
    print(f"📋 使用模型：{model.get('market_name', args.market)}")
    print(f"因子权重:")
    for factor, weight in model.get('factor_weights', {}).items():
        print(f"  - {factor}: {weight*100:.0f}%")
    print()
    
    # 连接 OpenD
    quote_ctx = connect_opend()
    
    try:
        # 获取股票列表
        stock_list = get_stock_list(quote_ctx, args.market)
        
        if stock_list.empty:
            print("❌ 未获取到股票列表")
            return
        
        codes = stock_list['code'].tolist()
        
        # 获取市场快照（简化版，实际需要分批获取）
        print(f"正在获取 {len(codes)} 只股票数据...")
        # 这里简化处理，实际需要调用 get_market_snapshot
        
        print(f"\n✅ 选股完成")
        print(f"📁 结果将保存到：{args.output}")
    
    finally:
        quote_ctx.close()


if __name__ == "__main__":
    main()
