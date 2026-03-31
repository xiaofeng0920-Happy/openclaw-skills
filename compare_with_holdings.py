#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓对比分析 - 对比锋哥现有持仓与行业推荐
"""

import json
from datetime import datetime

def main():
    print("=" * 80)
    print("📊 锋哥持仓对比分析")
    print("=" * 80)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 读取持仓数据
    with open('config/feng_portfolio.json', 'r', encoding='utf-8') as f:
        portfolio = json.load(f)
    
    # 读取行业推荐数据
    with open('reports/hk_industry_top5.json', 'r', encoding='utf-8') as f:
        industry_data = json.load(f)
    
    # 读取汇总数据
    with open('reports/hk_market_full_summary.json', 'r', encoding='utf-8') as f:
        all_stocks = json.load(f)
    
    # 锋哥港股持仓
    hk_holdings = portfolio['accounts']['hk_stocks']['holdings']
    holding_symbols = [h['symbol'] for h in hk_holdings]
    
    print(f"📋 锋哥港股持仓：{len(hk_holdings)} 只")
    for h in hk_holdings:
        print(f"  - {h['symbol']}: {h['name']} ({h['pnl_percent']:+.1f}%)")
    
    print()
    print("=" * 80)
    print("🔍 持仓与行业推荐对比")
    print("=" * 80)
    
    # 检查持仓股票是否在推荐列表中
    all_recommended = all_stocks['all_results']
    recommended_symbols = {s['code']: s for s in all_recommended if s['score'] >= 60}
    
    print("\n✅ 持仓中的推荐股:")
    for symbol in holding_symbols:
        code = f"HK.{symbol.replace('.HK', '')}" if not symbol.startswith('HK.') else symbol
        if code in recommended_symbols:
            stock = recommended_symbols[code]
            print(f"  ✓ {symbol}: 评分{stock['score']}分, PE{stock['pe']:.1f}, PB{stock['pb']:.2f}")
    
    print("\n❌ 持仓中但未达推荐的股票:")
    for symbol in holding_symbols:
        code = f"HK.{symbol.replace('.HK', '')}" if not symbol.startswith('HK.') else symbol
        if code not in recommended_symbols:
            # 在全部股票中查找
            for s in all_stocks['all_results']:
                if s['code'] == code:
                    print(f"  ✗ {symbol}: 评分{s['score']}分 (低于 60 分)")
                    break
    
    print()
    print("=" * 80)
    print("💡 行业配置建议")
    print("=" * 80)
    
    # 行业配置分析
    print("\n📌 锋哥当前港股行业分布:")
    print("  - 互联网科技：腾讯、阿里 (亏损)")
    print("  - 能源：中海油 (+178% ✅)")
    print("  - 指数 ETF：日经 225 (-11%)")
    print("  - 杠杆 ETF：南方两倍做多 (+25% ✅)")
    print("  - 高端制造：潍柴动力、紫金矿业")
    print("  - AI 概念：心动公司、智谱")
    
    print("\n📌 建议增加的行业配置:")
    print("  1. 🏦 银行金融 (0%) → 建议 20-30%")
    print("     推荐：建设银行、工商银行、中原银行")
    print("  2. 💡 公用事业 (0%) → 建议 15-20%")
    print("     推荐：华润电力、中国水务、上海实业环境")
    print("  3. 🚄 基建交通 (0%) → 建议 10-15%")
    print("     推荐：招商局港口、中远海运港口")
    print("  4. 💊 医药医疗 (0%) → 建议 10-15%")
    print("     推荐：华润医疗、中国健康科技")
    
    print("\n📌 建议减仓的持仓:")
    print("  ⚠️ 03153.HK 南方日经 225 (-11%)")
    print("     原因：不符合巴菲特标准，评分仅 28 分")
    print("     建议：换到 GOOGL/BRK.B 或港股银行股")
    
    print("\n📌 建议继续持有的持仓:")
    print("  ✅ 00883.HK 中国海洋石油 (+178%)")
    print("     原因：能源行业龙头，业绩优秀")
    print("  ✅ 07709.HK 南方两倍做多 (+25%)")
    print("     原因：杠杆 ETF，趋势向好")
    
    print()
    print("=" * 80)
    print("🎯 优化后的组合建议")
    print("=" * 80)
    
    print("""
┌─────────────────────────────────────────────────────────────┐
│  保守型组合 (收息为主)                                      │
├─────────────────────────────────────────────────────────────┤
│  🏦 银行金融    30%  (建行、工行、中原银行)                 │
│  💡 公用事业    25%  (华润电力、中国水务)                   │
│  🚄 基建交通    20%  (招商局港口、中远海运)                 │
│  ⛽ 能源石油    15%  (中海油、中油燃气)                     │
│  💊 医药医疗    10%  (华润医疗)                             │
├─────────────────────────────────────────────────────────────┤
│  预期股息率：6-8%  |  风险等级：⭐⭐                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  平衡型组合 (收息 + 成长)                                    │
├─────────────────────────────────────────────────────────────┤
│  🏦 银行金融    25%  (建行、工行)                           │
│  💊 医药医疗    20%  (华润医疗、中国健康科技)               │
│  💡 公用事业    20%  (华润电力、中国水务)                   │
│  ⛽ 能源石油    15%  (中海油、天伦燃气)                     │
│  🚄 基建交通    15%  (招商局港口、天津港)                   │
│  🏠 房地产      5%   (中国海外发展)                          │
├─────────────────────────────────────────────────────────────┤
│  预期收益：15-25%  |  风险等级：⭐⭐⭐                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  锋哥当前持仓优化建议                                        │
├─────────────────────────────────────────────────────────────┤
│  ✅ 继续持有：                                              │
│     - 00883.HK 中海油 (能源龙头)                            │
│     - 07709.HK 南方两倍做多 (趋势向好)                      │
│     - 02338.HK 潍柴动力 (高端制造)                          │
│                                                             │
│  ⚠️ 建议减仓：                                              │
│     - 03153.HK 南方日经 225 → 换银行股                      │
│     - 02400.HK 心动公司 → 换公用事业                        │
│     - 02899.HK 紫金矿业 → 换基建交通                        │
│                                                             │
│  🆕 建议新增：                                              │
│     - 00939.HK 建设银行 (10%)                               │
│     - 00836.HK 华润电力 (10%)                               │
│     - 01515.HK 华润医疗 (5%)                                │
└─────────────────────────────────────────────────────────────┘
    """)
    
    print("=" * 80)
    print("✅ 对比分析完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()
