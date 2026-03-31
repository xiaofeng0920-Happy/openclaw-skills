#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股批量分析脚本 - 分析锋哥关注的港股
"""

import json
import sys
from datetime import datetime

# 富途 OpenD SDK
from futu import *

# 要分析的港股列表
HK_STOCKS = [
    "HK.00144",  # 招商局港口
    "HK.00151",  # 中国旺旺
    "HK.00322",  # 康师傅控股
    "HK.00390",  # 中国中铁
    "HK.00392",  # 北京控股
    "HK.00489",  # 东风集团股份
    "HK.00551",  # 裕元集团
    "HK.00586",  # 海螺创业
    "HK.00669",  # 创科实业
    "HK.00753",  # 中国国航
    "HK.00762",  # 中国联通
    "HK.00823",  # 领展房产基金
]

def get_stock_data(stock_code):
    """获取股票实时行情"""
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    try:
        # 获取实时行情 - 修复返回值数量
        ret, data = quote_ctx.get_market_snapshot([stock_code])
        
        if ret != RET_OK:
            print(f"  API 返回错误：{ret}")
            return None
        
        if data is None or (hasattr(data, 'empty') and data.empty):
            return None
        
        row = data.iloc[0] if hasattr(data, 'iloc') else data[0] if isinstance(data, list) else None
        
        if row is None:
            return None
        
        # 兼容 Series 和 dict
        def get_val(key, default=0):
            if hasattr(row, 'get'):
                return row.get(key, default)
            elif isinstance(row, dict):
                return row.get(key, default)
            else:
                return getattr(row, key, default)
        
        return {
            'code': stock_code,
            'name': get_val('name', ''),
            'price': get_val('last_price', 0),
            'change': get_val('change', 0),
            'change_percent': get_val('change_percent', 0),
            'open': get_val('open_price', 0),
            'high': get_val('high_price', 0),
            'low': get_val('low_price', 0),
            'volume': get_val('volume', 0),
            'turnover': get_val('turnover', 0),
            'pe': get_val('pe_ratio', 0),
            'pb': get_val('pb_ratio', 0),
            'dividend_yield': get_val('dividend_yield', 0),
            'market_cap': get_val('market_cap', 0),
            '52w_high': get_val('high_52w', 0),
            '52w_low': get_val('low_52w', 0),
        }
    except Exception as e:
        print(f"获取 {stock_code} 数据失败：{e}")
        return None
    finally:
        quote_ctx.close()

def analyze_stock(data):
    """分析股票并给出评级"""
    if not data:
        return None
    
    score = 50  # 基础分
    signals = []
    
    # 涨跌幅评分
    change_pct = data['change_percent']
    if change_pct > 5:
        score += 15
        signals.append("🔥 大涨>5%")
    elif change_pct > 2:
        score += 8
        signals.append("📈 上涨>2%")
    elif change_pct < -5:
        score -= 15
        signals.append("📉 大跌>5%")
    elif change_pct < -2:
        score -= 8
        signals.append("📉 下跌>2%")
    
    # 市盈率评分 (越低越好，但负值不好)
    pe = data['pe']
    if 0 < pe < 10:
        score += 10
        signals.append(f"💰 低 PE ({pe:.1f})")
    elif 10 <= pe < 20:
        score += 5
        signals.append(f"✅ 合理 PE ({pe:.1f})")
    elif pe < 0:
        score -= 10
        signals.append(f"⚠️ 亏损 (PE {pe:.1f})")
    elif pe > 30:
        score -= 5
        signals.append(f"⚠️ 高 PE ({pe:.1f})")
    
    # 市净率评分
    pb = data['pb']
    if 0 < pb < 1:
        score += 8
        signals.append(f"💎 低 PB ({pb:.2f})")
    elif pb > 3:
        score -= 5
        signals.append(f"⚠️ 高 PB ({pb:.2f})")
    
    # 股息率评分
    dividend = data['dividend_yield']
    if dividend > 5:
        score += 10
        signals.append(f"💵 高股息 ({dividend:.1f}%)")
    elif dividend > 3:
        score += 5
        signals.append(f"✅ 不错股息 ({dividend:.1f}%)")
    
    # 52 周位置
    price = data['price']
    high_52w = data['52w_high']
    low_52w = data['52w_low']
    
    if high_52w > 0 and low_52w > 0:
        position = (price - low_52w) / (high_52w - low_52w) * 100
        if position < 20:
            score += 8
            signals.append(f"📍 近 52 周低位")
        elif position > 80:
            score -= 5
            signals.append(f"⚠️ 近 52 周高位")
    
    # 评级
    if score >= 75:
        rating = "强烈推荐"
        emoji = "🔥"
    elif score >= 60:
        rating = "推荐"
        emoji = "👍"
    elif score >= 45:
        rating = "中性"
        emoji = "➖"
    elif score >= 30:
        rating = "谨慎"
        emoji = "⚠️"
    else:
        rating = "回避"
        emoji = "❌"
    
    return {
        **data,
        'score': score,
        'rating': rating,
        'emoji': emoji,
        'signals': signals
    }

def main():
    print("=" * 60)
    print("📊 锋哥港股批量分析报告")
    print(f"🕐 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    results = []
    
    for i, stock_code in enumerate(HK_STOCKS, 1):
        print(f"[{i}/{len(HK_STOCKS)}] 分析 {stock_code}...")
        
        data = get_stock_data(stock_code)
        if data:
            analysis = analyze_stock(data)
            results.append(analysis)
            
            # 打印简要信息
            print(f"  {analysis['emoji']} {analysis['name']} ({analysis['code']})")
            print(f"     价格：HK$ {analysis['price']:.2f} ({analysis['change_percent']:+.2f}%)")
            print(f"     评分：{analysis['score']} - {analysis['rating']}")
            if analysis['signals']:
                print(f"     信号：{', '.join(analysis['signals'])}")
            print()
        else:
            print(f"  ❌ 获取 {stock_code} 数据失败")
            print()
    
    # 汇总
    print("=" * 60)
    print("📋 汇总")
    print("=" * 60)
    
    if results:
        # 按评分排序
        sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)
        
        print("\n🔥 推荐买入 (评分≥60):")
        for r in [x for x in sorted_results if x['score'] >= 60]:
            print(f"  {r['emoji']} {r['name']} ({r['code']}): HK$ {r['price']:.2f}, 评分{r['score']}")
        
        print("\n➖ 中性观望 (45≤评分<60):")
        for r in [x for x in sorted_results if 45 <= x['score'] < 60]:
            print(f"  {r['emoji']} {r['name']} ({r['code']}): HK$ {r['price']:.2f}, 评分{r['score']}")
        
        print("\n⚠️ 谨慎/回避 (评分<45):")
        for r in [x for x in sorted_results if x['score'] < 45]:
            print(f"  {r['emoji']} {r['name']} ({r['code']}): HK$ {r['price']:.2f}, 评分{r['score']}")
    
    # 保存结果 - 修复 numpy 类型序列化
    output_file = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/reports/hk_stocks_analysis.json"
    
    def convert_to_serializable(obj):
        """转换 numpy 类型为 Python 原生类型"""
        import numpy as np
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(i) for i in obj]
        return obj
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': convert_to_serializable(results)
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 详细报告已保存：{output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
