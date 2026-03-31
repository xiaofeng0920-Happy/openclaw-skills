#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
川普动态监控 - RSS 版本（无需 API key）
每 30 分钟检查一次
"""

import feedparser
import subprocess
from datetime import datetime

FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"
LAST_POST_FILE = "/Users/zhaoxf/.openclaw/workspace/config/trump_last_post.txt"

# RSS 源（使用第三方聚合）
RSS_FEEDS = [
    "https://search.app.nixnet.services/search?q=Donald+Trump+Truth+Social&format=rss",
]

def get_last_post():
    try:
        with open(LAST_POST_FILE, 'r') as f:
            return f.read().strip()
    except:
        return None

def save_last_post(title):
    import os
    os.makedirs(os.path.dirname(LAST_POST_FILE), exist_ok=True)
    with open(LAST_POST_FILE, 'w') as f:
        f.write(title)

def translate_text(text):
    """翻译"""
    try:
        import requests
        url = "https://api.mymemory.translated.net/get"
        params = {'q': text[:500], 'langpair': 'en|zh-CN'}
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('responseData', {}).get('translatedText', text)
    except:
        pass
    return text

def send_feishu(message):
    cmd = ["openclaw", "message", "send", "--channel", "feishu", "--target", FEISHU_USER_ID, "--message", message]
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"发送失败：{e}")
        return False

def monitor():
    print(f"[{datetime.now()}] 检查川普动态...")
    
    last_post = get_last_post()
    new_posts = []
    
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                title = entry.get('title', '')
                if title and title != last_post:
                    new_posts.append({
                        'title': title,
                        'link': entry.get('link', ''),
                        'published': entry.get('published', ''),
                        'source': feed.feed.get('title', 'Unknown')
                    })
        except Exception as e:
            print(f"RSS 失败：{e}")
    
    if new_posts:
        print(f"✅ 发现 {len(new_posts)} 条新动态")
        
        message_lines = ["🇺🇸 川普动态监控", f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
        
        for post in new_posts[:3]:
            title = post['title']
            title_zh = translate_text(title)
            
            message_lines.append(f"📰 {post['source']}")
            message_lines.append(f"📝 {title}")
            message_lines.append(f"📖 {title_zh}")
            message_lines.append(f"🔗 {post['link']}")
            message_lines.append(f"🕐 {post['published']}")
            message_lines.append("")
        
        message_lines.append("⏰ 下次检查：30 分钟后")
        
        send_feishu("\n".join(message_lines))
        
        # 保存
        if new_posts:
            save_last_post(new_posts[0]['title'])
    else:
        print("ℹ️ 无新动态")

if __name__ == "__main__":
    monitor()
