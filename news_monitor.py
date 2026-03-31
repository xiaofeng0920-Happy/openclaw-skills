#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓新闻监控 - 监控持仓股票相关重大新闻
每天 7:00 AM 自动运行，推送重要新闻
"""

import json
import requests
from datetime import datetime, timedelta

CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
NEWS_CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/config/news_monitor_config.json"
FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"

def load_portfolio():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_news_config():
    try:
        with open(NEWS_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "last_news_time": {},
            "keywords": ["财报", "盈利", "收购", "合并", "监管", "诉讼", "产品发布", "CEO", "裁员"]
        }

def search_news(symbol, keyword=None):
    """搜索新闻（使用免费 API）"""
    news_list = []
    
    # 使用 Finnhub 新闻 API（如果有 API key）
    try:
        with open('/Users/zhaoxf/.openclaw/workspace/config/finnhub_api_key.txt', 'r') as f:
            api_key = f.read().strip()
        
        # 搜索最近 24 小时新闻
        from_ts = int((datetime.now() - timedelta(days=1)).timestamp())
        to_ts = int(datetime.now().timestamp())
        
        url = f"https://finnhub.io/api/v1/company-news"
        params = {
            "symbol": symbol.replace('.HK', '') if '.HK' in symbol else symbol,
            "from": from_ts,
            "to": to_ts,
            "token": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data[:5]:  # 最多 5 条
                news_list.append({
                    "title": item.get('headline', ''),
                    "summary": item.get('summary', ''),
                    "url": item.get('url', ''),
                    "source": item.get('source', ''),
                    "time": datetime.fromtimestamp(item.get('datetime', 0)).strftime('%Y-%m-%d %H:%M')
                })
    except Exception as e:
        print(f"获取新闻失败：{e}")
    
    return news_list

def filter_important_news(news_list, keywords):
    """筛选重要新闻"""
    important = []
    for news in news_list:
        title = news['title'].lower()
        summary = news['summary'].lower()
        
        # 检查是否包含关键词
        for kw in keywords:
            if kw.lower() in title or kw.lower() in summary:
                important.append(news)
                break
    
    return important

def send_feishu(message):
    import subprocess
    cmd = [
        "openclaw", "message", "send",
        "--channel", "feishu",
        "--target", FEISHU_USER_ID,
        "--message", message
    ]
    try:
        subprocess.run(cmd, check=True)
        print("✅ 飞书消息已发送")
    except Exception as e:
        print(f"❌ 发送失败：{e}")

def monitor_news():
    print(f"[{datetime.now()}] 开始监控新闻...")
    
    portfolio = load_portfolio()
    news_config = load_news_config()
    
    # 获取所有持仓股票代码
    us_symbols = [h['symbol'] for h in portfolio['accounts']['us_stocks']['holdings']]
    hk_symbols = [h['symbol'] for h in portfolio['accounts']['hk_stocks']['holdings']]
    all_symbols = us_symbols + hk_symbols
    
    print(f"监控 {len(all_symbols)} 只股票新闻")
    
    important_news = []
    
    for symbol in all_symbols:
        print(f"  搜索 {symbol}...")
        news_list = search_news(symbol)
        filtered = filter_important_news(news_list, news_config['keywords'])
        important_news.extend(filtered)
    
    if important_news:
        # 去重
        seen = set()
        unique_news = []
        for news in important_news:
            if news['url'] not in seen:
                seen.add(news['url'])
                unique_news.append(news)
        
        # 发送飞书
        message_lines = ["📰 持仓新闻监控", f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}", f"发现 {len(unique_news)} 条重要新闻", ""]
        
        for i, news in enumerate(unique_news[:10], 1):  # 最多 10 条
            message_lines.append(f"{i}. {news['title']}")
            message_lines.append(f"   来源：{news['source']} | 时间：{news['time']}")
            message_lines.append(f"   🔗 {news['url']}")
            message_lines.append("")
        
        send_feishu("\n".join(message_lines))
        print(f"✅ 已发送 {len(unique_news)} 条新闻")
    else:
        print("ℹ️ 无重要新闻")
    
    return True

if __name__ == "__main__":
    success = monitor_news()
    exit(0 if success else 1)
