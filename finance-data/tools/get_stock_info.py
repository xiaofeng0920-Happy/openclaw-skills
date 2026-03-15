#!/usr/bin/env python3
"""
Get Stock Info: Get comprehensive stock information (price + key indicators + company profile).
For A-shares: Returns price, PE, PB, change_pct, market_cap
For HK stocks: Returns price, PE, PB, change_pct, market_cap + company profile
For Funds: Returns NAV, daily_growth

Usage:
  get_stock_info.py <symbol>
  
Examples:
  get_stock_info.py 600000      # A-share
  get_stock_info.py HK00700     # HK stock
  get_stock_info.py 110011      # Fund
"""

import sys
import json

try:
    import akshare as ak
except ImportError:
    print(json.dumps({"error": "akshare not installed", "message": "Run: pip3 install akshare -U"}), file=sys.stderr)
    sys.exit(1)

# Import MCP query
sys.path.insert(0, '/'.join(__file__.split('/')[:-1]))
from mcp_query import query_mcp

def get_stock_info(symbol):
    """Get comprehensive stock information"""
    
    # A-shares - try MCP first
    if symbol.isdigit() and (symbol.startswith("6") or symbol.startswith("0") or symbol.startswith("3")):
        # Try MCP first
        mcp_result = query_mcp(symbol, "brief")
        if mcp_result:
            data = mcp_result.get("data", {})
            return {
                "source": "mcp",
                "type": "stock",
                "symbol": symbol,
                "name": mcp_result.get("name", ""),
                "data": {
                    "price": data.get("price"),
                    "change_pct": data.get("change_pct"),
                    "pe_ratio": data.get("pe_ratio"),
                    "pb_ratio": data.get("pb_ratio")
                },
                "update_time": mcp_result.get("update_time", ""),
                "note": "Use query_indicator.py for specific indicators, stock_news.py for news"
            }
        
        # Fallback to akshare
        try:
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
                        "market_cap": float(row.get("总市值", 0))
                    },
                    "update_time": str(row.get("数据日期", "")),
                    "note": "Use query_indicator.py for specific indicators, stock_news.py for news"
                }
        except:
            pass
    
    # HK stocks
    elif symbol.startswith("HK"):
        code = symbol[2:]
        result = {}
        
        # Get price data
        try:
            data = ak.stock_hk_spot()
            if data is not None and len(data) > 0:
                row = data[data['代码'] == code]
                if len(row) > 0:
                    row = row.iloc[0]
                    result.update({
                        "price": float(row.get("最新价", 0)),
                        "change_pct": float(row.get("涨跌幅", 0)),
                        "pe_ratio": float(row.get("市盈率", 0)) if row.get("市盈率") else None,
                        "pb_ratio": float(row.get("市净率", 0)) if row.get("市净率") else None,
                        "market_cap": float(row.get("市值", 0)) if row.get("市值") else None
                    })
        except:
            pass
        
        # Get company profile
        try:
            profile_df = ak.stock_hk_company_profile_em(symbol=code)
            if profile_df is not None and len(profile_df) > 0:
                row = profile_df.iloc[0]
                result.update({
                    "company_name": row.get("公司名称", ""),
                    "industry": row.get("所属行业", ""),
                    "chairman": row.get("董事长", ""),
                    "employees": int(row.get("员工人数", 0)) if row.get("员工人数") else None,
                    "profile": row.get("公司介绍", "")[:300] if row.get("公司介绍") else ""
                })
        except:
            pass
        
        if result:
            return {
                "source": "akshare",
                "type": "stock",
                "symbol": symbol,
                "name": result.get("company_name", ""),
                "data": result,
                "update_time": "",
                "note": "Use query_indicator.py for specific indicators, stock_news.py for news"
            }
    
    # Funds
    elif symbol.isdigit() and len(symbol) == 6:
        try:
            data = ak.fund_open_fund_info_em(symbol=symbol)
            if data is not None and len(data) > 0:
                row = data.iloc[0]
                return {
                    "source": "akshare",
                    "type": "fund",
                    "symbol": symbol,
                    "name": symbol,
                    "data": {
                        "nav": float(row.get("单位净值", 0)),
                        "daily_growth": float(row.get("日增长率", 0))
                    },
                    "update_time": str(row.get("净值日期", "")),
                    "note": "Use query_indicator.py for specific indicators"
                }
        except:
            pass
    
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: get_stock_info.py <symbol>", file=sys.stderr)
        print("Examples:")
        print("  get_stock_info.py 600000    # A-share")
        print("  get_stock_info.py HK00700   # HK stock")
        print("  get_stock_info.py 110011    # Fund")
        sys.exit(1)
    
    result = get_stock_info(sys.argv[1])
    
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "Failed to get stock info", "symbol": sys.argv[1]}))
        sys.exit(1)

if __name__ == "__main__":
    main()
