#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化组合监控脚本 - 每周跟踪表现

作者：小巴
日期：2026-03-26
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from futu import *
except ImportError:
    print("❌ 未安装 futu-api，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "futu-api", "-q"])
    from futu import *

# ============ 配置 ============
OPEND_HOST = '127.0.0.1'
OPEND_PORT = 11111
PORTFOLIO_FILE = '/Users/zhaoxf/.openclaw/workspace/agents/stock-system/reports/portfolio_HK_20260326.csv'
MONITOR_FILE = '/Users/zhaoxf/.openclaw/workspace/agents/stock-system/reports/portfolio_monitoring.json'

# ============================


def connect_opend() -> OpenQuoteContext:
    """连接 OpenD"""
    quote_ctx = OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    ret, state = quote_ctx.get_global_state()
    
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！")
        return None
    
    print("✅ OpenD 连接成功")
    return quote_ctx


def load_portfolio() -> pd.DataFrame:
    """加载组合权重"""
    if not Path(PORTFOLIO_FILE).exists():
        print(f"❌ 组合文件不存在：{PORTFOLIO_FILE}")
        return pd.DataFrame()
    
    df = pd.read_csv(PORTFOLIO_FILE)
    print(f"✅ 加载组合：{len(df)} 只股票")
    return df


def load_monitoring_history() -> list:
    """加载历史监控记录"""
    if not Path(MONITOR_FILE).exists():
        return []
    
    with open(MONITOR_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('history', [])


def get_current_prices(quote_ctx: OpenQuoteContext, codes: list) -> dict:
    """获取当前价格"""
    prices = {}
    
    for code in codes:
        ret, data = quote_ctx.get_market_snapshot(code)
        if ret == RET_OK and len(data) > 0:
            prices[code] = float(data['last_price'].iloc[0])
        else:
            prices[code] = None
    
    return prices


def calculate_performance(portfolio: pd.DataFrame, current_prices: dict) -> dict:
    """计算组合表现"""
    
    total_value = 0
    total_cost = 0
    positions = []
    
    for _, row in portfolio.iterrows():
        code = row['code']
        weight = row['weight']
        entry_price = row['last_price']
        quantity = row.get('quantity', 0)
        
        current_price = current_prices.get(code)
        
        if current_price is None:
            continue
        
        # 计算持仓价值
        if quantity > 0:
            cost = entry_price * quantity
            value = current_price * quantity
            pnl = value - cost
            pnl_pct = (pnl / cost) * 100 if cost > 0 else 0
        else:
            # 假设建仓
            cost = 1000000 * weight  # 假设 100 万总资金
            value = cost * (current_price / entry_price)
            pnl = value - cost
            pnl_pct = ((current_price - entry_price) / entry_price) * 100
        
        total_value += value
        total_cost += cost
        
        positions.append({
            'code': code,
            'name': row['name'],
            'entry_price': entry_price,
            'current_price': current_price,
            'weight': weight,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
    
    # 组合总体表现
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
    
    return {
        'positions': positions,
        'total_value': total_value,
        'total_cost': total_cost,
        'total_pnl': total_pnl,
        'total_pnl_pct': total_pnl_pct
    }


def generate_monitoring_report(performance: dict, history: list) -> str:
    """生成监控报告"""
    
    report = f"""# 📊 量化组合监控报告

**日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**策略**: 量价 60% + 价值 40%

---

## 📈 组合总体表现

| 指标 | 数值 |
|------|------|
| **总市值** | ${performance['total_value']:,.0f} |
| **总成本** | ${performance['total_cost']:,.0f} |
| **总盈亏** | ${performance['total_pnl']:,.0f} |
| **收益率** | {performance['total_pnl_pct']:+.2f}% |

---

## 💼 个股表现

| 代码 | 名称 | 建仓价 | 现价 | 盈亏 | 收益率 | 权重 |
|------|------|--------|------|------|--------|--------|
"""
    
    # 按收益率排序
    positions = sorted(performance['positions'], key=lambda x: x['pnl_pct'], reverse=True)
    
    for pos in positions:
        report += f"| {pos['code']} | {pos['name']} | ${pos['entry_price']:.2f} | ${pos['current_price']:.2f} | ${pos['pnl']:+,.0f} | {pos['pnl_pct']:+.2f}% | {pos['weight']*100:.1f}% |\n"
    
    # 历史表现
    if history:
        report += f"""
---

## 📅 历史表现

| 日期 | 收益率 | 备注 |
|------|--------|------|
"""
        for record in history[-10:]:  # 最近 10 次
            report += f"| {record['date']} | {record['total_pnl_pct']:+.2f}% | {record.get('note', '')} |\n"
    
    report += f"""
---

## ⚠️ 预警信息

"""
    
    # 检查止损/止盈
    alerts = []
    for pos in positions:
        if pos['pnl_pct'] <= -10:
            alerts.append(f"🔴 **{pos['code']}** 触发止损线（-{abs(pos['pnl_pct']):.2f}%）")
        elif pos['pnl_pct'] >= 20:
            alerts.append(f"🟢 **{pos['code']}** 触发止盈线（+{pos['pnl_pct']:.2f}%）")
    
    if alerts:
        report += "\n".join(alerts)
    else:
        report += "✅ 无预警，所有持仓正常"
    
    report += f"""

---

## 📝 操作建议

"""
    
    # 再平衡建议
    if len(history) > 0:
        days_since_start = (datetime.now() - datetime.fromisoformat(history[0]['date'])).days
        if days_since_start >= 90:  # 季度再平衡
            report += "⚠️ **建议进行季度再平衡**（距离上次再平衡已超过 90 天）\n"
    
    # 行业集中度
    insurance_weight = sum(p['weight'] for p in positions if '保险' in p['name'] or '保险' in p['code'])
    if insurance_weight > 0.35:
        report += f"⚠️ **保险行业集中度过高**（{insurance_weight*100:.1f}%），建议降低到 30% 以下\n"
    
    report += f"""
---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report


def save_monitoring_data(performance: dict, history: list):
    """保存监控数据"""
    
    # 添加新记录
    new_record = {
        'date': datetime.now().isoformat(),
        'total_value': performance['total_value'],
        'total_cost': performance['total_cost'],
        'total_pnl': performance['total_pnl'],
        'total_pnl_pct': performance['total_pnl_pct'],
        'positions': performance['positions']
    }
    
    history.append(new_record)
    
    # 保存（保留最近 52 周记录）
    with open(MONITOR_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'last_updated': datetime.now().isoformat(),
            'history': history[-52:]  # 保留 1 年数据
        }, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"📊 量化组合监控系统")
    print(f"{'='*60}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # 连接 OpenD
    quote_ctx = connect_opend()
    if quote_ctx is None:
        return
    
    try:
        # 加载组合
        portfolio = load_portfolio()
        if portfolio.empty:
            return
        
        # 加载历史记录
        history = load_monitoring_history()
        print(f"✅ 加载历史记录：{len(history)} 条")
        
        # 获取当前价格
        print("\n正在获取当前价格...")
        codes = portfolio['code'].tolist()
        current_prices = get_current_prices(quote_ctx, codes)
        print(f"✅ 获取价格完成")
        
        # 计算表现
        print("\n正在计算组合表现...")
        performance = calculate_performance(portfolio, current_prices)
        
        # 生成报告
        report = generate_monitoring_report(performance, history)
        
        # 保存报告
        report_file = f'/Users/zhaoxf/.openclaw/workspace/agents/stock-system/reports/monitoring_{datetime.now().strftime("%Y%m%d")}.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n✅ 监控报告已保存到：{report_file}")
        
        # 保存数据
        save_monitoring_data(performance, history)
        print(f"✅ 监控数据已保存到：{MONITOR_FILE}")
        
        # 显示摘要
        print(f"\n{'='*60}")
        print(f"📊 组合表现摘要")
        print(f"{'='*60}")
        print(f"总市值：${performance['total_value']:,.0f}")
        print(f"总成本：${performance['total_cost']:,.0f}")
        print(f"总盈亏：${performance['total_pnl']:,.0f}")
        print(f"收益率：{performance['total_pnl_pct']:+.2f}%")
        print(f"{'='*60}")
    
    finally:
        quote_ctx.close()


if __name__ == "__main__":
    main()
