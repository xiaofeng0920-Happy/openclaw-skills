#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小巴 - 锋哥持仓日报生成器
读取真实持仓配置，生成每日持仓报告 + 市场分析
"""

import json
import sys
import os
from datetime import datetime, timedelta
import subprocess
import urllib.request
import ssl

# 忽略 SSL 证书验证（用于 API 调用）
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# 配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config', 'feng_portfolio.json')
REPORTS_DIR = os.path.join(SCRIPT_DIR, 'reports')
FINNHUB_API_KEY_FILE = os.path.expanduser('~/.openclaw/workspace/config/finnhub_api_key.txt')
TWELVEDATA_API_KEY_FILE = os.path.expanduser('~/.openclaw/workspace/config/twelvedata_api_key.txt')

def load_config():
    """加载持仓配置"""
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 配置文件不存在：{CONFIG_FILE}")
        sys.exit(1)
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_finnhub_key():
    """加载 Finnhub API Key"""
    if os.path.exists(FINNHUB_API_KEY_FILE):
        with open(FINNHUB_API_KEY_FILE, 'r') as f:
            return f.read().strip()
    return None

def load_twelvedata_key():
    """加载 TwelveData API Key"""
    if os.path.exists(TWELVEDATA_API_KEY_FILE):
        with open(TWELVEDATA_API_KEY_FILE, 'r') as f:
            return f.read().strip()
    return None

def get_stock_price(symbol, finnhub_key=None, twelvedata_key=None):
    """获取股票实时价格（优先 TwelveData，备选 Finnhub）"""
    
    # 尝试 TwelveData（支持全球市场）
    if twelvedata_key:
        try:
            # TwelveData 符号格式：美股直接，港股加.HK
            td_symbol = symbol if not symbol.endswith('.HK') else symbol
            url = f"https://api.twelvedata.com/quote?symbol={td_symbol}&apikey={twelvedata_key}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                if data.get('price'):
                    current = float(data['price'])
                    change_pct = float(data.get('change_percent', 0).replace('%', ''))
                    return current, change_pct
        except Exception as e:
            pass
    
    # 备选 Finnhub（主要美股）
    if finnhub_key:
        try:
            finnhub_symbol = symbol
            url = f"https://finnhub.io/api/v1/quote?symbol={finnhub_symbol}&token={finnhub_key}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                if data.get('c'):
                    current = data['c']
                    change_pct = data.get('dp', 0)
                    return current, change_pct
        except Exception as e:
            pass
    
    return None, None

def get_hk_stock_price(symbol, finnhub_key=None, twelvedata_key=None):
    """获取港股价格（优先 TwelveData，备选 Yahoo Finance）"""
    # 优先使用 TwelveData（支持港股）
    current, change_pct = get_stock_price(symbol, finnhub_key, twelvedata_key)
    if current:
        return current, change_pct
    
    # 备选 Yahoo Finance
    try:
        yahoo_symbol = symbol.replace('.HK', '') + '.HK'
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get('chart', {}).get('result'):
                result = data['chart']['result'][0]
                current = result['meta'].get('regularMarketPrice', 0)
                change_pct = result['meta'].get('regularMarketChangePercent', 0)
                return current, change_pct
    except:
        pass
    return None, None

def generate_report(config):
    """生成持仓日报"""
    today = datetime.now().strftime('%Y-%m-%d')
    report_time = datetime.now().strftime('%H:%M:%S')
    
    finnhub_key = load_finnhub_key()
    twelvedata_key = load_twelvedata_key()
    
    print(f"✅ Finnhub API: {'已加载' if finnhub_key else '未配置'}")
    print(f"✅ TwelveData API: {'已加载' if twelvedata_key else '未配置'}")
    print("ℹ️  注：港股价格延迟（非交易时间），美股为实时数据")
    
    # 报告头部
    report = []
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append(f"📊 锋哥持仓日报 | {today} {report_time}")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("")
    
    # 总体概览
    report.append("## 📈 总体概览")
    report.append("")
    total_value = config['total_value_usd']
    total_pnl = config['total_pnl_usd']
    total_pnl_pct = config['total_pnl_percent']
    
    report.append(f"**总持仓**: ${total_value:,}")
    report.append(f"**总盈亏**: {'+' if total_pnl > 0 else ''}${total_pnl:,} ({total_pnl_pct}%)")
    report.append(f"**上次更新**: {config['last_updated']}")
    report.append("")
    
    # 账户明细
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("## 🏦 账户表现")
    report.append("")
    
    accounts = config['accounts']
    
    # 美股账户
    us = accounts['us_stocks']
    report.append(f"### 🇺🇸 {us['name']}")
    report.append(f"**市值**: ${us['value_usd']:,} | **盈亏**: {us['pnl_usd']:+,.0f} ({us['pnl_percent']}%) | **状态**: {us['status']}")
    report.append("")
    report.append("| 股票 | 持仓 | 成本 | 现价 | 盈亏% | 状态 |")
    report.append("|------|------|------|------|-------|------|")
    
    for holding in us['holdings']:
        symbol = holding['symbol']
        shares = holding['shares']
        cost = holding['avg_cost_usd']
        current, change_pct = get_stock_price(symbol, finnhub_key, twelvedata_key)
        
        if current:
            current_str = f"${current:.2f}"
            pnl_pct = holding['pnl_percent']
        else:
            current_str = "N/A"
            pnl_pct = holding['pnl_percent']
        
        status_icon = "✅" if holding['status'] == '盈利' else ("❌" if '亏损' in holding['status'] else "➖")
        report.append(f"| {symbol} | {shares} | ${cost:.2f} | {current_str} | {pnl_pct:+.1f}% | {status_icon} {holding['status']} |")
    
    report.append("")
    
    # 港股账户
    hk = accounts['hk_stocks']
    report.append(f"### 🇭🇰 {hk['name']}")
    report.append(f"**市值**: ${hk['value_usd']:,} | **盈亏**: {hk['pnl_usd']:+,.0f} ({hk['pnl_percent']}%) | **状态**: {hk['status']}")
    report.append("")
    report.append("| 股票 | 持仓 | 成本 (HKD) | 现价 (HKD) | 盈亏% | 状态 |")
    report.append("|------|------|------------|-----------|-------|------|")
    
    for holding in hk['holdings'][:6]:  # 只显示前 6 只
        symbol = holding['symbol']
        shares = holding['shares']
        cost = holding['avg_cost_hkd']
        current, change_pct = get_hk_stock_price(symbol, finnhub_key, twelvedata_key)
        
        if current:
            current_str = f"${current:.2f}"
        else:
            current_str = "N/A"
        
        status_icon = "✅" if holding['status'] == '盈利' else ("❌" if '亏损' in holding['status'] else "➖")
        report.append(f"| {symbol} | {shares} | ${cost:.2f} | {current_str} | {holding['pnl_percent']:+.1f}% | {status_icon} {holding['status']} |")
    
    report.append("")
    
    # 期权亮点
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("## 📋 期权策略")
    report.append("")
    
    # 美股期权
    report.append("### 美股期权")
    for opt in config['options']['us_options'][:3]:
        status_icon = "✅" if opt['pnl_usd'] > 0 else "❌"
        report.append(f"- {opt['symbol']} {opt['type']} {opt['expiry']} ${opt['strike']}: {opt['pnl_usd']:+,.0f} USD {status_icon}")
    report.append("")
    
    # 港股期权亮点
    report.append("### 港股期权亮点")
    for opt in config['options']['hk_options']:
        if opt['pnl_percent'] > 50:  # 只显示大赚的
            report.append(f"- ✅ {opt['symbol']} {opt['type']}: **+{opt['pnl_percent']}%** ({opt['pnl_hkd']:+,.0f} HKD)")
    report.append("")
    
    # 待办事项
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("## ⚠️ 今日待办")
    report.append("")
    
    for item in config['action_items']:
        priority_icon = "🔴" if item['priority'] <= 3 else ("🟡" if item['priority'] <= 5 else "🟢")
        report.append(f"{priority_icon} **P{item['priority']}** {item['action']}: {item['target']}")
        report.append(f"   → {item['suggestion']}")
        report.append("")
    
    # 市场亮点
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("## 💡 持仓亮点")
    report.append("")
    
    for highlight in config['highlights']:
        report.append(highlight)
    
    report.append("")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("")
    report.append('*小巴 - "在华尔街，犹豫是昂贵的，果断是赚钱的。"*')
    
    return "\n".join(report)

def save_report(report, date):
    """保存报告到文件"""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filename = os.path.join(REPORTS_DIR, f"feng-daily-{date}.md")
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return filename

def send_to_feishu(report):
    """发送到飞书"""
    try:
        # 使用 openclaw message 工具发送
        cmd = [
            'openclaw', 'message', 'send',
            '--channel', 'feishu',
            '--target', 'ou_636c8e8b7ad36d7fc28e6cf90c350fdd',
            '--message', report
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ 报告已发送到飞书")
            return True
        else:
            print(f"⚠️  发送失败：{result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️  发送异常：{e}")
        return False

def main():
    """主函数"""
    print("📊 生成锋哥持仓日报...")
    print("")
    
    # 检查是否是交易日
    today = datetime.now()
    weekday = today.weekday()  # 0=Monday, 6=Sunday
    
    if '--force' not in sys.argv and weekday >= 5:
        print("⚠️  非交易日，跳过报告生成")
        sys.exit(0)
    
    # 加载配置
    config = load_config()
    print(f"✅ 加载持仓配置：{config['portfolio_name']}")
    
    # 生成报告
    report = generate_report(config)
    print("✅ 报告生成完成")
    
    # 保存报告
    today_str = today.strftime('%Y-%m-%d')
    filename = save_report(report, today_str)
    print(f"✅ 报告已保存：{filename}")
    
    # 发送到飞书
    print("")
    print("📤 发送到飞书...")
    send_to_feishu(report)
    
    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("预览报告:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(report)

if __name__ == '__main__':
    main()
