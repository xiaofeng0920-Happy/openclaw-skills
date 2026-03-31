#!/usr/bin/env python3
"""
Tavily Search 测试脚本
"""

import os
import sys
from datetime import datetime

def test_tavily_search(query="test search"):
    """测试 Tavily 搜索"""
    
    print("=" * 60)
    print("🔍 Tavily Search 测试")
    print("=" * 60)
    print()
    
    # 获取 API Key
    api_key = os.environ.get('TAVILY_API_KEY')
    
    if not api_key:
        # 尝试从.env 文件读取
        env_file = os.path.expanduser("~/.openclaw/.env")
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('TAVILY_API_KEY='):
                        api_key = line.split('=')[1].strip()
                        break
    
    if not api_key:
        print("❌ 错误：未找到 Tavily API Key")
        print()
        print("请先配置 API Key：")
        print("  1. 访问 https://tavily.com 获取 API Key")
        print("  2. 运行：bash ~/.openclaw/workspace/scripts/configure-tavily.sh")
        return False
    
    print(f"✅ API Key 已找到：{api_key[:10]}...")
    print()
    
    try:
        from tavily import TavilyClient
        
        client = TavilyClient(api_key=api_key)
        
        print(f"📡 搜索查询：{query}")
        print()
        
        # 执行搜索
        response = client.search(query, max_results=5)
        
        if 'results' in response:
            results = response['results']
            print(f"✅ 搜索成功！找到 {len(results)} 条结果")
            print()
            print("-" * 60)
            
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.get('title', '无标题')}")
                print(f"   URL: {result.get('url', '无链接')}")
                print(f"   内容：{result.get('content', '无内容')[:200]}...")
            
            print()
            print("-" * 60)
            print()
            print("✅ Tavily Search 配置成功！")
            return True
        else:
            print("⚠️  未找到搜索结果")
            return False
            
    except ImportError:
        print("❌ 错误：tavily 库未安装")
        print()
        print("安装命令：")
        print("  pip3 install tavily-python")
        return False
        
    except Exception as e:
        print(f"❌ 错误：{e}")
        print()
        print("可能原因：")
        print("  1. API Key 不正确")
        print("  2. 网络连接问题")
        print("  3. API 配额已用尽")
        return False

if __name__ == "__main__":
    # 获取查询参数
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "AI news today"
    
    success = test_tavily_search(query)
    sys.exit(0 if success else 1)
