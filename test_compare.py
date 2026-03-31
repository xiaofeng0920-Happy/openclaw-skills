#!/usr/bin/env python3
# 测试对比显示

from futu import OpenQuoteContext, RET_OK
import json

with open('config/feng_portfolio.json', 'r') as f:
    portfolio = json.load(f)

quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

print('📊 当日涨跌幅 vs 成本价盈亏 对比')
print('=' * 70)

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
        
        # 获取成本价盈亏
        holding = hk_holdings[i]
        cost_pnl = holding['pnl_percent']
        
        # 判断是否显示
        if abs(today_change) >= 3:
            emoji = '🟢' if today_change > 5 else '🔴' if today_change < -5 else '📈'
            fire = ' 🔥' if today_change >= 5 else ''
            print(f'{emoji} {symbol}: 今日{today_change:+.1f}% | 成本{cost_pnl:+.1f}%{fire}')

quote_ctx.close()

print()
print('✅ 测试完成！两个维度同时显示')
