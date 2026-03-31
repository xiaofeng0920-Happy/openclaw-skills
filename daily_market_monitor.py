#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态因子权重策略 - 每日市场状态监控
- 每日 9:00 AM 检查恒指与 200 日均线关系
- 根据市场状态选择因子配置
- 发送飞书通知
"""

import os
import json
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from futu import *

# 配置
FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"
EMAIL_FROM = "xiaofeng0920@126.com"
EMAIL_TO = "xiaofeng0920@gmail.com"
EMAIL_PASSWORD = "VTxCTBADLJHrVr2W"
CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/dynamic_strategy_state.json"

# 因子配置
FACTOR_CONFIGS = {
    'bull': {'name': '牛市配置', 'momentum': 0.40, 'value': 0.30, 'quality': 0.30},
    'bear': {'name': '熊市防御', 'momentum': 0.10, 'value': 0.45, 'quality': 0.45},
    'sideways': {'name': '震荡市', 'momentum': 0.33, 'value': 0.34, 'quality': 0.33}
}

def get_hsi_data():
    """获取恒指数据（使用 AkShare）"""
    print("使用 AkShare 获取恒指数据...")
    
    try:
        import akshare as ak
        
        # 获取恒指历史数据
        df = ak.stock_hk_daily(symbol='HSI', adjust='qfq')
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        if len(df) == 0:
            print("❌ 获取恒指数据失败")
            return None, None
        
        # 计算 200 日均线
        if len(df) < 200:
            print("⚠️ 数据不足 200 天")
            ma200 = df['close'].mean()
        else:
            ma200 = df['close'].iloc[-200:].mean()
        
        current_price = df['close'].iloc[-1]
        current_date = df['date'].iloc[-1]
        
        print(f"✅ 恒指数据获取成功")
        print(f"   当前点位：{current_price:,.0f}")
        print(f"   200 日均线：{ma200:,.0f}")
        
        return current_price, ma200
        
    except Exception as e:
        print(f"❌ 获取数据失败：{e}")
        return None, None

def determine_market_state(current_price, ma200):
    """判断市场状态"""
    if current_price is None or ma200 is None:
        return 'unknown', 0
    
    deviation = (current_price - ma200) / ma200
    
    if current_price > ma200 * 1.05:
        return 'bull', deviation  # 牛市：恒指 > 200 日均线 +5%
    elif current_price < ma200 * 0.95:
        return 'bear', deviation  # 熊市：恒指 < 200 日均线 -5%
    else:
        return 'sideways', deviation  # 震荡市：恒指 ≈ 200 日均线 ±5%

def load_previous_state():
    """加载上一次的市场状态"""
    if not os.path.exists(CONFIG_FILE):
        return None
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_current_state(market_state, config_name, deviation):
    """保存当前市场状态"""
    state = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'market_state': market_state,
        'config_name': config_name,
        'deviation': deviation,
        'config': FACTOR_CONFIGS[market_state]
    }
    
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    
    return state

def send_feishu_notification(market_state, current_price, ma200, deviation, config_name, config):
    """发送飞书通知"""
    import subprocess
    
    state_cn = {
        'bull': '🐂 牛市',
        'bear': '🐻 熊市',
        'sideways': '📊 震荡市',
        'unknown': '❓ 未知'
    }
    
    message = f"""
📊 动态策略市场状态监控

📅 监控时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}
🔍 市场状态：{state_cn.get(market_state, market_state)}

📈 恒指数据:
  当前点位：{current_price:,.0f} (如果可用)
  200 日均线：{ma200:,.0f} (如果可用)
  偏离度：{deviation*100:+.1f}%

⚙️ 当前配置:
  配置名称：{config_name}
  动量因子：{config['momentum']*100:.0f}%
  价值因子：{config['value']*100:.0f}%
  质量因子：{config['quality']*100:.0f}%

💡 操作建议:
  • 牛市：使用当前配置（40/30/30），积极做多
  • 熊市：使用防御配置（10/45/45），价值 + 质量防御
  • 震荡市：使用均衡配置（33/34/33），稳健操作

---
小巴量化投资系统
"""
    
    cmd = [
        "openclaw", "message", "send",
        "--channel", "feishu",
        "--target", FEISHU_USER_ID,
        "--message", message.strip()
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ 飞书通知已发送")
        return True
    except Exception as e:
        print(f"❌ 发送飞书通知失败：{e}")
        return False

def send_email_notification(market_state, current_price, ma200, deviation, config_name, config):
    """发送邮件通知"""
    state_cn = {
        'bull': '🐂 牛市',
        'bear': '🐻 熊市',
        'sideways': '📊 震荡市',
        'unknown': '❓ 未知'
    }
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = f"动态策略市场状态监控 - {datetime.now().strftime('%Y-%m-%d')}"
    
    body = f"""
锋哥好～

今日市场状态监控完成！

📊 市场状态：{state_cn.get(market_state, market_state)}

📈 恒指数据:
  当前点位：{current_price:,.0f}
  200 日均线：{ma200:,.0f}
  偏离度：{deviation*100:+.1f}%

⚙️ 当前因子配置:
  配置名称：{config_name}
  动量因子：{config['momentum']*100:.0f}%
  价值因子：{config['value']*100:.0f}%
  质量因子：{config['quality']*100:.0f}%

💡 操作建议:
  • 牛市：使用当前配置（40/30/30），积极做多
  • 熊市：使用防御配置（10/45/45），价值 + 质量防御
  • 震荡市：使用均衡配置（33/34/33），稳健操作

下次检查：明天 9:00 AM

祝投资顺利！
小巴量化投资系统
"""
    
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP_SSL("smtp.126.com", 465)
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("✅ 邮件通知已发送")
        return True
    except Exception as e:
        print(f"❌ 发送邮件失败：{e}")
        return False

def main():
    """主函数"""
    print(f"[{datetime.now()}] 开始每日市场状态监控...")
    
    # 获取恒指数据
    current_price, ma200 = get_hsi_data()
    
    if current_price is None:
        print("❌ 获取恒指数据失败，使用上一次状态")
        # 如果获取失败，使用上一次的状态
        previous_state = load_previous_state()
        if previous_state:
            print(f"上一次市场状态：{previous_state['market_state']}")
            return
        else:
            print("❌ 无历史状态，使用默认配置（牛市）")
            market_state = 'bull'
            deviation = 0
    else:
        # 判断市场状态
        market_state, deviation = determine_market_state(current_price, ma200)
        print(f"市场状态：{market_state} (偏离度：{deviation*100:+.1f}%)")
    
    # 获取当前配置
    config = FACTOR_CONFIGS.get(market_state, FACTOR_CONFIGS['bull'])
    config_name = config['name']
    
    # 保存当前状态
    save_current_state(market_state, config_name, deviation)
    
    # 检查市场状态是否变化
    previous_state = load_previous_state()
    state_changed = False
    
    if previous_state and previous_state.get('market_state') != market_state:
        state_changed = True
        print(f"⚠️ 市场状态变化：{previous_state.get('market_state')} → {market_state}")
    
    # 发送通知
    if current_price and ma200:
        send_feishu_notification(market_state, current_price, ma200, deviation, config_name, config)
        send_email_notification(market_state, current_price, ma200, deviation, config_name, config)
    
    print(f"[{datetime.now()}] 市场状态监控完成")
    print(f"当前配置：{config_name}")
    print(f"因子权重：动量{config['momentum']*100:.0f}% + 价值{config['value']*100:.0f}% + 质量{config['quality']*100:.0f}%")

if __name__ == "__main__":
    import pandas as pd
    main()
