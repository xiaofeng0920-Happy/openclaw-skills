#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取港股指数成分股
- 恒生指数（HSI）：约 80 只
- 恒生科技指数（HSTECH）：约 30 只
- 国企指数（HSCEI）：约 50 只
- 恒生综合指数（HSCI）：约 500 只
"""

import akshare as ak
import json
from datetime import datetime

def get_hsi_constituents():
    """获取恒生指数成分股"""
    print("获取恒生指数成分股...")
    try:
        df = ak.index_stock_cons(symbol="恒生指数")
        if df is not None and len(df) > 0:
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': row.get('品种代码', ''),
                    'name': row.get('品种名称', '')
                })
            print(f"✅ 恒生指数成分股：{len(stocks)} 只")
            return stocks
    except Exception as e:
        print(f"❌ 获取恒生指数成分股失败：{e}")
    return []

def get_hstech_constituents():
    """获取恒生科技指数成分股"""
    print("获取恒生科技指数成分股...")
    try:
        df = ak.index_stock_cons(symbol="恒生科技指数")
        if df is not None and len(df) > 0:
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': row.get('品种代码', ''),
                    'name': row.get('品种名称', '')
                })
            print(f"✅ 恒生科技指数成分股：{len(stocks)} 只")
            return stocks
    except Exception as e:
        print(f"❌ 获取恒生科技指数成分股失败：{e}")
    return []

def get_hscei_constituents():
    """获取国企指数成分股"""
    print("获取国企指数成分股...")
    try:
        df = ak.index_stock_cons(symbol="国企指数")
        if df is not None and len(df) > 0:
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': row.get('品种代码', ''),
                    'name': row.get('品种名称', '')
                })
            print(f"✅ 国企指数成分股：{len(stocks)} 只")
            return stocks
    except Exception as e:
        print(f"❌ 获取国企指数成分股失败：{e}")
    return []

def get_hsci_constituents():
    """获取恒生综合指数成分股"""
    print("获取恒生综合指数成分股...")
    try:
        # 恒生综合指数包含多个子指数，这里获取大盘指数成分股
        df = ak.index_stock_cons(symbol="恒生综合指数")
        if df is not None and len(df) > 0:
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': row.get('品种代码', ''),
                    'name': row.get('品种名称', '')
                })
            print(f"✅ 恒生综合指数成分股：{len(stocks)} 只")
            return stocks
    except Exception as e:
        print(f"❌ 获取恒生综合指数成分股失败：{e}")
    return []

def merge_stocks(stock_lists):
    """合并股票列表，去重"""
    merged = {}
    for stocks in stock_lists:
        for stock in stocks:
            code = stock['code']
            if code and code not in merged:
                merged[code] = stock
    return list(merged.values())

def save_stock_pool(stocks, filename, description):
    """保存股票池"""
    output = {
        'description': description,
        'count': len(stocks),
        'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'stocks': stocks
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 股票池已保存：{filename} ({len(stocks)} 只)")

def main():
    """主函数"""
    print(f"[{datetime.now()}] 开始获取港股指数成分股...")
    
    # 获取各指数成分股
    hsi_stocks = get_hsi_constituents()
    hstech_stocks = get_hstech_constituents()
    hscei_stocks = get_hscei_constituents()
    hsci_stocks = get_hsci_constituents()
    
    # 选项 B：恒指 + 恒生科技 + 国企指数
    option_b_stocks = merge_stocks([hsi_stocks, hstech_stocks, hscei_stocks])
    save_stock_pool(
        option_b_stocks,
        '/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/stock_pool_option_b.json',
        '选项 B：恒指 + 恒生科技 + 国企指数（约 200 只）'
    )
    
    # 选项 A：恒生综合指数
    if hsci_stocks:
        save_stock_pool(
            hsci_stocks,
            '/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/stock_pool_option_a.json',
            '选项 A：恒生综合指数（约 500 只）'
        )
    else:
        # 如果获取失败，使用选项 B 作为选项 A
        print("⚠️ 恒生综合指数获取失败，使用选项 B 作为选项 A")
        save_stock_pool(
            option_b_stocks,
            '/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/stock_pool_option_a.json',
            '选项 A：恒指 + 恒生科技 + 国企指数（备选，约 200 只）'
        )
    
    # 生成 Python 格式的股票池
    print("生成 Python 格式股票池...")
    
    # 选项 B 格式
    option_b_python = "STOCK_POOL = [\n"
    for stock in option_b_stocks:
        if stock['code']:
            option_b_python += f"    {{'code': '{stock['code']}.HK', 'name': '{stock['name']}'}},\n"
    option_b_python += "]"
    
    with open('/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/stock_pool_option_b.py', 'w', encoding='utf-8') as f:
        f.write(option_b_python)
    
    print(f"✅ Python 格式股票池已生成")
    
    print(f"\n[总结]")
    print(f"恒生指数成分股：{len(hsi_stocks)} 只")
    print(f"恒生科技指数成分股：{len(hstech_stocks)} 只")
    print(f"国企指数成分股：{len(hscei_stocks)} 只")
    print(f"恒生综合指数成分股：{len(hsci_stocks)} 只")
    print(f"选项 B（恒指 + 恒生科技 + 国企）：{len(option_b_stocks)} 只")
    
    print(f"\n[{datetime.now()}] 获取完成")

if __name__ == "__main__":
    main()
