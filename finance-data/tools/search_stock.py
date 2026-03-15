#!/usr/bin/env python3
"""
Stock/Fund Search: Search for stock or fund codes by name.
Supports: A-shares, HK stocks, Funds

Uses akshare for all searches.
Note: Requires network connection and akshare installation.
"""

import sys
import json

try:
    import akshare as ak
except ImportError:
    print(json.dumps({
        "error": "akshare not installed",
        "message": "Run: pip3 install akshare -U",
        "keyword": sys.argv[1] if len(sys.argv) > 1 else ""
    }, indent=2))
    sys.exit(1)

def search_stock(keyword, market="all"):
    """Search for stocks by keyword (name or code)"""
    results = []
    keyword_upper = str(keyword).strip().upper()
    keyword_lower = str(keyword).strip().lower()
    
    try:
        # A-shares search
        if market in ["all", "a"]:
            try:
                data = ak.stock_info_a_code_name()
                if data is not None and len(data) > 0:
                    # Filter by keyword (case insensitive)
                    mask = data['name'].str.contains(keyword, case=False, na=False)
                    filtered = data[mask]
                    
                    for _, row in filtered.iterrows():
                        name = str(row.get("name", ""))
                        code = str(row.get("code", ""))
                        results.append({
                            "name": name,
                            "symbol": code,
                            "market": "A",
                            "full_symbol": code
                        })
            except Exception as e:
                pass
        
        # HK stocks search - use stock_hk_spot() which is more reliable
        if market in ["all", "hk"]:
            try:
                # stock_hk_spot() is slower but more reliable than *_em APIs
                data = ak.stock_hk_spot()
                if data is not None and len(data) > 0:
                    # Filter by keyword (case insensitive for Chinese)
                    mask = data['中文名称'].str.contains(keyword, case=False, na=False)
                    filtered = data[mask]
                    
                    for _, row in filtered.iterrows():
                        name = str(row.get("中文名称", ""))
                        code = str(row.get("代码", ""))
                        results.append({
                            "name": name,
                            "symbol": code,
                            "market": "HK",
                            "full_symbol": "HK" + code
                        })
            except Exception as e:
                pass
        
    except Exception as e:
        pass
    
    return results

def search_fund(keyword):
    """Search for funds by keyword (name or code)"""
    results = []
    keyword_upper = str(keyword).strip().upper()
    
    try:
        # Use fund_open_fund_daily_em() which has fund codes
        data = ak.fund_open_fund_daily_em()
        if data is not None and len(data) > 0:
            for _, row in data.iterrows():
                name = str(row.get("基金简称", ""))
                code = str(row.get("基金代码", ""))
                if keyword_upper in name.upper() or keyword_upper in code:
                    results.append({
                        "name": name,
                        "symbol": code,
                        "market": "FUND",
                        "full_symbol": code
                    })
                    if len(results) >= 5:
                        break
    except Exception as e:
        pass
    
    return results

def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Missing keyword",
            "usage": "search_stock.py <keyword> [type] [market]",
            "examples": [
                "search_stock.py 阿里巴巴",
                "search_stock.py 腾讯 stock hk",
                "search_stock.py 易方达 fund",
                "search_stock.py 茅台"
            ]
        }, indent=2))
        sys.exit(1)
    
    keyword = sys.argv[1]
    search_type = sys.argv[2] if len(sys.argv) > 2 else "all"
    market = sys.argv[3] if len(sys.argv) > 3 else "all"
    
    results = []
    
    if search_type in ["all", "stock"]:
        results.extend(search_stock(keyword, market))
    
    if search_type in ["all", "fund"]:
        results.extend(search_fund(keyword))
    
    # Handle ambiguity - if multiple results, ask user to specify
    if len(results) > 1:
        output = {
            "keyword": keyword,
            "count": len(results),
            "ambiguous": True,
            "message": f"找到 {len(results)} 只股票/基金，请指定具体名称或代码",
            "results": results,
            "suggestion": "请使用更完整的名称或股票代码进行查询"
        }
    else:
        output = {
            "keyword": keyword,
            "count": len(results),
            "ambiguous": False,
            "results": results,
            "note": "If no results found, try different keyword or check akshare connection"
        }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
