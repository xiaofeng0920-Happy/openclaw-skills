#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
锋哥持仓深度分析 - 调用 GPT-4o
结合实时价格 + 历史走势 + 巴菲特策略
"""

import json
from datetime import datetime
from futu import *

CONFIG_FILE = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/config/feng_portfolio.json"

def load_portfolio():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_realtime_data(quote_ctx, symbol, market):
    """获取实时价格和涨跌幅"""
    try:
        if market == 'US':
            code = f"US.{symbol}"
        else:
            code = f"HK.{symbol}"
        
        ret, data = quote_ctx.get_market_snapshot(code)
        if ret == RET_OK and len(data) > 0:
            row = data.iloc[0]
            # 安全获取字段
            change_pct = row.get('change_percent', [0])[0] if 'change_percent' in row else 0
            pe = row.get('pe_ratio', [None])[0] if 'pe_ratio' in row else None
            return {
                'price': float(row['last_price'][0]),
                'change_pct': float(change_pct) if change_pct else 0,
                'pe': float(pe) if pe else None,
                'market_value': float(row['market_value'][0]) if 'market_value' in row and len(row['market_value']) > 0 else None
            }
        return None
    except Exception as e:
        print(f"获取 {symbol} 数据失败：{e}")
        return None

def analyze_portfolio():
    print(f"[{datetime.now()}] 开始获取实时数据...")
    
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    ret, state = quote_ctx.get_global_state()
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！")
        return None
    
    print("✅ OpenD 连接成功")
    
    portfolio = load_portfolio()
    
    # 整理持仓数据
    holdings_data = {
        'us_stocks': [],
        'hk_stocks': [],
        'options': {
            'us_options': portfolio['options']['us_options'],
            'hk_options': portfolio['options']['hk_options']
        },
        'account_info': portfolio.get('account_info', {}),
        'action_items': portfolio.get('action_items', [])
    }
    
    # 获取美股实时数据
    for holding in portfolio['accounts']['us_stocks']['holdings']:
        realtime = get_realtime_data(quote_ctx, holding['symbol'], 'US')
        if realtime:
            holdings_data['us_stocks'].append({
                'name': holding['name'],
                'symbol': holding['symbol'],
                'shares': holding['shares'],
                'avg_cost': holding['avg_cost_usd'],
                'current_price': realtime['price'],
                'change_pct': realtime['change_pct'],
                'pe_ratio': realtime['pe'],
                'value': holding['shares'] * realtime['price'],
                'pnl': (realtime['price'] - holding['avg_cost_usd']) * holding['shares'],
                'pnl_pct': ((realtime['price'] - holding['avg_cost_usd']) / holding['avg_cost_usd']) * 100
            })
    
    # 获取港股实时数据
    for holding in portfolio['accounts']['hk_stocks']['holdings']:
        symbol = holding['symbol'].replace('.HK', '')
        realtime = get_realtime_data(quote_ctx, symbol, 'HK')
        if realtime:
            holdings_data['hk_stocks'].append({
                'name': holding['name'],
                'symbol': holding['symbol'],
                'shares': holding['shares'],
                'avg_cost': holding['avg_cost_hkd'],
                'current_price': realtime['price'],
                'change_pct': realtime['change_pct'],
                'pe_ratio': realtime['pe'],
                'value_hkd': holding['shares'] * realtime['price'],
                'pnl_hkd': (realtime['price'] - holding['avg_cost_hkd']) * holding['shares'],
                'pnl_pct': ((realtime['price'] - holding['avg_cost_hkd']) / holding['avg_cost_hkd']) * 100
            })
    
    # 计算总体数据
    us_total = sum(h['value'] for h in holdings_data['us_stocks'])
    hk_total_hkd = sum(h['value_hkd'] for h in holdings_data['hk_stocks'])
    hk_total_usd = hk_total_hkd / 7.8
    
    holdings_data['summary'] = {
        'us_total_value': us_total,
        'hk_total_value_hkd': hk_total_hkd,
        'hk_total_value_usd': hk_total_usd,
        'total_value_usd': us_total + hk_total_usd + portfolio['accounts']['margin']['value_usd'],
        'us_count': len(holdings_data['us_stocks']),
        'hk_count': len(holdings_data['hk_stocks'])
    }
    
    quote_ctx.close()
    
    # 生成分析提示词
    prompt = f"""你是专业的投资顾问，请分析以下持仓并给出深度建议。

## 锋哥持仓数据（{datetime.now().strftime('%Y-%m-%d')} 实时）

### 总体情况
- 总资产：≈${holdings_data['summary']['total_value_usd']:,.0f} USD
- 美股：${holdings_data['summary']['us_total_value']:,.0f} ({holdings_data['summary']['us_count']} 只)
- 港股：${holdings_data['summary']['hk_total_value_usd']:,.0f} ({holdings_data['summary']['hk_count']} 只，{holdings_data['summary']['hk_total_value_hkd']:,.0f} HKD)
- 保证金账户：$335,000 USD

### 美股持仓
"""
    
    for h in holdings_data['us_stocks']:
        emoji = "🟢" if h['pnl'] >= 0 else "🔴"
        prompt += f"{emoji} {h['name']}({h['symbol']}): ${h['current_price']:.2f} ({h['change_pct']:+.2f}%) | 盈亏：${h['pnl']:,.0f} ({h['pnl_pct']:+.1f}%) | 持仓：${h['value']:,.0f}\n"
    
    prompt += "\n### 港股持仓\n"
    for h in holdings_data['hk_stocks']:
        emoji = "🟢" if h['pnl_hkd'] >= 0 else "🔴"
        prompt += f"{emoji} {h['name']}({h['symbol']}): ${h['current_price']:.2f} ({h['change_pct']:+.2f}%) | 盈亏：${h['pnl_hkd']:,.0f} HKD ({h['pnl_pct']:+.1f}%) | 持仓：${h['value_hkd']:,.0f} HKD\n"
    
    prompt += """
### 期权持仓（部分）
- 腾讯 CALL(600, 2026-05): +HKD 87,400 (+180%) ✅
- 阿里 Short Put: +155% ✅
- 中海油 CALL: -HKD 19,245 (-88%) ⚠️
- MSFT CALL(440): -$727 (-77%) ⚠️

### 分析要求

请结合**近 10 年（2016-2026）港股和美股市场走势**，进行深度分析：

1. **市场周期分析**
   - 美股：2016-2021 牛市，2022 熊市，2023-2025 AI 牛市，当前处于什么周期位置？
   - 港股：2017 高点，2018-2023 长期低迷，2024-2026 反弹，当前估值水平？
   - 未来 1-3 年趋势判断

2. **持仓诊断**
   - 行业配置是否合理？（科技、消费、能源、金融）
   - 个股集中度风险？
   - 与当前市场周期的匹配度？

3. **巴菲特策略评估**
   - 哪些持仓符合巴菲特标准（护城河、ROE、现金流）？
   - 哪些应该调仓？

4. **具体建议**
   - 立即执行（本周内）
   - 短期执行（1 个月内）
   - 中期调整（1-3 个月）
   - 长期策略（6-12 个月）

5. **风险预警**
   - 最大下行风险
   - 对冲建议

请用**专业但易懂**的语言，给出**可执行**的建议。数据用表格呈现，结论要清晰。
"""
    
    # 保存分析数据
    with open('/tmp/portfolio_analysis_input.json', 'w', encoding='utf-8') as f:
        json.dump({
            'holdings': holdings_data,
            'prompt': prompt
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 数据整理完成，共 {len(holdings_data['us_stocks'])} 只美股 + {len(holdings_data['hk_stocks'])} 只港股")
    print(f"📝 分析提示词已生成，{len(prompt)} 字符")
    
    return prompt

if __name__ == "__main__":
    prompt = analyze_portfolio()
    if prompt:
        print("\n" + "="*60)
        print("提示词预览（前 1000 字符）:")
        print("="*60)
        print(prompt[:1000])
        print("\n...（完整提示词已保存到 /tmp/portfolio_analysis_input.json）")
