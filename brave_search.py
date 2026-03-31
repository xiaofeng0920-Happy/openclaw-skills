#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Brave Search Skill - 隐私优先的搜索引擎
"""

import os
import sys
import json
import requests

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")

def search(query, count=10, country="US"):
    """使用 Brave Search"""
    if not BRAVE_API_KEY:
        return {
            "error": "未配置 BRAVE_API_KEY",
            "setup": "请访问 https://brave.com/search/api 注册并获取 API Key"
        }
    
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY
    }
    params = {
        "q": query,
        "count": count,
        "country": country
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    if len(sys.argv) < 2:
        print("用法：brave-search <搜索关键词>")
        print("示例：brave-search 'AI 新闻 2026'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    result = search(query)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
