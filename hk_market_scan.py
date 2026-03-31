#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股全市场分析 - 687 只股票批量分析
支持多 agent 并行处理
"""

import json
import sys
from datetime import datetime
from futu import *

def get_all_hk_stocks():
    """获取所有港股列表"""
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    try:
        ret, data = quote_ctx.get_stock_basicinfo(market=TrdMarket.HK)
        
        if ret == RET_OK and data is not None and not data.empty:
            stocks = []
            for _, row in data.iterrows():
                code = row.get('code', '')
                name = row.get('name', '')
                stock_type = row.get('stock_type', '')
                if code and name and stock_type in ['主板', '创业板', '主板 (香港)', '创业板 (香港)']:
                    stocks.append({
                        'code': f'HK.{code}',
                        'name': name
                    })
            return stocks
        return []
    except Exception as e:
        print(f"获取港股列表失败：{e}")
        return []
    finally:
        quote_ctx.close()

def get_stock_snapshot(quote_ctx, stock_code):
    """获取股票快照数据"""
    try:
        ret, data = quote_ctx.get_market_snapshot([stock_code])
        
        if ret != RET_OK or data is None or (hasattr(data, 'empty') and data.empty):
            return None
        
        row = data.iloc[0] if hasattr(data, 'iloc') else data[0] if isinstance(data, list) else None
        if row is None:
            return None
        
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
            'change_percent': get_val('change_percent', 0),
            'pe': get_val('pe_ratio', 0),
            'pb': get_val('pb_ratio', 0),
            'dividend_yield': get_val('dividend_yield', 0),
            'volume': get_val('volume', 0),
            'turnover': get_val('turnover', 0),
            'market_cap': get_val('market_cap', 0),
        }
    except Exception as e:
        return None

def get_batch_snapshots(quote_ctx, stock_codes):
    """批量获取股票快照数据"""
    try:
        ret, data = quote_ctx.get_market_snapshot(stock_codes)
        
        if ret != RET_OK or data is None or (hasattr(data, 'empty') and data.empty):
            return {}
        
        results = {}
        for _, row in data.iterrows():
            code = row.get('code', '')
            if not code:
                continue
            
            def get_val(key, default=0):
                if hasattr(row, 'get'):
                    return row.get(key, default)
                elif isinstance(row, dict):
                    return row.get(key, default)
                else:
                    return getattr(row, key, default)
            
            results[code] = {
                'code': code,
                'name': get_val('name', ''),
                'price': get_val('last_price', 0),
                'change_percent': get_val('change_percent', 0),
                'pe': get_val('pe_ratio', 0),
                'pb': get_val('pb_ratio', 0),
                'dividend_yield': get_val('dividend_yield', 0),
                'volume': get_val('volume', 0),
                'turnover': get_val('turnover', 0),
                'market_cap': get_val('market_cap', 0),
            }
        return results
    except Exception as e:
        return {}

def analyze_stock(data):
    """分析股票并评分"""
    if not data:
        return None
    
    score = 50
    signals = []
    
    # 涨跌幅
    change_pct = data['change_percent']
    if change_pct > 5:
        score += 15
        signals.append("🔥大涨>5%")
    elif change_pct > 2:
        score += 8
        signals.append("📈上涨>2%")
    elif change_pct < -5:
        score -= 15
        signals.append("📉大跌>5%")
    elif change_pct < -2:
        score -= 8
        signals.append("📉下跌>2%")
    
    # PE 评分
    pe = data['pe']
    if 0 < pe < 10:
        score += 10
        signals.append(f"💰低 PE({pe:.1f})")
    elif 10 <= pe < 20:
        score += 5
        signals.append(f"✅合理 PE({pe:.1f})")
    elif pe < 0:
        score -= 10
        signals.append(f"⚠️亏损")
    elif pe > 30:
        score -= 5
        signals.append(f"⚠️高 PE({pe:.1f})")
    
    # PB 评分
    pb = data['pb']
    if 0 < pb < 1:
        score += 8
        signals.append(f"💎低 PB({pb:.2f})")
    elif pb > 3:
        score -= 5
        signals.append(f"⚠️高 PB({pb:.2f})")
    
    # 股息率
    dividend = data['dividend_yield']
    if dividend > 5:
        score += 10
        signals.append(f"💵高股息({dividend:.1f}%)")
    elif dividend > 3:
        score += 5
        signals.append(f"✅不错股息({dividend:.1f}%)")
    
    # 评级
    if score >= 75:
        rating, emoji = "强烈推荐", "🔥"
    elif score >= 60:
        rating, emoji = "推荐", "👍"
    elif score >= 45:
        rating, emoji = "中性", "➖"
    elif score >= 30:
        rating, emoji = "谨慎", "⚠️"
    else:
        rating, emoji = "回避", "❌"
    
    return {
        **data,
        'score': score,
        'rating': rating,
        'emoji': emoji,
        'signals': signals
    }

def main():
    if len(sys.argv) < 2:
        print("用法：python3 hk_market_scan.py <batch_file>")
        sys.exit(1)
    
    batch_file = sys.argv[1]
    with open(batch_file, 'r', encoding='utf-8') as f:
        batch = json.load(f)
    
    stock_list = batch.get('stocks', [])
    batch_id = batch.get('batch_id', 0)
    total_batches = batch.get('total_batches', 1)
    
    print(f"📊 港股全市场分析 - Batch {batch_id + 1}/{total_batches}")
    print(f"📋 本批股票数：{len(stock_list)}")
    print(f"🕐 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 创建单一连接，复用
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    results = []
    
    try:
        # 批量处理，每批 10 只股票
        batch_size = 10
        for batch_start in range(0, len(stock_list), batch_size):
            batch_stocks = stock_list[batch_start:batch_start + batch_size]
            batch_codes = []
            stock_map = {}  # code -> original stock info
            
            for stock in batch_stocks:
                code = stock['code']
                name = stock['name']
                # 修复代码格式：HK.HK.XXXXX -> HK.XXXXX
                if code.startswith('HK.HK.'):
                    code = 'HK.' + code[6:]
                batch_codes.append(code)
                stock_map[code] = {'original_code': stock['code'], 'name': name}
            
            # 批量获取快照
            snapshots = get_batch_snapshots(quote_ctx, batch_codes)
            
            # 处理结果
            for code in batch_codes:
                i = batch_start + batch_codes.index(code) + 1
                name = stock_map.get(code, {}).get('name', '')
                print(f"[{i}/{len(stock_list)}] 分析 {code} {name}...", end=" ")
                
                data = snapshots.get(code)
                if data:
                    analysis = analyze_stock(data)
                    results.append(analysis)
                    
                    if analysis['score'] >= 60:
                        print(f"{analysis['emoji']} {analysis['rating']} ({analysis['score']}分)")
                    else:
                        print("✓")
                else:
                    print("❌ 失败")
    finally:
        quote_ctx.close()
    
    # 保存结果
    output_file = f"/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/reports/hk_market_scan_batch_{batch_id + 1}.json"
    
    # 转换类型
    def convert(obj):
        import numpy as np
        if isinstance(obj, (np.integer, np.int64)): return int(obj)
        elif isinstance(obj, (np.floating, np.float64)): return float(obj)
        elif isinstance(obj, dict): return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list): return [convert(i) for i in obj]
        return obj
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'batch_id': batch_id + 1,
            'total_batches': total_batches,
            'timestamp': datetime.now().isoformat(),
            'stock_count': len(results),
            'results': convert(results)
        }, f, ensure_ascii=False, indent=2)
    
    # 统计
    top_stocks = [r for r in results if r['score'] >= 75]
    recommend_stocks = [r for r in results if 60 <= r['score'] < 75]
    
    print("\n" + "=" * 60)
    print(f"📋 Batch {batch_id + 1} 汇总:")
    print(f"  🔥 强烈推荐：{len(top_stocks)} 只")
    print(f"  👍 推荐：{len(recommend_stocks)} 只")
    print(f"  💾 报告：{output_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()
