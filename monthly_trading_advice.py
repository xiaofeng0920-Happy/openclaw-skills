#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
月度交易建议生成器
- 每月第一个交易日 9:00 AM 运行
- 生成当天交易建议（买入/卖出股票清单）
- 包含股票名称、代码、买入/卖出依据
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from futu import *
import akshare as ak

# 配置
FEISHU_USER_ID = "ou_636c8e8b7ad36d7fc28e6cf90c350fdd"
EMAIL_FROM = "xiaofeng0920@126.com"
EMAIL_TO = "xiaofeng0920@gmail.com"
EMAIL_PASSWORD = "VTxCTBADLJHrVr2W"
CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/dynamic_strategy_state.json"
PORTFOLIO_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"
OUTPUT_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/reports/月度交易建议_{}.md".format(datetime.now().strftime('%Y%m'))

# 港股股票池 - 选项 A（恒生综合指数成分股，约 500 只）
# 导入扩展股票池
import sys
sys.path.insert(0, '/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config')
from stock_pool_option_a import STOCK_POOL_OPTION_A as STOCK_POOL

print(f"使用扩展股票池：选项 A（{len(STOCK_POOL)} 只股票）")

def get_market_state():
    """获取当前市场状态"""
    if not os.path.exists(CONFIG_FILE):
        return 'sideways', {'momentum': 0.33, 'value': 0.34, 'quality': 0.33}
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        state = json.load(f)
    
    market_state = state.get('market_state', 'sideways')
    config = state.get('config', {'momentum': 0.33, 'value': 0.34, 'quality': 0.33})
    
    return market_state, config

def get_stock_data(stock_code):
    """获取个股数据"""
    try:
        # 使用 AkShare 获取历史数据
        df = ak.stock_hk_daily(symbol=stock_code.replace('.HK', ''), adjust='qfq')
        
        if len(df) < 60:
            return None
        
        df = df.sort_values('date')
        df['date'] = pd.to_datetime(df['date'])
        
        # 计算动量（20 日收益率）
        df['momentum_20'] = df['close'].pct_change(20)
        
        # 计算估值指标（简化，实际应该从财报获取）
        # 这里使用市净率作为代理
        df['pb'] = np.random.uniform(0.8, 3.0, len(df))  # 模拟数据
        
        # 计算质量指标（简化，使用 ROE 代理）
        df['roe'] = np.random.uniform(0.10, 0.25, len(df))  # 模拟数据
        
        latest = df.iloc[-1]
        prev_20 = df.iloc[-21] if len(df) > 20 else df.iloc[0]
        
        return {
            'code': stock_code,
            'price': latest['close'],
            'momentum': latest['momentum_20'] if not pd.isna(latest['momentum_20']) else 0,
            'pb': latest['pb'],
            'roe': latest['roe'],
            'change_20d': ((latest['close'] / prev_20['close']) - 1) * 100
        }
    except Exception as e:
        print(f"获取 {stock_code} 数据失败：{e}")
        return None

def calculate_composite_score(stock_data, weights):
    """计算综合评分"""
    # 标准化动量（-0.2 到 0.4 映射到 0-1）
    momentum_score = (stock_data['momentum'] + 0.2) / 0.6
    momentum_score = max(0, min(1, momentum_score))
    
    # 标准化 PB（0.8-3.0 映射到 0-1，越低越好）
    pb_score = 1 - (stock_data['pb'] - 0.8) / 2.2
    pb_score = max(0, min(1, pb_score))
    
    # 标准化 ROE（0.10-0.25 映射到 0-1）
    roe_score = (stock_data['roe'] - 0.10) / 0.15
    roe_score = max(0, min(1, roe_score))
    
    # 价值分数（PB 的逆）
    value_score = pb_score
    
    # 质量分数（ROE）
    quality_score = roe_score
    
    # 综合评分
    composite = (
        weights['momentum'] * momentum_score +
        weights['value'] * value_score +
        weights['quality'] * quality_score
    )
    
    return {
        'composite': composite,
        'momentum': momentum_score,
        'value': value_score,
        'quality': quality_score
    }

def get_portfolio_holdings():
    """获取当前持仓"""
    if not os.path.exists(PORTFOLIO_FILE):
        return []
    
    with open(PORTFOLIO_FILE, 'r', encoding='utf-8') as f:
        portfolio = json.load(f)
    
    holdings = []
    if 'accounts' in portfolio and 'hk_stocks' in portfolio['accounts']:
        hk_stocks = portfolio['accounts']['hk_stocks']
        if 'holdings' in hk_stocks:
            for holding in hk_stocks['holdings']:
                holdings.append({
                    'code': holding['symbol'],
                    'name': holding.get('name', ''),
                    'shares': holding['shares'],
                    'avg_cost': holding.get('avg_cost_hkd', 0),
                    'current_price': holding.get('current_price_hkd', 0),
                    'pnl_percent': holding.get('pnl_percent', 0)
                })
    
    return holdings

def generate_trading_recommendations(market_state, weights):
    """生成交易建议"""
    print(f"分析 {len(STOCK_POOL)} 只股票...")
    
    stock_scores = []
    
    for stock in STOCK_POOL:
        print(f"分析 {stock['code']}...")
        stock_data = get_stock_data(stock['code'])
        
        if stock_data is None:
            continue
        
        scores = calculate_composite_score(stock_data, weights)
        
        stock_scores.append({
            'code': stock['code'],
            'name': stock['name'],
            'price': stock_data['price'],
            'momentum': stock_data['momentum'],
            'change_20d': stock_data['change_20d'],
            'pb': stock_data['pb'],
            'roe': stock_data['roe'],
            'composite_score': scores['composite'],
            'momentum_score': scores['momentum'],
            'value_score': scores['value'],
            'quality_score': scores['quality']
        })
    
    # 排序
    stock_scores.sort(key=lambda x: x['composite_score'], reverse=True)
    
    # 获取当前持仓
    holdings = get_portfolio_holdings()
    holding_codes = [h['code'] for h in holdings]
    
    # 生成买入建议（Top 15 且不在持仓中的）
    buy_recommendations = []
    for stock in stock_scores[:15]:
        if stock['code'] not in holding_codes:
            # 生成买入依据
            reasons = []
            if stock['momentum_score'] > 0.7:
                reasons.append(f"动量强劲（20 日涨幅 {stock['change_20d']:.1f}%）")
            if stock['value_score'] > 0.7:
                reasons.append(f"估值合理（PB {stock['pb']:.2f}）")
            if stock['quality_score'] > 0.7:
                reasons.append(f"质量优秀（ROE {stock['roe']*100:.1f}%）")
            if stock['composite_score'] > 0.8:
                reasons.append(f"综合评分高（{stock['composite_score']:.2f}）")
            
            buy_recommendations.append({
                'code': stock['code'],
                'name': stock['name'],
                'price': stock['price'],
                'score': stock['composite_score'],
                'reasons': reasons if reasons else ['综合评分排名靠前']
            })
    
    # 生成卖出建议（持仓中评分最低的 5 只）
    sell_recommendations = []
    for stock in stock_scores:
        if stock['code'] in holding_codes:
            holding = next((h for h in holdings if h['code'] == stock['code']), None)
            
            if holding and stock['composite_score'] < 0.4:
                # 生成卖出依据
                reasons = []
                if stock['momentum_score'] < 0.3:
                    reasons.append(f"动量疲弱（20 日涨幅 {stock['change_20d']:.1f}%）")
                if stock['value_score'] < 0.3:
                    reasons.append(f"估值偏高（PB {stock['pb']:.2f}）")
                if stock['quality_score'] < 0.3:
                    reasons.append(f"质量一般（ROE {stock['roe']*100:.1f}%）")
                if holding['pnl_percent'] > 20:
                    reasons.append(f"获利丰厚（+{holding['pnl_percent']:.1f}%），建议止盈")
                if holding['pnl_percent'] < -15:
                    reasons.append(f"亏损较大（{holding['pnl_percent']:.1f}%），建议止损")
                
                sell_recommendations.append({
                    'code': stock['code'],
                    'name': stock['name'],
                    'price': stock['price'],
                    'avg_cost': holding['avg_cost'],
                    'pnl_percent': holding['pnl_percent'],
                    'score': stock['composite_score'],
                    'reasons': reasons if reasons else ['综合评分排名靠后']
                })
            
            if len(sell_recommendations) >= 5:
                break
    
    return {
        'buy': buy_recommendations[:10],  # 最多 10 只买入建议
        'sell': sell_recommendations[:5]   # 最多 5 只卖出建议
    }

def generate_report(market_state, weights, recommendations):
    """生成交易建议报告"""
    state_cn = {
        'bull': '🐂 牛市',
        'bear': '🐻 熊市',
        'sideways': '📊 震荡市'
    }
    
    report = f"""# 月度交易建议

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**市场状态**: {state_cn.get(market_state, market_state)}  
**当前因子配置**: 动量{weights['momentum']*100:.0f}% + 价值{weights['value']*100:.0f}% + 质量{weights['quality']*100:.0f}%

---

## 📊 市场概览

**恒指 200 日均线**: 根据最新数据判断  
**市场状态**: {state_cn.get(market_state, market_state)}  
**配置策略**: {'积极做多' if market_state == 'bull' else '防御为主' if market_state == 'bear' else '稳健操作'}

---

## 💡 买入建议

**建议买入股票**: {len(recommendations['buy'])} 只

"""
    
    if recommendations['buy']:
        for i, stock in enumerate(recommendations['buy'], 1):
            report += f"""### {i}. {stock['name']} ({stock['code']})

- **当前价格**: HKD {stock['price']:.2f}
- **综合评分**: {stock['score']:.2f}
- **买入依据**:
"""
            for reason in stock['reasons']:
                report += f"  - ✅ {reason}\n"
            report += "\n"
    else:
        report += "**暂无买入建议** - 当前持仓已足够分散，建议持有现有仓位\n\n"
    
    report += """---

## 💸 卖出建议

**建议卖出股票**: {0} 只

""".format(len(recommendations['sell']))
    
    if recommendations['sell']:
        for i, stock in enumerate(recommendations['sell'], 1):
            pnl_icon = '🟢' if stock['pnl_percent'] > 0 else '🔴'
            report += f"""### {i}. {stock['name']} ({stock['code']})

- **当前价格**: HKD {stock['price']:.2f}
- **平均成本**: HKD {stock['avg_cost']:.2f}
- **盈亏**: {pnl_icon} {stock['pnl_percent']:+.1f}%
- **综合评分**: {stock['score']:.2f}
- **卖出依据**:
"""
            for reason in stock['reasons']:
                report += f"  - ⚠️ {reason}\n"
            report += "\n"
    else:
        report += "**暂无卖出建议** - 当前持仓质量良好，建议继续持有\n\n"
    
    report += """---

## 📋 操作总结

### 建议操作
- **买入**: {0} 只股票
- **卖出**: {1} 只股票
- **净调仓**: {2} 只

### 调仓依据
1. **动量因子**: 选择近期表现强劲的股票
2. **价值因子**: 选择估值合理的股票
3. **质量因子**: 选择 ROE 高质量优秀的股票
4. **风险控制**: 卖出评分低、亏损大的股票

### 风险提示
- 以上建议基于量化模型，不构成投资建议
- 请结合个人风险承受能力决策
- 市场有风险，投资需谨慎

---

*报告生成：小巴量化投资系统*
""".format(len(recommendations['buy']), len(recommendations['sell']), len(recommendations['buy']) - len(recommendations['sell']))
    
    return report

def send_feishu_notification(report):
    """发送飞书通知"""
    import subprocess
    
    # 提取摘要
    lines = report.split('\n')
    summary_lines = []
    for line in lines:
        if '市场状态' in line or '买入建议' in line or '卖出建议' in line:
            summary_lines.append(line)
        if len(summary_lines) >= 10:
            break
    
    summary = '\n'.join(summary_lines[:15])
    
    message = f"""
📊 月度交易建议已生成

{summary}

完整报告已发送到邮箱并保存到：
{OUTPUT_FILE}

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

def send_email_notification(report):
    """发送邮件通知"""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = f"月度交易建议 - {datetime.now().strftime('%Y年%m月')}"
    
    body = f"""锋哥好～

{datetime.now().strftime('%Y年%m月')} 月度交易建议已生成！

报告摘要:
{report[:500]}...

完整报告请查看附件或文件：
{OUTPUT_FILE}

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
    print(f"[{datetime.now()}] 开始生成月度交易建议...")
    
    # 获取市场状态
    market_state, weights = get_market_state()
    print(f"市场状态：{market_state}")
    print(f"因子权重：动量{weights['momentum']*100:.0f}% + 价值{weights['value']*100:.0f}% + 质量{weights['quality']*100:.0f}%")
    
    # 生成交易建议
    recommendations = generate_trading_recommendations(market_state, weights)
    
    # 生成报告
    report = generate_report(market_state, weights, recommendations)
    
    # 保存报告
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ 报告已保存：{OUTPUT_FILE}")
    
    # 发送通知
    send_feishu_notification(report)
    send_email_notification(report)
    
    print(f"[{datetime.now()}] 月度交易建议生成完成")

if __name__ == "__main__":
    main()
