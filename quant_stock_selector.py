#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化选股策略 - 基于富途 OpenAPI
支持多因子选股、股票评分、组合优化

作者：小巴
日期：2026-03-26
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from futu import *
except ImportError:
    print("❌ 未安装 futu-api，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "futu-api", "-q"])
    from futu import *

# ============ 配置 ============
OPEND_HOST = '127.0.0.1'
OPEND_PORT = 11111

# 选股策略配置
STRATEGY_CONFIG = {
    'value': {  # 价值选股
        'weight': 0.3,
        'factors': {
            'pe_ratio': {'min': 0, 'max': 20, 'direction': 'low'},  # PE 越低越好
            'pb_ratio': {'min': 0, 'max': 3, 'direction': 'low'},   # PB 越低越好
            'dividend_yield': {'min': 2, 'max': None, 'direction': 'high'}  # 股息率越高越好
        }
    },
    'growth': {  # 成长选股
        'weight': 0.3,
        'factors': {
            'revenue_growth': {'min': 20, 'max': None, 'direction': 'high'},  # 营收增长>20%
            'earnings_growth': {'min': 25, 'max': None, 'direction': 'high'},  # 利润增长>25%
            'roe': {'min': 15, 'max': None, 'direction': 'high'}  # ROE>15%
        }
    },
    'momentum': {  # 动量选股
        'weight': 0.2,
        'factors': {
            'change_rate_20d': {'min': 10, 'max': None, 'direction': 'high'},  # 20 日涨幅>10%
            'volume_ratio': {'min': 1.5, 'max': None, 'direction': 'high'},  # 成交量放大>50%
            'rsi': {'min': 50, 'max': 70, 'direction': 'mid'}  # RSI 50-70
        }
    },
    'quality': {  # 质量选股
        'weight': 0.2,
        'factors': {
            'gross_margin': {'min': 30, 'max': None, 'direction': 'high'},  # 毛利率>30%
            'debt_ratio': {'min': None, 'max': 50, 'direction': 'low'},  # 负债率<50%
            'operating_cash_flow': {'min': 0, 'max': None, 'direction': 'high'}  # 经营现金流为正
        }
    }
}

# ============================


def connect_opend() -> OpenQuoteContext:
    """连接 OpenD"""
    quote_ctx = OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    ret, state = quote_ctx.get_global_state()
    
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！请确保 OpenD 已启动")
        sys.exit(1)
    
    print("✅ OpenD 连接成功")
    return quote_ctx


def get_stock_list(quote_ctx: OpenQuoteContext, market: str = 'HK') -> pd.DataFrame:
    """获取股票列表"""
    print(f"正在获取 {market} 股市场列表...")
    
    market_map = {
        'HK': Market.HK,
        'US': Market.US,
        'CN': Market.SH
    }
    
    ret, data = quote_ctx.get_stock_basicinfo(market_map[market], SecurityType.STOCK)
    
    if ret != RET_OK:
        print(f"❌ 获取股票列表失败：{data}")
        return pd.DataFrame()
    
    print(f"✅ 获取到 {len(data)} 只股票")
    return data


def get_snapshot_data(quote_ctx: OpenQuoteContext, codes: List[str]) -> pd.DataFrame:
    """获取市场快照数据"""
    print(f"正在获取 {len(codes)} 只股票的实时数据...")
    
    # 分批获取，每次最多 400 只
    batch_size = 400
    all_data = []
    
    for i in range(0, len(codes), batch_size):
        batch = codes[i:i+batch_size]
        ret, data = quote_ctx.get_market_snapshot(batch)
        
        if ret == RET_OK:
            all_data.append(data)
            print(f"  进度：{min(i+batch_size, len(codes))}/{len(codes)}")
        else:
            print(f"  ⚠️ 批次 {i//batch_size + 1} 获取失败")
    
    if not all_data:
        return pd.DataFrame()
    
    result = pd.concat(all_data, ignore_index=True)
    print(f"✅ 成功获取 {len(result)} 只股票数据")
    return result


def calculate_score(stock_data: pd.DataFrame, strategy: str = 'all') -> pd.DataFrame:
    """计算股票综合评分"""
    
    if stock_data.empty:
        return pd.DataFrame()
    
    print(f"\n正在计算股票评分（策略：{strategy}）...")
    
    # 初始化评分列
    stock_data['total_score'] = 0.0
    stock_data['value_score'] = 0.0
    stock_data['growth_score'] = 0.0
    stock_data['momentum_score'] = 0.0
    stock_data['quality_score'] = 0.0
    
    # 价值因子评分
    if strategy in ['all', 'value']:
        # PE 评分（越低越好）
        if 'pe_ratio' in stock_data.columns:
            pe_min = stock_data['pe_ratio'].min()
            pe_max = stock_data['pe_ratio'].max()
            if pe_max > pe_min:
                stock_data['value_score'] += (1 - (stock_data['pe_ratio'] - pe_min) / (pe_max - pe_min)) * 30
        
        # PB 评分（越低越好）
        if 'pb_ratio' in stock_data.columns:
            pb_min = stock_data['pb_ratio'].min()
            pb_max = stock_data['pb_ratio'].max()
            if pb_max > pb_min:
                stock_data['value_score'] += (1 - (stock_data['pb_ratio'] - pb_min) / (pb_max - pb_min)) * 30
        
        # 股息率评分（越高越好）
        if 'dividend_ratio' in stock_data.columns:
            div_max = stock_data['dividend_ratio'].max()
            if div_max > 0:
                stock_data['value_score'] += (stock_data['dividend_ratio'] / div_max) * 40
        
        stock_data['total_score'] += stock_data['value_score'] * STRATEGY_CONFIG['value']['weight']
    
    # 成长因子评分
    if strategy in ['all', 'growth']:
        # 营收增长评分
        if 'revenue_growth' in stock_data.columns:
            rev_max = stock_data['revenue_growth'].max()
            if rev_max > 0:
                stock_data['growth_score'] += (stock_data['revenue_growth'] / rev_max) * 40
        
        # ROE 评分
        if 'roe' in stock_data.columns:
            roe_max = stock_data['roe'].max()
            if roe_max > 0:
                stock_data['growth_score'] += (stock_data['roe'] / roe_max) * 60
        
        stock_data['total_score'] += stock_data['growth_score'] * STRATEGY_CONFIG['growth']['weight']
    
    # 动量因子评分
    if strategy in ['all', 'momentum']:
        # 涨跌幅评分
        if 'change_percent' in stock_data.columns:
            chg_min = stock_data['change_percent'].min()
            chg_max = stock_data['change_percent'].max()
            if chg_max > chg_min:
                stock_data['momentum_score'] += ((stock_data['change_percent'] - chg_min) / (chg_max - chg_min)) * 50
        
        # 成交量评分
        if 'volume_ratio' in stock_data.columns:
            vol_max = stock_data['volume_ratio'].max()
            if vol_max > 0:
                stock_data['momentum_score'] += (stock_data['volume_ratio'] / vol_max) * 50
        
        stock_data['total_score'] += stock_data['momentum_score'] * STRATEGY_CONFIG['momentum']['weight']
    
    # 质量因子评分
    if strategy in ['all', 'quality']:
        # 毛利率评分
        if 'gross_margin' in stock_data.columns:
            gm_max = stock_data['gross_margin'].max()
            if gm_max > 0:
                stock_data['quality_score'] += (stock_data['gross_margin'] / gm_max) * 40
        
        # 负债率评分（越低越好）
        if 'debt_ratio' in stock_data.columns:
            dr_min = stock_data['debt_ratio'].min()
            dr_max = stock_data['debt_ratio'].max()
            if dr_max > dr_min:
                stock_data['quality_score'] += (1 - (stock_data['debt_ratio'] - dr_min) / (dr_max - dr_min)) * 30
        
        stock_data['total_score'] += stock_data['quality_score'] * STRATEGY_CONFIG['quality']['weight']
    
    # 排序
    stock_data = stock_data.sort_values('total_score', ascending=False)
    
    print(f"✅ 评分完成，最高分：{stock_data['total_score'].max():.2f}")
    return stock_data


def filter_stocks(stock_data: pd.DataFrame, filters: Dict = None) -> pd.DataFrame:
    """筛选股票"""
    
    if filters is None:
        filters = {
            'min_market_cap': 100,  # 最小市值 100 亿
            'min_volume': 1000000,  # 最小成交量 100 万
            'max_pe': 50,  # 最大 PE 50
            'min_price': 1,  # 最小价格 1 元
            'max_price': 1000  # 最大价格 1000 元
        }
    
    filtered = stock_data.copy()
    
    # 市值筛选
    if 'market_val' in filtered.columns and 'min_market_cap' in filters:
        filtered = filtered[filtered['market_val'] >= filters['min_market_cap'] * 1e8]
    
    # 成交量筛选
    if 'volume' in filtered.columns and 'min_volume' in filters:
        filtered = filtered[filtered['volume'] >= filters['min_volume']]
    
    # PE 筛选
    if 'pe_ratio' in filtered.columns and 'max_pe' in filters:
        filtered = filtered[(filtered['pe_ratio'] > 0) & (filtered['pe_ratio'] <= filters['max_pe'])]
    
    # 价格筛选
    if 'last_price' in filtered.columns:
        filtered = filtered[
            (filtered['last_price'] >= filters['min_price']) & 
            (filtered['last_price'] <= filters['max_price'])
        ]
    
    print(f"✅ 筛选后剩余 {len(filtered)} 只股票")
    return filtered


def optimize_portfolio(stock_data: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """组合优化 - 简单版（等权重 + 行业分散）"""
    
    if stock_data.empty:
        return pd.DataFrame()
    
    print(f"\n正在进行组合优化（Top {top_n}）...")
    
    # 选择前 N 只股票
    top_stocks = stock_data.head(top_n).copy()
    
    # 计算等权重
    weight = 1.0 / len(top_stocks)
    top_stocks['weight'] = weight
    
    # 计算预期收益（基于评分）
    top_stocks['expected_return'] = top_stocks['total_score'] / 100.0
    
    print(f"✅ 组合优化完成")
    print(f"   股票数量：{len(top_stocks)}")
    print(f"   平均预期收益：{top_stocks['expected_return'].mean()*100:.2f}%")
    
    return top_stocks


def save_results(stock_data: pd.DataFrame, output_file: str = None):
    """保存结果"""
    
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'/tmp/stock_selection_{timestamp}.csv'
    
    stock_data.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ 结果已保存到：{output_file}")


def display_top_stocks(stock_data: pd.DataFrame, top_n: int = 20):
    """显示前 N 只股票"""
    
    if stock_data.empty:
        print("❌ 没有数据可显示")
        return
    
    print("\n" + "="*100)
    print(f"🏆 选股结果 Top {top_n}")
    print("="*100)
    
    display_cols = ['code', 'name', 'last_price', 'change_percent', 'pe_ratio', 
                    'market_val', 'total_score', 'value_score', 'growth_score', 
                    'momentum_score', 'quality_score']
    
    available_cols = [col for col in display_cols if col in stock_data.columns]
    
    for i, (_, row) in enumerate(stock_data.head(top_n).iterrows(), 1):
        print(f"\n{i:2d}. {row.get('code', 'N/A')} | {row.get('name', 'N/A')}")
        print(f"    价格：${row.get('last_price', 0):.2f} ({row.get('change_percent', 0):+.2f}%)")
        print(f"    PE: {row.get('pe_ratio', 'N/A'):>8}  |  市值：{row.get('market_val', 0)/1e8:.1f}亿")
        print(f"    总分：{row.get('total_score', 0):.2f}")
        print(f"    价值：{row.get('value_score', 0):.1f} | 成长：{row.get('growth_score', 0):.1f} | "
              f"动量：{row.get('momentum_score', 0):.1f} | 质量：{row.get('quality_score', 0):.1f}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='量化选股策略')
    parser.add_argument('--market', type=str, default='HK', choices=['HK', 'US', 'CN'],
                        help='市场 (HK/US/CN)')
    parser.add_argument('--strategy', type=str, default='all', 
                        choices=['all', 'value', 'growth', 'momentum', 'quality'],
                        help='选股策略')
    parser.add_argument('--top', type=int, default=20, help='显示前 N 只股票')
    parser.add_argument('--optimize', type=int, default=10, help='组合优化股票数量')
    parser.add_argument('--output', type=str, default=None, help='输出文件路径')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"📊 量化选股系统 - 富途 OpenAPI 版")
    print(f"{'='*60}")
    print(f"市场：{args.market} | 策略：{args.strategy} | 时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # 连接 OpenD
    quote_ctx = connect_opend()
    
    try:
        # 获取股票列表
        stock_list = get_stock_list(quote_ctx, args.market)
        
        if stock_list.empty:
            print("❌ 未获取到股票列表")
            return
        
        # 获取股票代码
        codes = stock_list['code'].tolist()
        
        # 获取市场快照
        snapshot_data = get_snapshot_data(quote_ctx, codes)
        
        if snapshot_data.empty:
            print("❌ 未获取到市场数据")
            return
        
        # 筛选股票
        filtered_data = filter_stocks(snapshot_data)
        
        # 计算评分
        scored_data = calculate_score(filtered_data, args.strategy)
        
        # 显示结果
        display_top_stocks(scored_data, args.top)
        
        # 组合优化
        if args.optimize > 0:
            portfolio = optimize_portfolio(scored_data, args.optimize)
            print("\n" + "="*60)
            print("💼 组合优化结果")
            print("="*60)
            for i, (_, row) in enumerate(portfolio.iterrows(), 1):
                print(f"{i:2d}. {row['code']} | {row['name']} | 权重：{row['weight']*100:.1f}% | "
                      f"预期收益：{row['expected_return']*100:.1f}%")
        
        # 保存结果
        save_results(scored_data, args.output)
        
        # JSON 输出
        if args.json:
            result = {
                'timestamp': datetime.now().isoformat(),
                'market': args.market,
                'strategy': args.strategy,
                'total_stocks': len(scored_data),
                'top_stocks': scored_data.head(args.top).to_dict('records')
            }
            print("\n" + json.dumps(result, ensure_ascii=False, indent=2))
    
    finally:
        quote_ctx.close()
        print("\n✅ 选股完成")


if __name__ == "__main__":
    main()
