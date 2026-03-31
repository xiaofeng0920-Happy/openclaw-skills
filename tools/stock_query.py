#!/usr/bin/env python3
"""
Stock Query: A-share and HK stock prices via akshare.
Note: HK stock data may be slower due to API limitations.
"""

import sys
import json
from datetime import date, datetime

try:
    import akshare as ak
except ImportError:
    print(json.dumps({"error": "akshare not installed", "message": "Run: pip3 install akshare -U"}), file=sys.stderr)
    sys.exit(1)

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

def query_stock(symbol):
    try:
        symbol = str(symbol).strip()
        
        # A-shares
        if symbol.isdigit() and (symbol.startswith("6") or symbol.startswith("0") or symbol.startswith("3")):
            data = ak.stock_value_em(symbol=symbol)
            if data is not None and len(data) > 0:
                row = data.iloc[0]
                return {
                    "source": "akshare",
                    "type": "stock",
                    "symbol": symbol,
                    "name": symbol,
                    "data": {
                        "price": float(row.get("当日收盘价", 0)),
                        "change_pct": float(row.get("当日涨跌幅", 0)),
                        "pe_ratio": float(row.get("PE(TTM)", 0)),
                        "pb_ratio": float(row.get("市净率", 0)),
                        "market_cap": float(row.get("总市值", 0)),
                        "float_market_cap": float(row.get("流通市值", 0))
                    },
                    "update_time": str(row.get("数据日期", ""))
                }
        
        # HK stocks - use stock_hk_spot() which is more reliable
        elif symbol.startswith("HK"):
            code = symbol[2:]
            data = ak.stock_hk_spot()
            if data is not None and len(data) > 0:
                row = data[data['代码'] == code]
                if len(row) > 0:
                    row = row.iloc[0]
                    return {
                        "source": "akshare",
                        "type": "stock",
                        "symbol": symbol,
                        "name": row.get("中文名称", ""),
                        "data": {
                            "price": float(row.get("最新价", 0)),
                            "change": float(row.get("涨跌额", 0)),
                            "change_pct": float(row.get("涨跌幅", 0)),
                            "pe_ratio": float(row.get("市盈率", 0)) if row.get("市盈率") else 0,
                            "pb_ratio": float(row.get("市净率", 0)) if row.get("市净率") else 0,
                            "market_cap": float(row.get("市值", 0)) if row.get("市值") else 0
                        },
                        "update_time": ""
                    }
        
        return None
    except Exception as e:
        print("Query failed: {}".format(e), file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: stock_query.py <symbol>", file=sys.stderr)
        sys.exit(1)
    
    result = query_stock(sys.argv[1])
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2, cls=DateEncoder))
    else:
        print(json.dumps({"error": "Stock query failed", "symbol": sys.argv[1]}))
        sys.exit(1)

if __name__ == "__main__":
    main()
