#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股行业分类统计 - 每个行业 Top 5
"""

import json
from futu import *
from collections import defaultdict

def get_stock_industry(stock_code):
    """获取股票行业分类"""
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    try:
        # 获取板块信息
        ret, data = quote_ctx.get_stock_basicinfo(market=TrdMarket.HK, stock_code=stock_code)
        
        if ret == RET_OK and data is not None and not data.empty:
            row = data.iloc[0]
            industry = row.get('industry', '')
            return industry if industry else '其他'
        return '未知'
    except:
        return '其他'
    finally:
        quote_ctx.close()

def main():
    print("=" * 70)
    print("📊 港股行业分类统计 - 每个行业 Top 5")
    print("=" * 70)
    
    # 读取汇总报告
    with open('reports/hk_market_full_summary.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_stocks = data['all_results']
    
    # 只保留推荐股票 (评分≥60)
    recommended = [s for s in all_stocks if s['score'] >= 60]
    print(f"\n✅ 推荐股票总数：{len(recommended)} 只")
    
    # 按行业分类
    industries = defaultdict(list)
    
    print("\n📋 正在获取行业分类...")
    
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    for i, stock in enumerate(recommended, 1):
        code = stock['code'].replace('HK.', '')
        
        # 简单行业分类（根据代码段和名称）
        industry = classify_industry(code, stock['name'])
        stock['industry'] = industry
        industries[industry].append(stock)
        
        if i % 100 == 0:
            print(f"  处理进度：{i}/{len(recommended)}")
    
    quote_ctx.close()
    
    # 统计每个行业
    print("\n" + "=" * 70)
    print("📈 行业分布统计")
    print("=" * 70)
    
    industry_summary = []
    for industry, stocks in sorted(industries.items(), key=lambda x: len(x[1]), reverse=True):
        industry_summary.append({
            'industry': industry,
            'count': len(stocks),
            'stocks': sorted(stocks, key=lambda x: x['score'], reverse=True)[:5]
        })
        print(f"{industry}: {len(stocks)} 只")
    
    # 生成报告
    report = {
        'timestamp': data['timestamp'],
        'total_recommended': len(recommended),
        'industries': industry_summary
    }
    
    # 保存行业报告
    with open('reports/hk_industry_top5.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("🏆 各行业 Top 5")
    print("=" * 70)
    
    for item in industry_summary[:10]:  # 显示前 10 个行业
        print(f"\n📌 {item['industry']} ({item['count']}只)")
        print("-" * 70)
        print(f"{'排名':<4} {'代码':<12} {'名称':<20} {'评分':<6} {'PE':<8} {'PB':<8}")
        print("-" * 70)
        
        for i, stock in enumerate(item['stocks'][:5], 1):
            pe = f"{stock['pe']:.1f}" if stock['pe'] > 0 else 'N/A'
            pb = f"{stock['pb']:.2f}" if stock['pb'] > 0 else 'N/A'
            print(f"{i:<4} {stock['code']:<12} {stock['name']:<20} {stock['score']:<6} {pe:<8} {pb:<8}")
    
    print("\n" + "=" * 70)
    print(f"💾 完整报告：reports/hk_industry_top5.json")
    print("=" * 70)

def classify_industry(code, name):
    """根据代码和名称简单分类行业"""
    name_upper = name.upper()
    
    # 银行
    if any(k in name_upper for k in ['BANK', '银行', 'CITIC', 'ICBC', 'CCB', 'BOC', 'ABC', 'BOCOM', 'CEB', 'CMB', 'PING AN']):
        return '🏦 银行金融'
    
    # 保险
    if any(k in name_upper for k in ['INSUR', '保险', 'PING AN', 'CPIC', 'CHINA LIFE']):
        return '🛡️ 保险'
    
    # 地产/物业
    if any(k in name_upper for k in ['PROPERTY', 'REAL ESTATE', '地产', '置业', 'CHINA OVERSEAS', 'COLI', 'CIFI', 'SHIMAO']):
        return '🏠 房地产'
    
    # 物业管理
    if any(k in name_upper for k in ['SERVICES', '服务', '物业', 'MGT', 'LIFESTYLE']):
        return '🏢 物业管理'
    
    # 基建/交通
    if any(k in name_upper for k in ['EXPRESSWAY', 'HIGHWAY', 'PORT', '港口', '高速', '交通', 'RAILWAY', 'AIRPORT']):
        return '🚄 基建交通'
    
    # 能源/石油
    if any(k in name_upper for k in ['OIL', 'GAS', '能源', '石油', 'CNOOC', 'SINOPEC', 'PETRO']):
        return '⛽ 能源石油'
    
    # 医药/医疗
    if any(k in name_upper for k in ['PHARMA', 'MEDICAL', '医药', '医疗', 'BIO', 'HEALTH', 'DRUG']):
        return '💊 医药医疗'
    
    # 科技/电子
    if any(k in name_upper for k in ['TECH', 'ELECTRONIC', '科技', '电子', 'SEMICONDUCTOR', 'DIGITAL']):
        return '💻 科技电子'
    
    # 消费/零售
    if any(k in name_upper for k in ['RETAIL', 'CONSUMER', '消费', '零售', 'FOOD', 'BEVERAGE', 'LIQUOR']):
        return '🛒 消费零售'
    
    # 制造/工业
    if any(k in name_upper for k in ['MANUFACTUR', 'INDUSTRIAL', '制造', '工业', 'MACHINERY', 'CEMENT', 'STEEL']):
        return '🏭 制造工业'
    
    # 电信
    if any(k in name_upper for k in ['TELECOM', 'COMMUNICATION', '电信', '通讯', 'CHINA MOBILE', 'UNICOM', 'TELECOM']):
        return '📱 电信通讯'
    
    # 公用事业
    if any(k in name_upper for k in ['UTILITY', 'WATER', 'ENVIRONMENT', '公用', '水务', '环保', 'POWER', 'ELECTRIC']):
        return '💡 公用事业'
    
    # 航运/物流
    if any(k in name_upper for k in ['SHIP', 'LOGISTICS', '航运', '物流', 'COSCO', 'TRANSPORT']):
        return '🚢 航运物流'
    
    # 证券/金融
    if any(k in name_upper for k in ['SECURITIES', 'CAPITAL', '证券', '金融', 'ASSET', 'FUND', 'WEALTH']):
        return '💰 证券金融'
    
    # 教育
    if any(k in name_upper for k in ['EDUCATION', '教育', 'EDU', 'SCHOOL', 'UNIVERSITY']):
        return '📚 教育'
    
    # 旅游/酒店
    if any(k in name_upper for k in ['TOUR', 'TRAVEL', 'HOTEL', '旅游', '酒店', 'HOSPITALITY']):
        return '🏨 旅游酒店'
    
    # 汽车
    if any(k in name_upper for k in ['AUTO', 'MOTOR', '汽车', 'VEHICLE', 'BYD', 'GEELY', 'GWM']):
        return '🚗 汽车'
    
    # 纺织/服装
    if any(k in name_upper for k in ['TEXTILE', 'GARMENT', 'FASHION', '纺织', '服装', 'APPAREL']):
        return '👕 纺织服装'
    
    # 农业
    if any(k in name_upper for k in ['AGRI', 'FARM', '农业', '畜牧', 'FEED']):
        return '🌾 农业'
    
    return '📦 其他行业'

if __name__ == "__main__":
    main()
