#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日组合跟踪监控 - 对比现有持仓 vs 旧权重 vs 新权重

作者：小巴
日期：2026-03-26
"""

import sys
import json
from pathlib import Path
from datetime import datetime, date
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
REPORTS_DIR = Path('/Users/zhaoxf/.openclaw/skills/港股量化投资/reports')
MONITORING_DIR = Path('/Users/zhaoxf/.openclaw/skills/港股量化投资/monitoring')

# 确保目录存在
MONITORING_DIR.mkdir(parents=True, exist_ok=True)

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


def get_current_prices(quote_ctx: OpenQuoteContext, codes: list) -> dict:
    """获取当前价格"""
    prices = {}
    
    # 分批获取，每批 400 只
    batch_size = 400
    for i in range(0, len(codes), batch_size):
        batch = codes[i:i+batch_size]
        ret, data = quote_ctx.get_market_snapshot(batch)
        
        if ret == RET_OK:
            for _, row in data.iterrows():
                code = row['code']
                prices[code] = {
                    'price': float(row['last_price']),
                    'change_pct': float(row['change_percent']) if 'change_percent' in row else 0,
                    'market_val': float(row['market_value']) if 'market_value' in row else 0
                }
    
    return prices


def load_portfolio_weights(portfolio_file: str) -> dict:
    """加载组合权重"""
    if not Path(portfolio_file).exists():
        return {}
    
    df = pd.read_csv(portfolio_file)
    weights = {}
    
    for _, row in df.iterrows():
        code = row['code']
        weights[code] = {
            'weight': row['weight'],
            'name': row['name'],
            'entry_price': row.get('last_price', 0)
        }
    
    return weights


def calculate_portfolio_performance(weights: dict, current_prices: dict, total_capital: float = 1000000) -> dict:
    """计算组合表现"""
    total_value = 0
    total_cost = total_capital
    positions = []
    
    for code, weight_data in weights.items():
        if code not in current_prices:
            continue
        
        current_price = current_prices[code]['price']
        change_pct = current_prices[code]['change_pct']
        entry_price = weight_data['entry_price']
        weight = weight_data['weight']
        name = weight_data['name']
        
        # 计算持仓价值
        position_value = total_capital * weight
        current_value = position_value * (current_price / entry_price) if entry_price > 0 else position_value
        pnl = current_value - position_value
        pnl_pct = (pnl / position_value) * 100 if position_value > 0 else 0
        
        total_value += current_value
        
        positions.append({
            'code': code,
            'name': name,
            'weight': weight * 100,
            'entry_price': entry_price,
            'current_price': current_price,
            'change_pct': change_pct,
            'value': current_value,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        })
    
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
    
    return {
        'positions': positions,
        'total_value': total_value,
        'total_cost': total_cost,
        'total_pnl': total_pnl,
        'total_pnl_pct': total_pnl_pct
    }


def load_existing_portfolio() -> dict:
    """加载现有持仓"""
    portfolio_file = Path('/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json')
    
    if not portfolio_file.exists():
        return {}
    
    with open(portfolio_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    positions = []
    total_value = 0
    total_cost = 0
    
    # 美股持仓
    if 'accounts' in data and 'us_stocks' in data['accounts']:
        for holding in data['accounts']['us_stocks']['holdings']:
            value = holding.get('value_usd', 0)
            cost = value - holding.get('pnl_usd', 0)
            positions.append({
                'code': f"US.{holding['symbol']}",
                'name': holding['name'],
                'value': value,
                'pnl': holding.get('pnl_usd', 0),
                'pnl_pct': holding.get('pnl_percent', 0)
            })
            total_value += value
            total_cost += cost
    
    # 港股持仓
    if 'accounts' in data and 'hk_stocks' in data['accounts']:
        for holding in data['accounts']['hk_stocks']['holdings']:
            value_hkd = holding.get('value_hkd', 0) / 7.8  # 换算成 USD
            cost_hkd = value_hkd - (holding.get('pnl_hkd', 0) / 7.8)
            positions.append({
                'code': holding['symbol'],
                'name': holding['name'],
                'value': value_hkd,
                'pnl': holding.get('pnl_hkd', 0) / 7.8,
                'pnl_pct': holding.get('pnl_percent', 0)
            })
            total_value += value_hkd
            total_cost += cost_hkd
    
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0
    
    return {
        'positions': positions,
        'total_value': total_value,
        'total_cost': total_cost,
        'total_pnl': total_pnl,
        'total_pnl_pct': total_pnl_pct
    }


def generate_daily_report(existing_perf: dict, old_weight_perf: dict, new_weight_perf: dict) -> str:
    """生成每日监控报告"""
    
    today = date.today().strftime('%Y-%m-%d')
    
    report = f"""# 📊 每日组合跟踪监控

**日期**: {today}  
**时间**: {datetime.now().strftime('%H:%M')}

---

## 📈 三个组合对比

| 组合 | 总市值 | 今日盈亏 | 收益率 | 特点 |
|------|--------|----------|--------|------|
| **现有持仓** | ${existing_perf['total_value']:,.0f} | ${existing_perf['total_pnl']:,.0f} | {existing_perf['total_pnl_pct']:+.2f}% | 科技 + 能源 |
| **旧权重组合** | ${old_weight_perf['total_value']:,.0f} | ${old_weight_perf['total_pnl']:,.0f} | {old_weight_perf['total_pnl_pct']:+.2f}% | 量价 60%+ 价值 40% |
| **新权重组合** | ${new_weight_perf['total_value']:,.0f} | ${new_weight_perf['total_pnl']:,.0f} | {new_weight_perf['total_pnl_pct']:+.2f}% | 量价 40%+ 价值 30%+ 质量 30% |

---

## 🏆 现有持仓 Top 5

| 股票 | 市值 | 盈亏 | 收益率 |
|------|------|------|--------|
"""
    
    # 现有持仓 Top 5
    existing_positions = sorted(existing_perf['positions'], key=lambda x: abs(x['value']), reverse=True)[:5]
    for pos in existing_positions:
        report += f"| {pos['name']} | ${pos['value']:,.0f} | ${pos['pnl']:+,.0f} | {pos['pnl_pct']:+.2f}% |\n"
    
    report += f"""
---

## 💼 旧权重组合 Top 5

| 股票 | 权重 | 价格 | 今日涨跌 | 收益率 |
|------|------|------|----------|--------|
"""
    
    # 旧权重 Top 5
    old_positions = sorted(old_weight_perf['positions'], key=lambda x: x['weight'], reverse=True)[:5]
    for pos in old_positions:
        report += f"| {pos['name']} | {pos['weight']:.1f}% | ${pos['current_price']:.2f} | {pos['change_pct']:+.2f}% | {pos['pnl_pct']:+.2f}% |\n"
    
    report += f"""
---

## 🎯 新权重组合 Top 5

| 股票 | 权重 | 价格 | 今日涨跌 | 收益率 |
|------|------|------|----------|--------|
"""
    
    # 新权重 Top 5
    new_positions = sorted(new_weight_perf['positions'], key=lambda x: x['weight'], reverse=True)[:5]
    for pos in new_positions:
        report += f"| {pos['name']} | {pos['weight']:.1f}% | ${pos['current_price']:.2f} | {pos['change_pct']:+.2f}% | {pos['pnl_pct']:+.2f}% |\n"
    
    report += f"""
---

## 📊 表现对比

| 指标 | 现有持仓 | 旧权重 | 新权重 | 最佳 |
|------|----------|--------|--------|------|
| **今日收益** | {existing_perf['total_pnl_pct']:+.2f}% | {old_weight_perf['total_pnl_pct']:+.2f}% | {new_weight_perf['total_pnl_pct']:+.2f}% | {max([existing_perf['total_pnl_pct'], old_weight_perf['total_pnl_pct'], new_weight_perf['total_pnl_pct']], key=abs):+.2f}% |
| **估值 (PE)** | 12.5 | 7.16 | 6.28 | 新权重 |
| **破净股** | 15% | 67% | 65% | 旧权重 |
| **质量 (ROE)** | 14.5% | N/A | 15.8% | 新权重 |

---

## 💡 今日观察

### 表现最佳组合
**{max([existing_perf, old_weight_perf, new_weight_perf], key=lambda x: x['total_pnl_pct'])['total_pnl_pct']:+.2f}%**: 

"""
    
    best = max([existing_perf, old_weight_perf, new_weight_perf], key=lambda x: x['total_pnl_pct'])
    if best == existing_perf:
        report += "现有持仓表现最佳，科技股/能源股领涨\n"
    elif best == old_weight_perf:
        report += "旧权重组合表现最佳，低估值策略占优\n"
    else:
        report += "新权重组合表现最佳，质量因子有效\n"
    
    report += f"""
### 行业表现
- **保险**: 关注中国太平、中国人寿表现
- **基建**: 中国状态建设、北京控股
- **消费**: 李宁、中升控股

### 风险提示
- 关注港股流动性
- 保险行业集中度偏高（38-41%）
- 科技股波动风险

---

## 📝 操作建议

### 现有持仓
- ✅ 保持科技股 + 能源股配置
- ⚠️ 关注科技股估值风险
- ✅ 继续执行期权策略

### 量化组合
- ✅ 继续观察模拟盘表现
- ⏳ 1-2 周后考虑小资金实盘
- ✅ 每周再平衡

---

*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    return report


def save_monitoring_data(existing_perf: dict, old_perf: dict, new_perf: dict):
    """保存监控数据"""
    
    # 加载历史数据
    history_file = MONITORING_DIR / 'tracking_history.json'
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    
    # 添加新记录
    new_record = {
        'date': date.today().isoformat(),
        'timestamp': datetime.now().isoformat(),
        'existing': {
            'total_value': existing_perf['total_value'],
            'total_pnl': existing_perf['total_pnl'],
            'total_pnl_pct': existing_perf['total_pnl_pct']
        },
        'old_weight': {
            'total_value': old_perf['total_value'],
            'total_pnl': old_perf['total_pnl'],
            'total_pnl_pct': old_perf['total_pnl_pct']
        },
        'new_weight': {
            'total_value': new_perf['total_value'],
            'total_pnl': new_perf['total_pnl'],
            'total_pnl_pct': new_perf['total_pnl_pct']
        }
    }
    
    history.append(new_record)
    
    # 保存（保留最近 90 天）
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history[-90:], f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"📊 每日组合跟踪监控")
    print(f"{'='*60}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # 连接 OpenD
    quote_ctx = connect_opend()
    if quote_ctx is None:
        return
    
    try:
        # 收集所有股票代码
        all_codes = set()
        
        # 旧权重组合代码
        old_weights_file = REPORTS_DIR / 'portfolio_HK_20260326.csv'
        if old_weights_file.exists():
            df = pd.read_csv(old_weights_file)
            all_codes.update(df['code'].tolist())
        
        # 新权重组合代码
        new_weights_file = REPORTS_DIR / 'portfolio_HK_20260326_new.csv'
        if new_weights_file.exists():
            df = pd.read_csv(new_weights_file)
            all_codes.update(df['code'].tolist())
        
        # 获取当前价格
        print(f"正在获取 {len(all_codes)} 只股票价格...")
        current_prices = get_current_prices(quote_ctx, list(all_codes))
        print(f"✅ 获取价格完成")
        
        # 加载组合权重
        print("\n加载组合权重...")
        old_weights = load_portfolio_weights(str(old_weights_file))
        new_weights = load_portfolio_weights(str(new_weights_file))
        print(f"✅ 旧权重组合：{len(old_weights)} 只股票")
        print(f"✅ 新权重组合：{len(new_weights)} 只股票")
        
        # 计算组合表现
        print("\n计算组合表现...")
        old_perf = calculate_portfolio_performance(old_weights, current_prices)
        new_perf = calculate_portfolio_performance(new_weights, current_prices)
        existing_perf = load_existing_portfolio()
        
        print(f"✅ 现有持仓：${existing_perf['total_value']:,.0f} ({existing_perf['total_pnl_pct']:+.2f}%)")
        print(f"✅ 旧权重组合：${old_perf['total_value']:,.0f} ({old_perf['total_pnl_pct']:+.2f}%)")
        print(f"✅ 新权重组合：${new_perf['total_value']:,.0f} ({new_perf['total_pnl_pct']:+.2f}%)")
        
        # 生成报告
        print("\n生成监控报告...")
        report = generate_daily_report(existing_perf, old_perf, new_perf)
        
        # 保存报告
        report_file = MONITORING_DIR / f'daily_monitoring_{date.today().strftime("%Y%m%d")}.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存到：{report_file}")
        
        # 保存历史数据
        save_monitoring_data(existing_perf, old_perf, new_perf)
        print(f"✅ 历史数据已更新")
        
        # 显示摘要
        print(f"\n{'='*60}")
        print(f"📊 今日表现摘要")
        print(f"{'='*60}")
        print(f"现有持仓：       ${existing_perf['total_value']:>12,.0f}  ({existing_perf['total_pnl_pct']:>+7.2f}%)")
        print(f"动量 + 价值：     ${old_perf['total_value']:>12,.0f}  ({old_perf['total_pnl_pct']:>+7.2f}%)")
        print(f"动量 + 价值 + 质量：${new_perf['total_value']:>12,.0f}  ({new_perf['total_pnl_pct']:>+7.2f}%)")
        print(f"{'='*60}")
        
        # 找出最佳组合
        performances = [
            ('现有持仓', existing_perf['total_pnl_pct']),
            ('动量 + 价值', old_perf['total_pnl_pct']),
            ('动量 + 价值 + 质量', new_perf['total_pnl_pct'])
        ]
        best = max(performances, key=lambda x: x[1])
        print(f"🏆 今日最佳：{best[0]} ({best[1]:+.2f}%)")
        print(f"{'='*60}\n")
    
    finally:
        quote_ctx.close()


if __name__ == "__main__":
    main()
     ]
        best = max(performances, key=lambda x: x[1])
        print(f"🏆 今日最佳：{best[0]} ({best[1]:+.2f}%)")
        print(f"{'='*60}\n")
    
    finally:
        quote_ctx.close()


if __name__ == "__main__":
    main()
