#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股重点行业深度分析
"""

import json
from datetime import datetime

def main():
    # 读取行业报告
    with open('reports/hk_industry_top5.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 80)
    print("🔍 港股重点行业深度分析")
    print("=" * 80)
    print(f"分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 选择重点行业深入分析
    key_industries = ['🏦 银行金融', '💊 医药医疗', '💡 公用事业', '⛽ 能源石油', '🚄 基建交通']
    
    for industry_data in data['industries']:
        industry = industry_data['industry']
        
        if industry not in key_industries:
            continue
        
        stocks = industry_data['stocks']
        count = industry_data['count']
        
        print("\n" + "=" * 80)
        print(f"📌 {industry} - 深度分析 ({count}只推荐股)")
        print("=" * 80)
        
        # 行业汇总
        avg_pe = sum(s['pe'] for s in stocks if s['pe'] > 0) / len([s for s in stocks if s['pe'] > 0])
        avg_pb = sum(s['pb'] for s in stocks if s['pb'] > 0) / len([s for s in stocks if s['pb'] > 0])
        
        print(f"\n📊 行业估值:")
        print(f"  平均 PE: {avg_pe:.1f}x")
        print(f"  平均 PB: {avg_pb:.2f}x")
        print(f"  推荐数量：{count}只")
        
        print(f"\n🏆 Top 5 详细分析:")
        print("-" * 80)
        
        for i, stock in enumerate(stocks[:5], 1):
            print(f"\n{i}. {stock['name']} ({stock['code']})")
            print(f"   评分：{stock['score']}分 | 价格：HK$ {stock['price']:.2f}")
            print(f"   PE: {stock['pe']:.1f}x | PB: {stock['pb']:.2f}x")
            print(f"   信号：{', '.join(stock['signals']) if stock['signals'] else '无'}")
            
            # 投资建议
            if stock['pe'] < 5 and stock['pb'] < 0.5:
                recommendation = "⭐⭐⭐ 深度价值，强烈推荐关注"
            elif stock['pe'] < 8 and stock['pb'] < 0.8:
                recommendation = "⭐⭐ 低估值，推荐配置"
            else:
                recommendation = "⭐ 估值合理，可关注"
            
            print(f"   建议：{recommendation}")
        
        # 行业配置建议
        print(f"\n💡 {industry}配置建议:")
        if '银行' in industry:
            print("   ✅ 高股息防御，适合长期持有")
            print("   ✅ 关注国有大行和优质城商行")
            print("   ⚠️ 净息差压力，房地产风险")
            print("   📊 建议配置：总仓位的 20-30%")
        elif '医药' in industry:
            print("   ✅ 人口老龄化长期逻辑")
            print("   ✅ 估值处于历史低位")
            print("   ⚠️ 集采政策压力")
            print("   📊 建议配置：总仓位的 15-20%")
        elif '公用' in industry:
            print("   ✅ 现金流稳定，分红率高")
            print("   ✅ 防御性首选")
            print("   ⚠️ 成长性有限")
            print("   📊 建议配置：总仓位的 15-20%")
        elif '能源' in industry:
            print("   ✅ 油价高位，业绩稳定")
            print("   ✅ 城燃需求刚性")
            print("   ⚠️ 油价波动风险")
            print("   📊 建议配置：总仓位的 10-15%")
        elif '基建' in industry:
            print("   ✅ 经济复苏受益")
            print("   ✅ 估值低，分红稳定")
            print("   ⚠️ 贸易摩擦风险")
            print("   📊 建议配置：总仓位的 10-15%")
    
    print("\n" + "=" * 80)
    print("✅ 深度分析完成！")
    print("=" * 80)

if __name__ == "__main__":
    main()
