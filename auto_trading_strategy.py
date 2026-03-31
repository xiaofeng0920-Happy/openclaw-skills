#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锋哥自动交易策略 - 富途 OpenAPI 版本
根据持仓配置自动执行止损止盈、条件单
数据源：富途 OpenD (本地)

⚠️ 安全提示：
1. 首次运行建议用模拟盘测试
2. 交易解锁必须在 OpenD GUI 界面手动操作
3. 建议先 dry-run 模式验证逻辑
"""

import json
import sys
from datetime import datetime
from futu import *

# ============ 配置 ============
CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
STRATEGY_CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/config/trading_strategy_config.json"
FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"
DRY_RUN = True  # 首次运行用模拟模式，不实际下单
# =============================

def load_portfolio():
    """加载持仓配置"""
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_strategy_config():
    """加载策略配置"""
    try:
        with open(STRATEGY_CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "stop_loss_percent": -10.0,  # 止损阈值：-10%
            "take_profit_percent": 20.0,  # 止盈阈值：+20%
            "enabled": True,
            "last_execution": None
        }

def save_strategy_config(config):
    """保存策略配置"""
    import os
    os.makedirs(os.path.dirname(STRATEGY_CONFIG_FILE), exist_ok=True)
    with open(STRATEGY_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def check_stop_loss_take_profit(holding, current_price, is_hkd=False):
    """检查止损止盈条件"""
    config = load_strategy_config()
    
    avg_cost = holding['avg_cost_hkd'] if is_hkd else holding['avg_cost_usd']
    change_pct = ((current_price - avg_cost) / avg_cost) * 100 if avg_cost > 0 else 0
    
    actions = []
    
    # 止损检查
    if change_pct <= config['stop_loss_percent']:
        actions.append({
            "type": "🛑 止损",
            "symbol": holding['symbol'],
            "action": "SELL",
            "reason": f"跌幅 {change_pct:.1f}% ≤ {config['stop_loss_percent']}%",
            "current_price": current_price,
            "avg_cost": avg_cost,
            "shares": holding['shares'],
            "estimated_loss": (current_price - avg_cost) * holding['shares']
        })
    
    # 止盈检查
    elif change_pct >= config['take_profit_percent']:
        actions.append({
            "type": "✅ 止盈",
            "symbol": holding['symbol'],
            "action": "SELL",
            "reason": f"涨幅 {change_pct:.1f}% ≥ {config['take_profit_percent']}%",
            "current_price": current_price,
            "avg_cost": avg_cost,
            "shares": holding['shares'],
            "estimated_profit": (current_price - avg_cost) * holding['shares']
        })
    
    return actions

def check_action_items(portfolio, current_prices):
    """检查配置中的行动项"""
    actions = []
    
    for item in portfolio.get('action_items', []):
        target = item.get('target', '')
        action = item.get('action', '')
        priority = item.get('priority', 99)
        
        # 解析目标
        if 'AAPL CALL' in target and '止损' in action:
            actions.append({
                "type": "⚡ 立即执行",
                "symbol": "AAPL_CALL_285",
                "action": "SELL_OPTION",
                "reason": item.get('suggestion', ''),
                "priority": priority,
                "estimated_pnl": item.get('pnl_usd', 0)
            })
        elif 'NVDA CALL' in target and '止损' in action:
            actions.append({
                "type": "⚡ 立即执行",
                "symbol": "NVDA_CALL_220",
                "action": "SELL_OPTION",
                "reason": item.get('suggestion', ''),
                "priority": priority,
                "estimated_pnl": item.get('pnl_usd', 0)
            })
        elif 'MSFT 减仓' in target:
            actions.append({
                "type": "📅 本周执行",
                "symbol": "MSFT",
                "action": "SELL_PARTIAL",
                "reason": item.get('suggestion', ''),
                "priority": priority,
                "sell_percent": 50
            })
    
    # 按优先级排序
    actions.sort(key=lambda x: x['priority'])
    
    return actions

def execute_order(trd_ctx, action, dry_run=True):
    """执行订单"""
    symbol = action['symbol']
    order_action = action['action']
    
    if dry_run:
        print(f"  [DRY RUN] {action['type']} {symbol}: {order_action}")
        print(f"    原因：{action['reason']}")
        if 'estimated_profit' in action:
            print(f"    预计盈利：${action['estimated_profit']:,.0f}")
        elif 'estimated_loss' in action:
            print(f"    预计亏损：${action['estimated_loss']:,.0f}")
        return True
    
    # 实际下单逻辑（需要解锁交易）
    # 这里需要根据富途 API 的具体接口实现
    print(f"  执行 {action['type']} {symbol}: {order_action}")
    return True

def send_feishu_report(actions, executed_count):
    """发送执行报告到飞书"""
    import subprocess
    
    if not actions:
        return
    
    message_lines = ["🤖 自动交易策略执行报告", f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    message_lines.append(f"✅ 已执行 {executed_count} 笔交易")
    message_lines.append("")
    
    for action in actions[:5]:  # 最多显示 5 条
        message_lines.append(f"{action['type']} {action['symbol']}")
        message_lines.append(f"  操作：{action['action']}")
        message_lines.append(f"  原因：{action['reason']}")
        message_lines.append("")
    
    if DRY_RUN:
        message_lines.append("⚠️ 当前为模拟模式 (DRY_RUN)，未实际下单")
    
    message = "\n".join(message_lines)
    
    cmd = [
        "openclaw", "message", "send",
        "--channel", "feishu",
        "--target", FEISHU_USER_ID,
        "--message", message
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ 执行报告已发送")
    except Exception as e:
        print(f"❌ 发送报告失败：{e}")

def run_strategy():
    """运行交易策略"""
    print(f"[{datetime.now()}] 开始运行自动交易策略...")
    
    # 连接 OpenD
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    trd_ctx = OpenHKTradeContext(host='127.0.0.1', port=11111)  # 港股交易
    
    # 验证连接
    ret, state = quote_ctx.get_global_state()
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！")
        return
    
    print("✅ OpenD 连接成功")
    
    # 加载配置
    portfolio = load_portfolio()
    strategy_config = load_strategy_config()
    
    if not strategy_config.get('enabled', True):
        print("⚠️ 策略已禁用，跳过执行")
        return
    
    # 获取实时价格
    us_symbols = [h['symbol'] for h in portfolio['accounts']['us_stocks']['holdings']]
    hk_symbols = [h['symbol'].replace('.HK', '') for h in portfolio['accounts']['hk_stocks']['holdings']]
    
    current_prices = {}
    
    # 获取美股价格
    ret, data = quote_ctx.get_market_snapshot([f"US.{s}" for s in us_symbols])
    if ret == RET_OK:
        for i, symbol in enumerate(us_symbols):
            current_prices[symbol] = float(data['last_price'][i])
    
    # 获取港股价格
    ret, data = quote_ctx.get_market_snapshot([f"HK.{s}" for s in hk_symbols])
    if ret == RET_OK:
        for i, symbol in enumerate(hk_symbols):
            current_prices[symbol] = float(data['last_price'][i])
    
    print(f"获取到 {len(current_prices)} 只股票的实时价格")
    
    # 检查止损止盈
    all_actions = []
    
    for holding in portfolio['accounts']['us_stocks']['holdings']:
        symbol = holding['symbol']
        if symbol in current_prices:
            actions = check_stop_loss_take_profit(holding, current_prices[symbol], is_hkd=False)
            all_actions.extend(actions)
    
    for holding in portfolio['accounts']['hk_stocks']['holdings']:
        symbol = holding['symbol'].replace('.HK', '')
        if symbol in current_prices:
            actions = check_stop_loss_take_profit(holding, current_prices[symbol], is_hkd=True)
            all_actions.extend(actions)
    
    # 检查配置中的行动项
    action_items = check_action_items(portfolio, current_prices)
    all_actions.extend(action_items)
    
    print(f"发现 {len(all_actions)} 个交易机会")
    
    # 执行交易
    executed_count = 0
    for action in all_actions:
        if execute_order(trd_ctx, action, dry_run=DRY_RUN):
            executed_count += 1
    
    # 发送报告
    send_feishu_report(all_actions, executed_count)
    
    # 更新执行时间
    strategy_config['last_execution'] = datetime.now().isoformat()
    save_strategy_config(strategy_config)
    
    quote_ctx.close()
    trd_ctx.close()
    
    print(f"✅ 策略执行完成，共执行 {executed_count} 笔交易")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--live':
        DRY_RUN = False
        print("⚠️ 警告：即将进入实盘模式！按 Ctrl+C 取消...")
        import time
        time.sleep(5)
    
    if DRY_RUN:
        print("🔍 当前为模拟模式 (DRY_RUN)，不会实际下单")
    
    run_strategy()
