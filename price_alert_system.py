#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时价格预警系统
监控锋哥持仓股票，突破阈值自动发送飞书预警
"""

import json
from pathlib import Path
from datetime import datetime
import sys
sys.path.insert(0, str(Path(__file__).parent))

from realtime_data_api import get_realtime_quote

# ============ 配置 ============
WATCHLIST_FILE = Path(__file__).parent / 'config' / 'feng_watchlist.json'
ALERT_COOLDOWN = 60  # 预警冷却时间 (分钟)

# 锋哥持仓监控列表
WATCHLIST = {
    # 港股
    'HK.00700': {'name': '腾讯控股', 'warn_up': 500, 'warn_down': 470},
    'HK.09988': {'name': '阿里巴巴', 'warn_up': 125, 'warn_down': 115},
    'HK.00883': {'name': '中海油', 'warn_up': 30, 'warn_down': 27},
    'HK.02338': {'name': '潍柴动力', 'warn_up': 29, 'warn_down': 26},
    # 美股
    'US.NVDA': {'name': '英伟达', 'warn_up': 175, 'warn_down': 160},
    'US.MSFT': {'name': '微软', 'warn_up': 370, 'warn_down': 340},
    'US.GOOGL': {'name': '谷歌', 'warn_up': 285, 'warn_down': 265},
    # A 股
    '600519.SH': {'name': '贵州茅台', 'warn_up': 1450, 'warn_down': 1380},
}

# ============================


def check_alerts():
    """检查价格预警"""
    print('='*80)
    print('🔔 实时价格预警系统')
    print('='*80)
    print(f'监控时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'监控股票：{len(WATCHLIST)} 只')
    print()
    
    alerts = []
    
    for code, config in WATCHLIST.items():
        # 获取实时价格
        data = get_realtime_quote(code)
        
        if not data:
            print(f'❌ {code} 获取价格失败')
            continue
        
        price = data['price']
        change_pct = data['change_pct']
        name = config['name']
        warn_up = config.get('warn_up', None)
        warn_down = config.get('warn_down', None)
        
        # 显示价格
        source = data.get('source', '未知')
        print(f'{code:<12} {name:<12} ${price:>9.2f} ({change_pct:>7.2f}%) [{source}]')
        
        # 检查预警
        if warn_up and price >= warn_up:
            alert = {
                'code': code,
                'name': name,
                'price': price,
                'change_pct': change_pct,
                'type': '突破上限',
                'threshold': warn_up,
                'message': f'🚨 {name} 突破预警线 ${warn_up:.2f}，当前 ${price:.2f} ({change_pct:+.2f}%)'
            }
            alerts.append(alert)
            print(f'  🚨 突破上限预警！阈值：${warn_up:.2f}')
        
        elif warn_down and price <= warn_down:
            alert = {
                'code': code,
                'name': name,
                'price': price,
                'change_pct': change_pct,
                'type': '跌破下限',
                'threshold': warn_down,
                'message': f'⚠️ {name} 跌破预警线 ${warn_down:.2f}，当前 ${price:.2f} ({change_pct:+.2f}%)'
            }
            alerts.append(alert)
            print(f'  ⚠️ 跌破下限预警！阈值：${warn_down:.2f}')
    
    print()
    print('='*80)
    
    if alerts:
        print(f'🚨 触发 {len(alerts)} 个预警！')
        print()
        for alert in alerts:
            print(alert['message'])
    else:
        print('✅ 无预警触发，所有股票正常')
    
    print('='*80)
    
    return alerts


def send_feishu_alert(alerts):
    """发送飞书预警"""
    if not alerts:
        return
    
    try:
        # 构建预警消息
        message = '🔔 价格预警通知\n\n'
        for alert in alerts:
            message += f'{alert["message"]}\n'
        
        message += f'\n监控时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # 发送飞书消息
        from message import send_message
        send_message(
            channel='feishu',
            target='ou_636c8e8b7ad36d7fc28e6cf90c350fdd',
            message=message
        )
        
        print('✅ 飞书预警已发送')
    
    except Exception as e:
        print(f'⚠️ 发送飞书失败：{e}')


if __name__ == '__main__':
    # 检查预警
    alerts = check_alerts()
    
    # 发送预警
    if alerts:
        send_feishu_alert(alerts)
