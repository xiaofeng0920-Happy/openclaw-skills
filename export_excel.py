#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出港股分析 Excel 表格
"""

import json
from datetime import datetime
from collections import defaultdict

def escape_excel(text):
    """转义 Excel 特殊字符"""
    if isinstance(text, str):
        return text.replace('"', '""')
    return text

def main():
    print("=" * 70)
    print("📊 导出港股分析 Excel 表格")
    print("=" * 70)
    
    # 读取数据
    with open('reports/hk_market_full_summary.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    with open('reports/hk_industry_top5.json', 'r', encoding='utf-8') as f:
        industry_data = json.load(f)
    
    all_stocks = data['all_results']
    
    # 1. 导出全部推荐股票 (CSV 格式，Excel 可打开)
    print("\n📁 生成文件 1: hk_recommended_stocks.csv (全部推荐股)")
    
    recommended = [s for s in all_stocks if s['score'] >= 60]
    recommended.sort(key=lambda x: x['score'], reverse=True)
    
    with open('reports/hk_recommended_stocks.csv', 'w', encoding='utf-8-sig') as f:
        # 表头
        f.write("排名，代码，名称，价格 (HK$),评分，PE,PB，股息率 (%)，行业，信号\n")
        
        for i, stock in enumerate(recommended, 1):
            signals = '; '.join(stock.get('signals', []))
            f.write(f"{i},{stock['code']},{escape_excel(stock['name'])},{stock['price']:.2f},"
                   f"{stock['score']},{stock['pe']:.1f},{stock['pb']:.2f},"
                   f"{stock['dividend_yield']:.1f},,{signals}\n")
    
    print(f"  ✓ 已导出 {len(recommended)} 只推荐股票")
    
    # 2. 导出行业 Top 5
    print("\n📁 生成文件 2: hk_industry_top5.csv (各行业 Top 5)")
    
    with open('reports/hk_industry_top5.csv', 'w', encoding='utf-8-sig') as f:
        f.write("行业，排名，代码，名称，价格 (HK$),评分，PE,PB，信号\n")
        
        for ind in industry_data['industries']:
            industry = ind['industry']
            for i, stock in enumerate(ind['stocks'][:5], 1):
                signals = '; '.join(stock.get('signals', []))
                f.write(f"{industry},{i},{stock['code']},{escape_excel(stock['name'])},"
                       f"{stock['price']:.2f},{stock['score']},{stock['pe']:.1f},"
                       f"{stock['pb']:.2f},{signals}\n")
    
    print(f"  ✓ 已导出 {len(industry_data['industries'])} 个行业的 Top 5")
    
    # 3. 导出重点推荐 (评分 68 分)
    print("\n📁 生成文件 3: hk_top_picks.csv (重点推荐 68 分)")
    
    top_picks = [s for s in all_stocks if s['score'] == 68]
    top_picks.sort(key=lambda x: (x['pe'] if x['pe'] > 0 else 999, x['pb'] if x['pb'] > 0 else 999))
    
    with open('reports/hk_top_picks.csv', 'w', encoding='utf-8-sig') as f:
        f.write("排名，代码，名称，价格 (HK$),PE,PB，市值，信号\n")
        
        for i, stock in enumerate(top_picks[:100], 1):  # 前 100 只
            signals = '; '.join(stock.get('signals', []))
            f.write(f"{i},{stock['code']},{escape_excel(stock['name'])},{stock['price']:.2f},"
                   f"{stock['pe']:.1f},{stock['pb']:.2f},{stock['market_cap']},{signals}\n")
    
    print(f"  ✓ 已导出 {min(len(top_picks), 100)} 只重点推荐股票")
    
    # 4. 导出锋哥持仓对比
    print("\n📁 生成文件 4: holdings_comparison.csv (持仓对比)")
    
    with open('config/feng_portfolio.json', 'r', encoding='utf-8') as f:
        portfolio = json.load(f)
    
    hk_holdings = portfolio['accounts']['hk_stocks']['holdings']
    
    # 构建推荐股票字典
    rec_dict = {s['code']: s for s in all_stocks}
    
    with open('reports/holdings_comparison.csv', 'w', encoding='utf-8-sig') as f:
        f.write("代码，名称，持仓盈亏 (%),评分，PE,PB，建议\n")
        
        for h in hk_holdings:
            symbol = h['symbol']
            code = f"HK.{symbol.replace('.HK', '')}" if not symbol.startswith('HK.') else symbol
            
            stock = rec_dict.get(code, {})
            score = stock.get('score', 0)
            pe = stock.get('pe', 0)
            pb = stock.get('pb', 0)
            
            if score >= 60:
                suggestion = "继续持有"
            elif score >= 45:
                suggestion = "观望"
            else:
                suggestion = "考虑减仓"
            
            f.write(f"{symbol},{escape_excel(h['name'])},{h['pnl_percent']:+.1f},"
                   f"{score},{pe:.1f},{pb:.2f},{suggestion}\n")
    
    print(f"  ✓ 已导出 {len(hk_holdings)} 只持仓股票对比")
    
    # 5. 生成汇总统计
    print("\n📁 生成文件 5: hk_summary_stats.txt (汇总统计)")
    
    with open('reports/hk_summary_stats.txt', 'w', encoding='utf-8') as f:
        f.write("港股全市场分析 - 汇总统计\n")
        f.write(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"总股票数：{data['total_stocks']}\n")
        f.write(f"推荐股票：{data['recommend_count']} ({data['recommend_count']/data['total_stocks']*100:.1f}%)\n")
        f.write(f"中性股票：{data['neutral_count']} ({data['neutral_count']/data['total_stocks']*100:.1f}%)\n")
        f.write(f"谨慎/回避：{data['caution_count']} ({data['caution_count']/data['total_stocks']*100:.1f}%)\n\n")
        
        f.write("行业分布:\n")
        for ind in industry_data['industries'][:10]:
            f.write(f"  {ind['industry']}: {ind['count']}只\n")
    
    print("  ✓ 已生成汇总统计")
    
    print("\n" + "=" * 70)
    print("✅ Excel 导出完成！")
    print("=" * 70)
    print("\n📁 文件位置:")
    print("  1. reports/hk_recommended_stocks.csv - 全部 620 只推荐股")
    print("  2. reports/hk_industry_top5.csv - 各行业 Top 5")
    print("  3. reports/hk_top_picks.csv - 重点推荐 (68 分)")
    print("  4. reports/holdings_comparison.csv - 持仓对比")
    print("  5. reports/hk_summary_stats.txt - 汇总统计")
    print("\n💡 提示：CSV 文件可用 Excel 直接打开")
    print("=" * 70)

if __name__ == "__main__":
    main()
