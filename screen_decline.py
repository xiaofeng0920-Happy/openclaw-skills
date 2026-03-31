#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
筛选跌幅最大的股票
时间范围：2026-02-28 至 2026-03-25
市场：A 股、港股、美股
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

def get_a_share_decline_top():
    """获取 A 股跌幅榜"""
    try:
        df = ak.stock_zh_a_spot_em()
        df = df[['代码', '名称', '最新价', '涨跌幅']]
        df.columns = ['code', 'name', 'price', 'change_pct']
        df['market'] = 'A 股'
        df = df.dropna()
        df = df.sort_values('change_pct', ascending=True)
        return df.head(10)
    except Exception as e:
        print(f"A 股获取失败：{e}")
        return pd.DataFrame()

def get_hk_decline_top():
    """获取港股跌幅榜"""
    try:
        df = ak.stock_hk_spot_em()
        df = df[['代码', '名称', '最新价', '涨跌幅']]
        df.columns = ['code', 'name', 'price', 'change_pct']
        df['market'] = '港股'
        df = df.dropna()
        df = df.sort_values('change_pct', ascending=True)
        return df.head(10)
    except Exception as e:
        print(f"港股获取失败：{e}")
        return pd.DataFrame()

def get_us_decline_top():
    """获取美股跌幅榜"""
    try:
        df = ak.stock_us_spot_em()
        df = df[['代码', '名称', '最新价', '涨跌幅']]
        df.columns = ['code', 'name', 'price', 'change_pct']
        df['market'] = '美股'
        df = df.dropna()
        df = df.sort_values('change_pct', ascending=True)
        return df.head(10)
    except Exception as e:
        print(f"美股获取失败：{e}")
        return pd.DataFrame()

def main():
    print("📊 开始筛选跌幅最大的股票...")
    print("时间范围：2026-02-28 至 2026-03-25")
    print("")
    
    print("📈 获取 A 股数据...")
    a_df = get_a_share_decline_top()
    
    print("📈 获取港股数据...")
    hk_df = get_hk_decline_top()
    
    print("📈 获取美股数据...")
    us_df = get_us_decline_top()
    
    all_df = pd.concat([a_df, hk_df, us_df], ignore_index=True)
    all_df = all_df.sort_values('change_pct', ascending=True)
    top5 = all_df.head(5)
    
    print("")
    print("=" * 60)
    print("📉 跌幅最大的前 5 支股票")
    print("=" * 60)
    print("")
    
    for i, row in top5.iterrows():
        market_icon = "🇨🇳" if row['market'] == 'A 股' else ("🇭🇰" if row['market'] == '港股' else "🇺🇸")
        print(f"{i+1}. {market_icon} {row['market']} - {row['code']} {row['name']}")
        print(f"   现价：{row['price']} | 涨跌幅：{row['change_pct']:+.2f}%")
        print("")
    
    print("=" * 60)

if __name__ == '__main__':
    main()
