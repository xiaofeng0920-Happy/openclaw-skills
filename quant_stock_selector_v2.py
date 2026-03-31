#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化选股策略 - 增强版
基于富途 OpenAPI + K 线数据计算

作者：小巴
日期：2026-03-26
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
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
OPEND_HOST = '127.0.0.1'
OPEND_PORT = 11111

# 选股参数
FILTERS = {
    'min_market_cap': 50,    # 最小市值 50 亿港元
    'min_volume': 500000,    # 最小成交量 50 万
    'max_pe': 30,            # 最大 PE 30
    'min_price': 2,          # 最小价格 2 港元
    'max_price': 500         # 最大价格 500 港元
}

# ============================


def connect_opend() -> OpenQuoteContext:
    """连接 OpenD"""
    quote_ctx = OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    ret, state = quote_ctx.get_global_state()
    
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！")
        sys.exit(1)
    
    print("✅ OpenD 连接成功")
    return quote_ctx


def get_hk_stocks(quote_ctx: OpenQuoteContext) -> pd.DataFrame:
    """获取港股列表"""
    print("正在获取港股列表...")
    ret, data = quote_ctx.get_stock_basicinfo(Market.HK, SecurityType.STOCK)
    
    if ret != RET_OK or data.empty:
        return pd.DataFrame()
    
    print(f"✅ 获取到 {len(data)} 只港股")
    return data


def get_snapshot(quote_ctx: OpenQuoteContext, codes: List[str]) -> pd.DataFrame:
    """获取市场快照"""
    print(f"正在获取 {len(codes)} 只股票的实时数据...")
    
    batch_size = 400
    all_data = []
    
    for i in range(0, len(codes), batch_size):
        batch = codes[i:i+batch_size]
        ret, data = quote_ctx.get_market_snapshot(batch)
        
        if ret == RET_OK:
            all_data.append(data)
            if (i//batch_size + 1) % 5 == 0:
                print(f"  进度：{min(i+batch_size, len(codes))}/{len(codes)}")
    
    if not all_data:
        return pd.DataFrame()
    
    result = pd.concat(all_data, ignore_index=True)
    print(f"✅ 成功获取 {len(result)} 只股票数据")
    return result


def calculate_kline_indicators(quote_ctx: OpenQuoteContext, code: str) -> Dict:
    """计算 K 线指标（20 日涨幅、RSI 等）"""
    try:
        ret, data = quote_ctx.get_cur_kline(code, num=30, ktype=KLType.K_DAY, autype=AuType.QFQ)
        
        if ret != RET_OK or len(data) < 20:
            return {}
        
        # 20 日涨幅
        close_20d_ago = data['close'].iloc[-20] if len(data) >= 20 else data['close'].iloc[0]
        current_close = data['close'].iloc[-1]
        change_20d = ((current_close - close_20d_ago) / close_20d_ago) * 100
        
        # 5 日涨幅
        close_5d_ago = data['close'].iloc[-5] if len(data) >= 5 else data['close'].iloc[0]
        change_5d = ((current_close - close_5d_ago) / close_5d_ago) * 100
        
        # RSI (14 日)
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_14 = rsi.iloc[-1] if not rsi.empty else 50
        
        # 成交量比率（今日/5 日均量）
        avg_volume_5d = data['volume'].iloc[-5:].mean()
        today_volume = data['volume'].iloc[-1]
        volume_ratio = today_volume / avg_volume_5d if avg_volume_5d > 0 else 1
        
        return {
            'change_20d': change_20d,
            'change_5d': change_5d,
            'rsi_14': rsi_14,
            'volume_ratio': volume_ratio
        }
    
    except Exception as e:
        return {}


def calculate_score(row: pd.Series) -> float:
    """计算综合评分"""
    score = 0.0
    
    # 价值因子 (40%)
    value_score = 0.0
    if row.get('pe_ratio', None) and row['pe_ratio'] > 0:
        # PE 越低越好，PE<5 得满分，PE>30 得 0 分
        pe_score = max(0, min(100, (30 - row['pe_ratio']) / 25 * 100))
        value_score += pe_score * 0.5
    
    if row.get('pb_ratio', None) and row['pb_ratio'] > 0:
        # PB 越低越好
        pb_score = max(0, min(100, (5 - row['pb_ratio']) / 5 * 100))
        value_score += pb_score * 0.3
    
    if row.get('dividend_ratio', None) and row['dividend_ratio'] > 0:
        # 股息率越高越好
        div_score = min(100, row['dividend_ratio'] * 20)
        value_score += div_score * 0.2
    
    score += value_score * 0.4
    
    # 量价因子 (60%) - 提高权重
    momentum_score = 0.0
    if 'change_20d' in row and row['change_20d']:
        # 20 日涨幅 10-50% 得高分
        if 10 <= row['change_20d'] <= 50:
            momentum_score += 100 * 0.5
        elif row['change_20d'] > 0:
            momentum_score += max(0, 100 - abs(row['change_20d'] - 30)) * 0.5
    
    if 'rsi_14' in row and row['rsi_14']:
        # RSI 50-70 最佳
        rsi = row['rsi_14']
        if 50 <= rsi <= 70:
            momentum_score += 100 * 0.3
        elif 30 <= rsi < 50 or 70 < rsi <= 80:
            momentum_score += 50 * 0.3
    
    if 'volume_ratio' in row and row['volume_ratio']:
        # 成交量放大 1.5-3 倍最佳
        vol = row['volume_ratio']
        if 1.5 <= vol <= 3:
            momentum_score += 100 * 0.2
        elif vol > 1:
            momentum_score += 50 * 0.2
    
    score += momentum_score * 0.4
    
    # 质量因子 (20%) - 简化版用市值和流动性代表
    quality_score = 0.0
    if row.get('market_val', 0) > 500e8:  # 市值>500 亿
        quality_score += 100 * 0.5
    elif row.get('market_val', 0) > 100e8:
        quality_score += 70 * 0.5
    elif row.get('market_val', 0) > 50e8:
        quality_score += 50 * 0.5
    
    if row.get('volume', 0) > 10000000:  # 成交量>1000 万
        quality_score += 100 * 0.5
    elif row.get('volume', 0) > 1000000:
        quality_score += 70 * 0.5
    
    score += quality_score * 0.2
    
    return score


def select_stocks(snapshot_data: pd.DataFrame, quote_ctx: OpenQuoteContext, 
                  top_n: int = 20, show_progress: bool = True) -> pd.DataFrame:
    """选股主流程"""
    
    # 初步筛选
    filtered = snapshot_data.copy()
    
    # 市值筛选
    if 'market_val' in filtered.columns:
        filtered = filtered[filtered['market_val'] >= FILTERS['min_market_cap'] * 1e8]
    
    # 成交量筛选
    if 'volume' in filtered.columns:
        filtered = filtered[filtered['volume'] >= FILTERS['min_volume']]
    
    # PE 筛选
    if 'pe_ratio' in filtered.columns:
        filtered = filtered[(filtered['pe_ratio'] > 0) & (filtered['pe_ratio'] <= FILTERS['max_pe'])]
    
    # 价格筛选
    if 'last_price' in filtered.columns:
        filtered = filtered[
            (filtered['last_price'] >= FILTERS['min_price']) & 
            (filtered['last_price'] <= FILTERS['max_price'])
        ]
    
    print(f"✅ 初步筛选后剩余 {len(filtered)} 只股票")
    
    # 计算 K 线指标（只计算前 100 只，节省时间）
    print("\n正在计算 K 线指标（前 100 只）...")
    kline_codes = filtered['code'].tolist()[:100]
    
    for i, code in enumerate(kline_codes, 1):
        indicators = calculate_kline_indicators(quote_ctx, code)
        if indicators:
            filtered.loc[filtered['code'] == code, 'change_20d'] = indicators['change_20d']
            filtered.loc[filtered['code'] == code, 'change_5d'] = indicators['change_5d']
            filtered.loc[filtered['code'] == code, 'rsi_14'] = indicators['rsi_14']
            filtered.loc[filtered['code'] == code, 'volume_ratio'] = indicators['volume_ratio']
        
        if show_progress and i % 20 == 0:
            print(f"  进度：{i}/{len(kline_codes)}")
    
    # 计算综合评分
    print("\n正在计算综合评分...")
    filtered['total_score'] = filtered.apply(calculate_score, axis=1)
    
    # 排序
    filtered = filtered.sort_values('total_score', ascending=False)
    
    return filtered


def display_results(stock_data: pd.DataFrame, top_n: int = 20):
    """显示结果"""
    
    if stock_data.empty:
        print("❌ 没有数据")
        return
    
    print("\n" + "="*100)
    print(f"🏆 选股结果 Top {top_n}")
    print("="*100)
    
    for i, (_, row) in enumerate(stock_data.head(top_n).iterrows(), 1):
        print(f"\n{i:2d}. {row.get('code', 'N/A')} | {row.get('name', 'N/A')}")
        print(f"    价格：${row.get('last_price', 0):.2f} ({row.get('change_percent', 0):+.2f}%)")
        print(f"    PE: {row.get('pe_ratio', 'N/A'):.2f}  |  PB: {row.get('pb_ratio', 'N/A'):.2f}  |  "
              f"股息率：{row.get('dividend_ratio', 0):.1f}%")
        print(f"    市值：{row.get('market_val', 0)/1e8:.1f}亿港元")
        print(f"    20 日涨幅：{row.get('change_20d', 0):+.1f}%  |  RSI: {row.get('rsi_14', 0):.1f}  |  "
              f"成交量比：{row.get('volume_ratio', 1):.2f}")
        print(f"    📊 综合评分：{row.get('total_score', 0):.2f}")


def save_results(stock_data: pd.DataFrame, output_file: str = None):
    """保存结果"""
    
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/stock_selection_{timestamp}.csv'
    
    # 选择重要列
    cols_to_save = ['code', 'name', 'last_price', 'change_percent', 'pe_ratio', 'pb_ratio',
                    'dividend_ratio', 'market_val', 'volume', 'change_20d', 'rsi_14', 
                    'volume_ratio', 'total_score']
    
    available_cols = [col for col in cols_to_save if col in stock_data.columns]
    stock_data[available_cols].to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ 结果已保存到：{output_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='量化选股策略 - 增强版')
    parser.add_argument('--market', type=str, default='HK', choices=['HK', 'US'],
                        help='市场 (HK/US)')
    parser.add_argument('--top', type=int, default=20, help='显示前 N 只股票')
    parser.add_argument('--output', type=str, default=None, help='输出文件路径')
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"📊 量化选股系统 - 增强版")
    print(f"{'='*60}")
    print(f"市场：{args.market} | 时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # 连接 OpenD
    quote_ctx = connect_opend()
    
    try:
        # 获取股票列表
        stock_list = get_hk_stocks(quote_ctx)
        
        if stock_list.empty:
            print("❌ 未获取到股票列表")
            return
        
        codes = stock_list['code'].tolist()
        
        # 获取市场快照
        snapshot_data = get_snapshot(quote_ctx, codes)
        
        if snapshot_data.empty:
            print("❌ 未获取到市场数据")
            return
        
        # 选股
        selected_stocks = select_stocks(snapshot_data, quote_ctx, top_n=args.top)
        
        # 显示结果
        display_results(selected_stocks, args.top)
        
        # 保存结果
        save_results(selected_stocks, args.output)
        
        # JSON 输出
        if args.json:
            result = {
                'timestamp': datetime.now().isoformat(),
                'market': args.market,
                'total_stocks': len(selected_stocks),
                'top_stocks': selected_stocks.head(args.top).to_dict('records')
            }
            print("\n" + json.dumps(result, ensure_ascii=False, indent=2))
    
    finally:
        quote_ctx.close()
        print("\n✅ 选股完成")


if __name__ == "__main__":
    main()
