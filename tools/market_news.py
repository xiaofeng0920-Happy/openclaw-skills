#!/usr/bin/env python3
"""
Market News: Real-time market news from Caixin (财新).
Supports: Market dynamics, policy news, financial news
Sorted by recency (newest first).
"""

import sys
import json
import argparse
from datetime import date, datetime

try:
    import akshare as ak
except ImportError:
    print(json.dumps({"error": "akshare not installed", "message": "Run: pip3 install akshare -U"}), file=sys.stderr)
    sys.exit(1)

DISCLAIMER = "⚠️ 免责声明：本数据仅供参考，不构成投资建议。市场有风险，投资需谨慎。"

class DateEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if isinstance(o, float) and (o != o):  # NaN check
            return None
        return super().default(o)

def query_caixin_news(limit=20):
    """Query market news from Caixin (财新)"""
    try:
        data = ak.stock_news_main_cx()
        if data is None or len(data) == 0:
            return None
        
        # Data is already sorted by recency (newest first)
        news_list = []
        for _, row in data.head(limit).iterrows():
            # Extract date from URL if available
            url = str(row.get('url', ''))
            news_date = ''
            if '2026-' in url or '2025-' in url or '2024-' in url:
                # Extract date from URL pattern: 2026-03-03/102418973.html
                import re
                match = re.search(r'(\d{4}-\d{2}-\d{2})', url)
                if match:
                    news_date = match.group(1)
            
            news_item = {
                "tag": str(row.get('tag', '')),
                "title": str(row.get('summary', ''))[:100],  # Use summary as title
                "summary": str(row.get('summary', '')),
                "url": url,
                "date": news_date
            }
            news_list.append(news_item)
        
        return {
            "source": "stock_news_main_cx",
            "source_name": "财新网",
            "type": "market_news",
            "mode": "market",
            "data": {
                "news": news_list,
                "count": len(news_list)
            },
            "disclaimer": DISCLAIMER
        }
    except Exception as e:
        print(f"Query failed: {e}", file=sys.stderr)
        return None

def query_policy_news(limit=20):
    """Query policy news from CCTV"""
    try:
        data = ak.news_cctv()
        if data is None or len(data) == 0:
            return None
        
        # CCTV news doesn't have importance field, use date order
        news_list = []
        for _, row in data.head(limit).iterrows():
            news_item = {
                "date": str(row.get('date', '')),
                "title": str(row.get('title', '')),
                "content": str(row.get('content', ''))[:500] + "..." if len(str(row.get('content', ''))) > 500 else str(row.get('content', ''))
            }
            news_list.append(news_item)
        
        return {
            "source": "news_cctv",
            "source_name": "央视新闻",
            "type": "market_news",
            "mode": "policy",
            "data": {
                "news": news_list,
                "count": len(news_list)
            },
            "disclaimer": DISCLAIMER
        }
    except Exception as e:
        print(f"Query failed: {e}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description='Query market news')
    parser.add_argument('--policy', action='store_true', help='Query policy news (CCTV)')
    parser.add_argument('--limit', type=int, default=20, help='Number of news items (default: 20)')
    
    args = parser.parse_args()
    
    if args.policy:
        result = query_policy_news(args.limit)
    else:
        result = query_caixin_news(args.limit)
    
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2, cls=DateEncoder))
    else:
        print(json.dumps({"error": "News query failed", "mode": "policy" if args.policy else "market"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
