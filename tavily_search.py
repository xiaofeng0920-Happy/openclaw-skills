#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tavily Search Skill - AI 专用搜索引擎
"""

import os
import sys
import json
import requests

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")

def search(query, search_depth="basic", topic="general"):
    """使用 Tavily 搜索"""
    if not TAVILY_API_KEY:
        return {
            "error": "未配置 TAVILY_API_KEY",
            "setup": "请访问 https://tavily.com 注册并获取 API Key"
        }
    
    url = "https://api.tavily.com/search"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}"
    }
    data = {
        "query": query,
        "search_depth": search_depth,
        "topic": topic,
        "max_results": 5
    }
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def main():
    if len(sys.argv) < 2:
        print("用法：tavily-search <搜索关键词>")
        print("示例：tavily-search 'AI 最新进展 2026'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    result = search(query)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
