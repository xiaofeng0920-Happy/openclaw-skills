#!/usr/bin/env python3
"""
Stock News: Stock news via akshare.
Supports: A-shares and HK stocks
"""

import sys
import json

try:
    import akshare as ak
except ImportError:
    print(json.dumps({"error": "akshare not installed", "message": "Run: pip3 install akshare -U"}), file=sys.stderr)
    sys.exit(1)

def query_news(symbol, limit=10):
    try:
        symbol = str(symbol).strip()
        
        # A-share news
        if symbol.isdigit() and (symbol.startswith("6") or symbol.startswith("0") or symbol.startswith("3")):
            try:
                data = ak.stock_news_em(symbol=symbol)
                if data is not None and len(data) > 0:
                    news_list = []
                    for _, row in data.head(limit).iterrows():
                        news_list.append({
                            "title": str(row.get("新闻标题", "")),
                            "source": str(row.get("文章来源", "")),
                            "date": str(row.get("发布时间", "")),
                            "url": str(row.get("新闻链接", ""))
                        })
                    
                    return {
                        "source": "akshare",
                        "type": "news",
                        "symbol": symbol,
                        "name": symbol,
                        "data": {"news": news_list, "count": len(news_list)},
                        "update_time": ""
                    }
            except Exception as e:
                pass
        
        # HK stock news - use stock code without HK prefix
        elif symbol.startswith("HK"):
            code = symbol[2:]
            try:
                data = ak.stock_news_em(symbol=code)
                if data is not None and len(data) > 0:
                    news_list = []
                    for _, row in data.head(limit).iterrows():
                        news_list.append({
                            "title": str(row.get("新闻标题", "")),
                            "source": str(row.get("文章来源", "")),
                            "date": str(row.get("发布时间", "")),
                            "url": str(row.get("新闻链接", ""))
                        })
                    
                    return {
                        "source": "akshare",
                        "type": "news",
                        "symbol": symbol,
                        "name": code,
                        "data": {"news": news_list, "count": len(news_list)},
                        "update_time": ""
                    }
            except Exception as e:
                pass
        
        return None
    except Exception as e:
        print("Query failed: {}".format(e), file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: stock_news.py <symbol> [limit]", file=sys.stderr)
        sys.exit(1)
    
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    result = query_news(sys.argv[1], limit)
    
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "News query failed", "symbol": sys.argv[1]}))
        sys.exit(1)

if __name__ == "__main__":
    main()
