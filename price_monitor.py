#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锋哥股价实时监控 - 富途 OpenAPI 版本
监控持仓股票价格，突破阈值时发送飞书预警
数据源：富途 OpenD (本地)
"""

import json
import time
from datetime import datetime
from futu import *

def is_hk_trading_hour():
    """判断是否在港股交易时段"""
    now = datetime.now()
    weekday = now.weekday()
    
    if weekday >= 5:  # 周末
        return False
    
    hour = now.hour
    minute = now.minute
    
    # 港股：9:30-12:00, 13:00-16:00
    hk_morning = (9, 30) <= (hour, minute) < (12, 0)
    hk_afternoon = (13, 0) <= (hour, minute) < (16, 0)
    
    return hk_morning or hk_afternoon

# ============ 配置 ============
CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
ALERT_CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/config/price_alert_config.json"
FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"
CHECK_INTERVAL_SECONDS = 60  # 每分钟检查一次
# =============================

def load_alert_config():
    """加载预警配置"""
    try:
        with open(ALERT_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 默认配置
        return {
            "last_alert_time": {},
            "alert_cooldown_minutes": 60,  # 同一股票预警间隔 60 分钟
            "price_change_threshold": 5.0  # 涨跌幅超过 5% 预警
        }

def save_alert_config(config):
    """保存预警配置"""
    import os
    os.makedirs(os.path.dirname(ALERT_CONFIG_FILE), exist_ok=True)
    with open(ALERT_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_portfolio():
    """加载持仓配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_realtime_prices(quote_ctx, symbols, market):
    """批量获取实时价格"""
    prices = {}
    try:
        codes = []
        for symbol in symbols:
            if market == 'US':
                codes.append(f"US.{symbol}")
            else:
                codes.append(f"HK.{symbol}")
        
        ret, data = quote_ctx.get_market_snapshot(codes)
        if ret == RET_OK:
            for i, code in enumerate(codes):
                symbol = code.split('.')[1]
                prices[symbol] = float(data['last_price'][i])
    except Exception as e:
        print(f"获取价格失败：{e}")
    
    return prices

def check_price_alerts(symbol, current_price, prev_close, shares, name, cost_pnl, last_alert_time, config, is_hkd=False):
    """检查价格预警（基于当日涨跌幅）"""
    alerts = []
    currency = "HKD" if is_hkd else "USD"
    
    # 计算当日涨跌幅
    if prev_close > 0:
        today_change = ((current_price - prev_close) / prev_close) * 100
    else:
        today_change = 0
    
    # 计算金额变化
    change_value = (current_price - prev_close) * shares if prev_close > 0 else 0
    
    # 检查是否超过预警阈值
    threshold = config.get('price_change_threshold', 5.0)
    cooldown = config.get('alert_cooldown_minutes', 60)
    
    # 检查冷却时间
    last_time = last_alert_time.get(symbol)
    if last_time:
        elapsed = (datetime.now().timestamp() - last_time) / 60
        if elapsed < cooldown:
            return alerts  # 还在冷却期内
    
    # 大涨预警
    if today_change >= threshold:
        alerts.append({
            "type": "🟢",
            "symbol": symbol,
            "name": name,
            "price": current_price,
            "today_change": today_change,
            "change_value": change_value,
            "cost_pnl": cost_pnl,
            "currency": currency,
            "fire": " 🔥" if today_change >= 5 else ""
        })
    
    # 大跌预警
    elif today_change <= -threshold:
        alerts.append({
            "type": "🔴",
            "symbol": symbol,
            "name": name,
            "price": current_price,
            "today_change": today_change,
            "change_value": change_value,
            "cost_pnl": cost_pnl,
            "currency": currency,
            "fire": ""
        })
    
    return alerts

def send_daily_summary(portfolio, quote_ctx):
    """发送盘后总结"""
    print("📊 发送盘后总结...")
    
    now = datetime.now()
    
    # 计算当日盈亏
    total_change_usd = 0
    total_change_hkd = 0
    highlights = []
    
    # 获取美股数据
    us_codes = [f"US.{h['symbol']}" for h in portfolio['accounts']['us_stocks']['holdings']]
    if us_codes:
        ret, data = quote_ctx.get_market_snapshot(us_codes)
        if ret == RET_OK:
            for i, code in enumerate(us_codes):
                symbol = code.split('.')[1]
                holding = next((h for h in portfolio['accounts']['us_stocks']['holdings'] if h['symbol'] == symbol), None)
                if holding:
                    last_price = float(data['last_price'][i])
                    prev_close = float(data['prev_close_price'][i]) if 'prev_close_price' in data.columns else last_price
                    change = ((last_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
                    change_value = (last_price - prev_close) * holding['shares']
                    total_change_usd += change_value
                    
                    if abs(change) >= 5:
                        emoji = '🟢' if change > 0 else '🔴'
                        highlights.append(f"{emoji} {holding['name']}: {change:+.1f}%")
    
    # 获取港股数据
    hk_codes = [f"HK.{h['symbol'].replace('.HK', '')}" for h in portfolio['accounts']['hk_stocks']['holdings']]
    if hk_codes:
        ret, data = quote_ctx.get_market_snapshot(hk_codes)
        if ret == RET_OK:
            for i, code in enumerate(hk_codes):
                symbol = code.split('.')[1] + ".HK"
                holding = next((h for h in portfolio['accounts']['hk_stocks']['holdings'] if h['symbol'] == symbol), None)
                if holding:
                    last_price = float(data['last_price'][i])
                    prev_close = float(data['prev_close_price'][i]) if 'prev_close_price' in data.columns else last_price
                    change = ((last_price - prev_close) / prev_close) * 100 if prev_close > 0 else 0
                    change_value = (last_price - prev_close) * holding['shares']
                    total_change_hkd += change_value
                    
                    if abs(change) >= 5:
                        emoji = '🟢' if change > 0 else '🔴'
                        highlights.append(f"{emoji} {holding['name']}: {change:+.1f}%")
    
    # 生成总结
    message_lines = ["📊 盘后总结", f"📅 {now.strftime('%Y-%m-%d')}", ""]
    message_lines.append(f"💰 今日盈亏：美股 ${total_change_usd:+,.0f} | 港股 HK${total_change_hkd:+,.0f}")
    message_lines.append("")
    
    if highlights:
        message_lines.append("✨ 涨跌幅超 5% 的股票")
        message_lines.extend(highlights)
        message_lines.append("")
    
    message_lines.append("🌙 港股已收盘，明日 9:30 继续监控")
    
    send_feishu("\n".join(message_lines))
    print("✅ 盘后总结已发送")

def send_feishu(message):
    """通用飞书发送函数"""
    import subprocess
    cmd = ["openclaw", "message", "send", "--channel", "feishu", "--target", FEISHU_USER_ID, "--message", message]
    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print(f"发送失败：{e}")
        return False

def send_feishu_alert(alerts):
    """发送飞书预警（新格式：股票名 + 当日涨跌幅 + 金额变化 + 成本盈亏）"""
    if not alerts:
        return
    
    import subprocess
    
    message_lines = ["🔍 股价异动", f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    
    for alert in alerts:
        currency = alert['currency']
        value_str = f"({currency}${alert['change_value']:+,.0f})"
        message_lines.append(f"{alert['type']} {alert['name']}({alert['symbol']}): 今日{alert['today_change']:+.1f}% {value_str} | 成本{alert['cost_pnl']:+.1f}%{alert['fire']}")
    
    message_lines.append("")
    message_lines.append("💡 说明：今日=当日涨跌幅 | 成本=持仓盈亏 | 金额=今日变化")
    
    message = "\n".join(message_lines)
    
    cmd = [
        "openclaw", "message", "send",
        "--channel", "feishu",
        "--target", FEISHU_USER_ID,
        "--message", message
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ 已发送 {len(alerts)} 条预警")
    except Exception as e:
        print(f"❌ 发送预警失败：{e}")

def monitor_prices():
    """主监控循环（仅交易时段监控股价）"""
    print(f"[{datetime.now()}] 开始监控股价...")
    
    # 连接 OpenD
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    # 验证连接
    ret, state = quote_ctx.get_global_state()
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！")
        return
    
    print("✅ OpenD 连接成功")
    
    # 加载配置
    portfolio = load_portfolio()
    alert_config = load_alert_config()
    
    # 获取所有持仓股票代码
    us_symbols = [h['symbol'] for h in portfolio['accounts']['us_stocks']['holdings']]
    hk_symbols = [h['symbol'].replace('.HK', '') for h in portfolio['accounts']['hk_stocks']['holdings']]
    
    print(f"监控 {len(hk_symbols)} 只港股")
    print("💡 提示：港股交易时段（9:30-16:00）监控股价，盘后发送总结")
    
    last_summary_date = None
    
    try:
        while True:
            now = datetime.now()
            hour = now.hour
            
            # 判断是否在港股交易时段
            is_trading = is_hk_trading_hour()
            
            # 非交易时段不监控股价
            if not is_trading:
                if is_hk_closed and last_summary_date != now.strftime('%Y-%m-%d'):
                    # 盘后总结（每天只发送一次）
                    send_daily_summary(portfolio, quote_ctx)
                    last_summary_date = now.strftime('%Y-%m-%d')
                time.sleep(CHECK_INTERVAL_SECONDS)
                continue
            
            all_alerts = []
            
            # 获取美股实时数据（包含昨收价）
            us_codes = [f"US.{s}" for s in us_symbols]
            if us_codes:
                ret, data = quote_ctx.get_market_snapshot(us_codes)
                if ret == RET_OK:
                    for i, code in enumerate(us_codes):
                        symbol = code.split('.')[1]
                        holding = next((h for h in portfolio['accounts']['us_stocks']['holdings'] if h['symbol'] == symbol), None)
                        if holding:
                            current_price = float(data['last_price'][i])
                            prev_close = float(data['prev_close_price'][i]) if 'prev_close_price' in data.columns else current_price
                            alerts = check_price_alerts(
                                symbol,
                                current_price,
                                prev_close,
                                holding['shares'],
                                holding.get('name', symbol),
                                holding['pnl_percent'],
                                alert_config['last_alert_time'],
                                alert_config,
                                is_hkd=False
                            )
                            all_alerts.extend(alerts)
            
            # 获取港股实时数据（包含昨收价）
            hk_codes = [f"HK.{s}" for s in hk_symbols]
            if hk_codes:
                ret, data = quote_ctx.get_market_snapshot(hk_codes)
                if ret == RET_OK:
                    for i, code in enumerate(hk_codes):
                        symbol = code.split('.')[1] + ".HK"
                        holding = next((h for h in portfolio['accounts']['hk_stocks']['holdings'] if h['symbol'] == symbol), None)
                        if holding:
                            current_price = float(data['last_price'][i])
                            prev_close = float(data['prev_close_price'][i]) if 'prev_close_price' in data.columns else current_price
                            alerts = check_price_alerts(
                                symbol,
                                current_price,
                                prev_close,
                                holding['shares'],
                                holding.get('name', symbol),
                                holding['pnl_percent'],
                                alert_config['last_alert_time'],
                                alert_config,
                                is_hkd=True
                            )
                            all_alerts.extend(alerts)
            
            # 发送预警
            if all_alerts:
                send_feishu_alert(all_alerts)
                
                # 更新预警时间
                for alert in all_alerts:
                    alert_config['last_alert_time'][alert['symbol']] = datetime.now().timestamp()
                save_alert_config(alert_config)
            
            # 等待下一次检查
            time.sleep(CHECK_INTERVAL_SECONDS)
    
    except KeyboardInterrupt:
        print("\n监控已停止")
    finally:
        quote_ctx.close()

if __name__ == "__main__":
    monitor_prices()
