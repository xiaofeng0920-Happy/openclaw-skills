#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财报日期提醒 - 监控持仓股票财报发布日期
提前 3 天、1 天、当天发送提醒
"""

import json
import requests
from datetime import datetime, timedelta

CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
EARNINGS_CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/config/earnings_calendar.json"
FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"

def load_portfolio():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_earnings_config():
    try:
        with open(EARNINGS_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "earnings_calendar": {},
            "reminded": []
        }

def save_earnings_config(config):
    import os
    os.makedirs(os.path.dirname(EARNINGS_CONFIG_FILE), exist_ok=True)
    with open(EARNINGS_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def get_earnings_date(symbol):
    """获取财报日期（使用免费 API）"""
    try:
        # 使用 Finnhub 财报日历 API
        with open('/Users/zhaoxf/.openclaw/workspace/config/finnhub_api_key.txt', 'r') as f:
            api_key = f.read().strip()
        
        # 查询本月和下月财报
        current_month = datetime.now().strftime('%Y-%m')
        next_month = (datetime.now().replace(day=28) + timedelta(days=4)).strftime('%Y-%m')
        
        url = "https://finnhub.io/api/v1/calendar/earnings"
        params = {
            "symbol": symbol.replace('.HK', '') if '.HK' in symbol else symbol,
            "token": api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'earnings' in data and len(data['earnings']) > 0:
                return data['earnings'][0].get('date', None)
    except Exception as e:
        print(f"获取财报日期失败：{e}")
    
    return None

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

def check_earnings():
    print(f"[{datetime.now()}] 检查财报日期...")
    
    portfolio = load_portfolio()
    earnings_config = load_earnings_config()
    
    today = datetime.now().date()
    
    # 获取所有持仓股票代码
    us_symbols = [(h['symbol'], h['name']) for h in portfolio['accounts']['us_stocks']['holdings']]
    hk_symbols = [(h['symbol'], h['name']) for h in portfolio['accounts']['hk_stocks']['holdings']]
    all_symbols = us_symbols + hk_symbols
    
    upcoming_earnings = []
    
    for symbol, name in all_symbols:
        # 检查是否已缓存
        if symbol in earnings_config['earnings_calendar']:
            earnings_date = earnings_config['earnings_calendar'][symbol]
        else:
            # 获取财报日期
            earnings_date = get_earnings_date(symbol)
            if earnings_date:
                earnings_config['earnings_calendar'][symbol] = earnings_date
        
        if earnings_date:
            try:
                earnings_dt = datetime.strptime(earnings_date, '%Y-%m-%d').date()
                days_until = (earnings_dt - today).days
                
                # 提前 3 天、1 天、当天提醒
                if days_until in [3, 1, 0]:
                    upcoming_earnings.append({
                        "symbol": symbol,
                        "name": name,
                        "date": earnings_date,
                        "days_until": days_until
                    })
            except:
                pass
    
    # 保存配置
    save_earnings_config(earnings_config)
    
    if upcoming_earnings:
        # 发送飞书
        message_lines = ["📅 财报日历提醒", f"📅 {today.strftime('%Y-%m-%d')}", ""]
        
        for item in upcoming_earnings:
            if item['days_until'] == 0:
                emoji = "🔴"
                text = "今天"
            elif item['days_until'] == 1:
                emoji = "🟡"
                text = "明天"
            else:
                emoji = "🟢"
                text = f"{item['days_until']} 天后"
            
            message_lines.append(f"{emoji} {item['name']} ({item['symbol']})")
            message_lines.append(f"   财报日期：{item['date']} ({text})")
            message_lines.append("")
        
        send_feishu("\n".join(message_lines))
        print(f"✅ 已发送 {len(upcoming_earnings)} 条财报提醒")
    else:
        print("ℹ️ 未来 3 天无财报")
    
    return True

if __name__ == "__main__":
    success = check_earnings()
    exit(0 if success else 1)
