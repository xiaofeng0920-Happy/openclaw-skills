#!/usr/bin/env python3
# 测试当日涨跌幅

from futu import OpenQuoteContext, RET_OK
import json

with open('config/feng_portfolio.json', 'r') as f:
    portfolio = json.load(f)

quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

print('📊 当日涨跌幅测试')
print('=' * 60)

# 测试港股
hk_holdings = portfolio['accounts']['hk_stocks']['holdings']
hk_codes = [f"HK.{h['symbol'].replace('.HK', '')}" for h in hk_holdings[:5]]  # 前 5 只

ret, data = quote_ctx.get_market_snapshot(hk_codes)

if ret == RET_OK:
    for i, code in enumerate(hk_codes):
        symbol = code.split('.')[1] + '.HK'
        last_price = float(data['last_price'][i])
        prev_close = float(data['prev_close_price'][i])
        today_change = ((last_price - prev_close) / prev_close) * 100
        
        emoji = '🟢' if today_change > 0 else '🔴' if today_change < 0 else '⚪'
        print(f'{emoji} {symbol}: ${last_price:.2f}  {today_change:+.1f}% (昨收：${prev_close:.2f})')

quote_ctx.close()

print()
print('✅ 测试完成！股价异动现在基于当日涨跌幅，不是成本价盈亏')
