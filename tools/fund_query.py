#!/usr/bin/env python3
"""
Fund Query: Fund NAV data via akshare.
"""

import sys
import json

try:
    import akshare as ak
except ImportError:
    print(json.dumps({"error": "akshare not installed", "message": "Run: pip3 install akshare -U"}), file=sys.stderr)
    sys.exit(1)

def query_fund(code):
    try:
        # API changed: use symbol parameter instead of fund
        data = ak.fund_open_fund_info_em(symbol=code)
        if data is not None and len(data) > 0:
            row = data.iloc[0]
            return {
                "source": "akshare",
                "type": "fund",
                "symbol": code,
                "name": code,  # API no longer returns fund name
                "data": {
                    "nav": float(row.get("单位净值", 0)),
                    "daily_growth": float(row.get("日增长率", 0)),
                },
                "update_time": str(row.get("净值日期", ""))
            }
        return None
    except Exception as e:
        print("Query failed: {}".format(e), file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: fund_query.py <code>", file=sys.stderr)
        sys.exit(1)
    
    result = query_fund(sys.argv[1])
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "Fund query failed", "code": sys.argv[1]}))
        sys.exit(1)

if __name__ == "__main__":
    main()
