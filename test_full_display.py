#!/usr/bin/env python3
# 测试完整显示（股票名 + 当日涨跌幅 + 成本盈亏 + 金额变化）

from futu import OpenQuoteContext, RET_OK
import json

with open('config/feng_portfolio.json', 'r') as f:
    portfolio = json.load(f)

quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

print('📊 完整信息测试')
print('=' * 80)

total_change_hkd = 0

# 测试港股
hk_holdings = portfolio['accounts']['hk_stocks']['holdings']
hk_codes = [f"HK.{h['symbol'].replace('.HK', '')}" for h in hk_holdings]

ret, data = quote_ctx.get_market_snapshot(hk_codes)

if ret == RET_OK:
    for i, code in enumerate(hk_codes):
        symbol = code.split('.')[1] + '.HK'
        last_price = float(data['last_price'][i])
        prev_close = float(data['prev_close_price'][i])
        today_change = ((last_price - prev_close) / prev_close) * 100
        
        # 获取持仓信息
        holding = hk_holdings[i]
        name = holding.get('name', symbol)
        shares = holding.get('shares', 0)
        cost_pnl = holding['pnl_percent']
        today_change_value = (last_price - prev_close) * shares if prev_close > 0 else 0
        total_change_hkd += today_change_value
        
        # 显示异动股票
        if abs(today_change) >= 3:
            emoji = '🟢' if today_change > 5 else '🔴' if today_change < -5 else '📈'
            fire = ' 🔥' if today_change >= 5 else ''
            value_str = f"(HK${today_change_value:+,.0f})"
            print(f'{emoji} {name}({symbol}): 今日{today_change:+.1f}% {value_str} | 成本{cost_pnl:+.1f}%{fire}')

quote_ctx.close()

print()
print(f'💰 今日港股持仓变化：HK${total_change_hkd:+,.0f}')
print()
print('✅ 测试完成！显示股票名、涨跌幅、金额变化、成本盈亏')
