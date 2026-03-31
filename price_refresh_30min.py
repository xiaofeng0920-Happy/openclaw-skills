#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锋哥持仓价格 30 分钟刷新
交易时间每 30 分钟发送一次价格行情
数据源：富途 OpenD
"""

import json
import subprocess
from datetime import datetime
from futu import *

# ============ 配置 ============
CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"
# =============================

def load_portfolio():
    """加载持仓配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_holdings(portfolio):
    """从配置中提取持仓列表"""
    holdings_hk = []
    holdings_us = []
    
    accounts = portfolio.get('accounts', {})
    
    # 提取港股
    hk_account = accounts.get('hk_stocks', {})
    for h in hk_account.get('holdings', []):
        symbol = h.get('symbol', '')
        if symbol:
            holdings_hk.append({
                'symbol': symbol.replace('.HK', ''),  # 去掉.HK 后缀
                'name': h.get('name', ''),
                'shares': h.get('shares', 0)
            })
    
    # 提取美股
    us_account = accounts.get('us_stocks', {})
    for h in us_account.get('holdings', []):
        symbol = h.get('symbol', '')
        if symbol:
            holdings_us.append({
                'symbol': symbol,
                'name': h.get('name', ''),
                'shares': h.get('shares', 0)
            })
    
    return holdings_hk, holdings_us

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

def get_hk_prices(quote_ctx, symbols):
    """获取港股实时价格"""
    prices = {}
    try:
        codes = [f"HK.{symbol}" for symbol in symbols]
        ret, data = quote_ctx.get_market_snapshot(codes)
        if ret == RET_OK:
            for i, code in enumerate(codes):
                symbol = code.split('.')[1]
                row = data.iloc[i]
                last_price = float(row['last_price']) if row['last_price'] != 'N/A' else 0
                prev_close = float(row['prev_close_price']) if row['prev_close_price'] != 'N/A' else 0
                high = float(row['high_price']) if row['high_price'] != 'N/A' else 0
                low = float(row['low_price']) if row['low_price'] != 'N/A' else 0
                
                # 计算涨跌幅
                change_pct = ((last_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                
                prices[symbol] = {
                    'price': last_price,
                    'change_pct': change_pct,
                    'high': high,
                    'low': low,
                    'volume': int(row['volume']) if row['volume'] != 'N/A' else 0
                }
    except Exception as e:
        print(f"获取港股价格失败：{e}")
    return prices

def get_us_prices(quote_ctx, symbols):
    """获取美股实时价格"""
    prices = {}
    try:
        codes = [f"US.{symbol}" for symbol in symbols]
        ret, data = quote_ctx.get_market_snapshot(codes)
        if ret == RET_OK:
            for i, code in enumerate(codes):
                symbol = code.split('.')[1]
                row = data.iloc[i]
                last_price = float(row['last_price']) if row['last_price'] != 'N/A' else 0
                prev_close = float(row['prev_close_price']) if row['prev_close_price'] != 'N/A' else 0
                high = float(row['high_price']) if row['high_price'] != 'N/A' else 0
                low = float(row['low_price']) if row['low_price'] != 'N/A' else 0
                
                # 计算涨跌幅
                change_pct = ((last_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
                
                prices[symbol] = {
                    'price': last_price,
                    'change_pct': change_pct,
                    'high': high,
                    'low': low,
                    'volume': int(row['volume']) if row['volume'] != 'N/A' else 0
                }
    except Exception as e:
        print(f"获取美股价格失败：{e}")
    return prices

def generate_report(hk_prices, us_prices, holdings_hk, holdings_us):
    """生成价格刷新报告"""
    now = datetime.now()
    time_str = now.strftime('%Y-%m-%d %H:%M')
    
    report = []
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append(f"📊 锋哥持仓 - 价格刷新")
    report.append(f"🕐 {time_str}")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("")
    
    # 港股部分
    if hk_prices:
        report.append("## 🇭🇰 港股持仓")
        report.append("")
        report.append("| 股票 | 名称 | 现价 | 涨跌 | 日内波幅 |")
        report.append("|------|------|------|------|----------|")
        
        for holding in holdings_hk:
            symbol = holding['symbol']
            name = holding.get('name', '')
            if symbol in hk_prices:
                p = hk_prices[symbol]
                change_icon = "📈" if p['change_pct'] > 0 else ("📉" if p['change_pct'] < 0 else "➡️")
                report.append(f"| {symbol} | {name} | {p['price']:.2f} | {change_icon} {p['change_pct']:+.2f}% | {p['low']:.2f}~{p['high']:.2f} |")
        
        report.append("")
    
    # 美股部分
    if us_prices:
        report.append("## 🇺🇸 美股持仓")
        report.append("")
        report.append("| 股票 | 名称 | 现价 | 涨跌 | 日内波幅 |")
        report.append("|------|------|------|------|----------|")
        
        for holding in holdings_us:
            symbol = holding['symbol']
            name = holding.get('name', '')
            if symbol in us_prices:
                p = us_prices[symbol]
                change_icon = "📈" if p['change_pct'] > 0 else ("📉" if p['change_pct'] < 0 else "➡️")
                report.append(f"| {symbol} | {name} | ${p['price']:.2f} | {change_icon} {p['change_pct']:+.2f}% | ${p['low']:.2f}~${p['high']:.2f} |")
        
        report.append("")
    
    # 重点提醒
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("## ⚡ 重点监控")
    report.append("")
    
    # 找出涨跌幅最大的
    all_changes = []
    for symbol, p in hk_prices.items():
        all_changes.append((symbol, p['change_pct'], 'HK'))
    for symbol, p in us_prices.items():
        all_changes.append((symbol, p['change_pct'], 'US'))
    
    if all_changes:
        all_changes.sort(key=lambda x: abs(x[1]), reverse=True)
        top = all_changes[:3]
        for symbol, change, market in top:
            icon = "🚀" if change > 2 else ("📉" if change < -2 else "👀")
            report.append(f"{icon} {symbol} ({market}): {change:+.2f}%")
    
    report.append("")
    report.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    report.append("*数据来自富途 OpenD | 30 分钟刷新*")
    
    return "\n".join(report)

def send_to_feishu(message):
    """发送到飞书"""
    try:
        cmd = [
            'openclaw', 'message', 'send',
            '--channel', 'feishu',
            '--target', FEISHU_USER_ID,
            '--message', message
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ 消息已发送到飞书")
            return True
        else:
            print(f"⚠️  发送失败：{result.stderr}")
            return False
    except Exception as e:
        print(f"⚠️  发送异常：{e}")
        return False

def main():
    """主函数"""
    print(f"🕐 开始 30 分钟价格刷新 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 检查是否在交易时间
    if not is_hk_trading_hour():
        print("⏰ 非交易时间，跳过")
        return
    
    # 加载配置
    portfolio = load_portfolio()
    print(f"✅ 加载持仓配置：{portfolio.get('portfolio_name', 'Unknown')}")
    
    # 提取持仓列表
    holdings_hk, holdings_us = extract_holdings(portfolio)
    print(f"📋 持仓：{len(holdings_hk)} 只港股 + {len(holdings_us)} 只美股")
    
    # 初始化富途报价上下文
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    try:
        # 获取港股代码
        hk_symbols = [h['symbol'] for h in holdings_hk]
        us_symbols = [h['symbol'] for h in holdings_us]
        
        print(f"📈 获取 {len(hk_symbols)} 只港股 + {len(us_symbols)} 只美股价格...")
        
        # 获取价格
        hk_prices = get_hk_prices(quote_ctx, hk_symbols)
        us_prices = get_us_prices(quote_ctx, us_symbols)
        
        if len(us_prices) == 0 and len(us_symbols) > 0:
            print("⚠️  美股行情权限未开通，只显示港股数据")
        
        print(f"✅ 获取成功：港股 {len(hk_prices)} 只，美股 {len(us_prices)} 只")
        
        # 生成报告
        report = generate_report(hk_prices, us_prices, holdings_hk, holdings_us)
        print("✅ 报告生成完成")
        
        # 发送到飞书
        print("")
        print("📤 发送到飞书...")
        send_to_feishu(report)
        
    except Exception as e:
        print(f"❌ 执行失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        quote_ctx.close()
    
    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("预览报告:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if 'report' in locals():
        print(report)

if __name__ == '__main__':
    main()
