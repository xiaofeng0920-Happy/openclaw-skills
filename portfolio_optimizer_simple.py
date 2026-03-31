#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版组合优化 - 基于选股结果直接推荐

作者：小巴
日期：2026-03-26
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import argparse

def load_stock_selection(input_file: str, top_n: int = 10) -> pd.DataFrame:
    """加载选股结果"""
    df = pd.read_csv(input_file)
    
    if 'total_score' not in df.columns:
        print("❌ CSV 文件中未找到 total_score 列")
        return pd.DataFrame()
    
    # 按评分排序，取前 N 只
    df = df.sort_values('total_score', ascending=False).head(top_n)
    
    print(f"✅ 加载 {len(df)} 只股票")
    return df


def optimize_simple(df: pd.DataFrame) -> pd.DataFrame:
    """
    简化版组合优化
    基于评分和估值综合分配权重
    """
    
    if df.empty:
        return df
    
    # 归一化评分
    score_min = df['total_score'].min()
    score_max = df['total_score'].max()
    
    if score_max > score_min:
        df['normalized_score'] = (df['total_score'] - score_min) / (score_max - score_min)
    else:
        df['normalized_score'] = 1.0 / len(df)
    
    # 估值调整（PE 越低权重越高）
    if 'pe_ratio' in df.columns:
        df['pe_score'] = 1.0 / df['pe_ratio'].replace(0, np.nan).fillna(df['pe_ratio'].median())
        df['pe_score'] = df['pe_score'] / df['pe_score'].max()
    else:
        df['pe_score'] = 1.0
    
    # 综合权重 = 评分 70% + 估值 30%
    df['final_score'] = df['normalized_score'] * 0.7 + df['pe_score'] * 0.3
    
    # 归一化为权重
    df['weight'] = df['final_score'] / df['final_score'].sum()
    
    # 限制单股权重不超过 20%
    df['weight'] = df['weight'].clip(upper=0.20)
    
    # 重新归一化
    df['weight'] = df['weight'] / df['weight'].sum()
    
    return df


def display_portfolio(df: pd.DataFrame):
    """显示组合"""
    
    if df.empty:
        print("❌ 没有数据")
        return
    
    print("\n" + "="*80)
    print("💼 推荐投资组合")
    print("="*80)
    
    total_weight = 0
    for i, (_, row) in enumerate(df.iterrows(), 1):
        code = row.get('code', 'N/A')
        name = row.get('name', 'N/A')
        weight = row.get('weight', 0) * 100
        score = row.get('total_score', 0)
        pe = row.get('pe_ratio', 'N/A')
        price = row.get('last_price', 0)
        
        print(f"{i:2d}. {code:12} | {name:20} | 权重：{weight:5.1f}% | 评分：{score:5.2f} | PE: {pe:>6} | 价格：${price:.2f}")
        total_weight += weight
    
    print("="*80)
    print(f"总计：{total_weight:.1f}%")
    print("="*80)
    
    # 组合统计
    print("\n📊 组合统计")
    print("-"*60)
    print(f"股票数量：{len(df)}")
    print(f"平均 PE: {df['pe_ratio'].mean():.2f}")
    print(f"平均 PB: {df['pb_ratio'].mean():.2f}")
    print(f"最高权重：{df['weight'].max()*100:.1f}%")
    print(f"最低权重：{df['weight'].min()*100:.1f}%")


def save_portfolio(df: pd.DataFrame, output_file: str = None):
    """保存组合结果"""
    
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/portfolio_{timestamp}.csv'
    
    cols_to_save = ['code', 'name', 'last_price', 'pe_ratio', 'pb_ratio', 
                    'total_score', 'weight']
    available_cols = [col for col in cols_to_save if col in df.columns]
    
    df[available_cols].to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n✅ 结果已保存到：{output_file}")
    
    # 同时保存 JSON
    json_file = output_file.replace('.csv', '.json')
    result = {
        'timestamp': datetime.now().isoformat(),
        'total_stocks': len(df),
        'portfolio': df[available_cols].to_dict('records')
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON 已保存到：{json_file}")


def main():
    parser = argparse.ArgumentParser(description='简化版组合优化')
    parser.add_argument('--input', type=str, required=True, help='选股结果 CSV 文件')
    parser.add_argument('--top', type=int, default=10, help='优化前 N 只股票')
    parser.add_argument('--output', type=str, default=None, help='输出文件路径')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"💼 简化版组合优化")
    print(f"{'='*60}")
    print(f"输入文件：{args.input}")
    print(f"优化标的：Top {args.top}")
    print(f"{'='*60}\n")
    
    # 加载选股结果
    df = load_stock_selection(args.input, args.top)
    
    if df.empty:
        return
    
    # 组合优化
    print("正在进行组合优化...")
    df = optimize_simple(df)
    
    # 显示结果
    display_portfolio(df)
    
    # 保存结果
    save_portfolio(df, args.output)
    
    print("\n✅ 组合优化完成")


if __name__ == "__main__":
    main()
