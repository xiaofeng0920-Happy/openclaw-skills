#!/usr/bin/env python3
"""
Stock Indicator Query: Query specific stock indicators.
Supports: A-shares (via MCP + akshare), HK stocks (via akshare)

A-shares support: All indicators
HK stocks support: Price, valuation, market cap indicators only
Technical indicators (MA, KDJ, MACD, RSI) are A-share only via MCP
"""

import sys
import json

try:
    import akshare as ak
except ImportError:
    print(json.dumps({
        "error": "akshare not installed",
        "message": "Run: pip3 install akshare -U"
    }, indent=2))
    sys.exit(1)

# Import MCP query
sys.path.insert(0, '/'.join(__file__.split('/')[:-1]))
from mcp_query import query_mcp

# Available indicators with Chinese aliases
INDICATORS = {
    # Price indicators
    "price": {"zh": "当前价格", "aliases": ["股价", "现价", "最新价", "当前价"]},
    "open": {"zh": "开盘价", "aliases": ["开盘"]},
    "high": {"zh": "最高价", "aliases": ["最高", "高点"]},
    "low": {"zh": "最低价", "aliases": ["最低", "低点"]},
    "close": {"zh": "收盘价", "aliases": ["收盘"]},
    "pre_close": {"zh": "昨收价", "aliases": ["昨收", "昨日收盘"]},
    "change": {"zh": "涨跌额", "aliases": ["涨跌"]},
    "change_pct": {"zh": "涨跌幅", "aliases": ["涨幅", "跌幅", "涨跌幅度"]},
    
    # Valuation indicators
    "pe_ratio": {"zh": "市盈率", "aliases": ["PE", "市盈率 TTM"]},
    "pe_ttm": {"zh": "市盈率 (TTM)", "aliases": ["PE TTM", "滚动市盈率"]},
    "pe_static": {"zh": "市盈率 (静)", "aliases": ["静态市盈率", "PE 静"]},
    "pb_ratio": {"zh": "市净率", "aliases": ["PB"]},
    "ps_ratio": {"zh": "市销率", "aliases": ["PS"]},
    "pcf_ratio": {"zh": "市现率", "aliases": ["PCF"]},
    "peg_ratio": {"zh": "PEG 值", "aliases": ["PEG"]},
    "dividend_yield": {"zh": "股息率", "aliases": ["分红率", "股息"]},
    
    # Market cap
    "market_cap": {"zh": "总市值", "aliases": ["市值"]},
    "float_market_cap": {"zh": "流通市值", "aliases": ["流通市值"]},
    "total_shares": {"zh": "总股本", "aliases": ["总股本", "总股数"]},
    "float_shares": {"zh": "流通股本", "aliases": ["流通股本", "流通股数"]},
    
    # Trading
    "volume": {"zh": "成交量", "aliases": ["成交量"]},
    "turnover": {"zh": "成交额", "aliases": ["成交额", "成交金额"]},
    "amplitude": {"zh": "振幅", "aliases": ["振幅", "波动幅度"]},
    "turnover_rate": {"zh": "换手率", "aliases": ["换手率", "周转率"]},
    "volume_ratio": {"zh": "量比", "aliases": ["量比"]},
    
    # Financial
    "revenue": {"zh": "营业收入", "aliases": ["营收", "营业收入", "销售收入"]},
    "net_profit": {"zh": "净利润", "aliases": ["利润", "净利润", "纯利润"]},
    "eps": {"zh": "每股收益", "aliases": ["EPS", "每股收益", "每股盈利"]},
    "bvps": {"zh": "每股净资产", "aliases": ["BVPS", "每股净资产", "每股账面价值"]},
    "roe": {"zh": "净资产收益率", "aliases": ["ROE", "净资产收益率", "股东权益回报率"]},
    "gross_margin": {"zh": "销售毛利率", "aliases": ["毛利率", "销售毛利率"]},
    "debt_ratio": {"zh": "资产负债率", "aliases": ["负债率", "资产负债率"]},
    
    # Technical (MCP only - A-shares only)
    "ma5": {"zh": "5 日均线", "aliases": ["五日均线", "MA5", "MA(5)"]},
    "ma10": {"zh": "10 日均线", "aliases": ["十日均线", "MA10", "MA(10)"]},
    "ma20": {"zh": "20 日均线", "aliases": ["二十日均线", "MA20", "MA(20)"]},
    "ma30": {"zh": "30 日均线", "aliases": ["三十日均线", "MA30", "MA(30)"]},
    "ma60": {"zh": "60 日均线", "aliases": ["六十日均线", "MA60", "MA(60)"]},
    "kdj_k": {"zh": "KDJ-K", "aliases": ["KDJ K 值", "K 值"]},
    "kdj_d": {"zh": "KDJ-D", "aliases": ["KDJ D 值", "D 值"]},
    "kdj_j": {"zh": "KDJ-J", "aliases": ["KDJ J 值", "J 值"]},
    "macd_dif": {"zh": "MACD-DIF", "aliases": ["MACD DIF", "DIF"]},
    "macd_dea": {"zh": "MACD-DEA", "aliases": ["MACD DEA", "DEA"]},
    "rsi6": {"zh": "RSI(6)", "aliases": ["RSI6", "6 日 RSI"]},
    "rsi12": {"zh": "RSI(12)", "aliases": ["RSI12", "12 日 RSI"]},
    "rsi24": {"zh": "RSI(24)", "aliases": ["RSI24", "24 日 RSI"]},
}

# HK stocks support limited indicators
HK_SUPPORTED_INDICATORS = {
    # Price
    "price", "change", "change_pct",
    # Valuation
    "pe_ratio", "pb_ratio", "dividend_yield",
    # Market cap
    "market_cap",
}

# A-shares support all indicators except technical (which need MCP)
A_SHARE_BASIC_INDICATORS = set(INDICATORS.keys()) - {
    "ma5", "ma10", "ma20", "ma30", "ma60",
    "kdj_k", "kdj_d", "kdj_j",
    "macd_dif", "macd_dea",
    "rsi6", "rsi12", "rsi24"
}

TECHNICAL_INDICATORS = {
    "ma5", "ma10", "ma20", "ma30", "ma60",
    "kdj_k", "kdj_d", "kdj_j",
    "macd_dif", "macd_dea",
    "rsi6", "rsi12", "rsi24"
}

def normalize_indicator(indicator):
    """Convert Chinese or alias to canonical indicator name"""
    indicator_lower = indicator.lower().strip()
    if indicator_lower in INDICATORS:
        return indicator_lower
    for canonical, info in INDICATORS.items():
        if indicator_lower == info["zh"].lower():
            return canonical
        if indicator_lower in [a.lower() for a in info.get("aliases", [])]:
            return canonical
    return None

def check_indicator_support(symbol, indicators):
    """Check if indicators are supported for the given market"""
    unsupported = []
    technical_requested = []
    
    is_hk = symbol.startswith("HK")
    is_a = symbol.isdigit() and (symbol.startswith("6") or symbol.startswith("0") or symbol.startswith("3"))
    
    for ind in indicators:
        if is_hk:
            if ind not in HK_SUPPORTED_INDICATORS:
                unsupported.append(ind)
        elif is_a:
            if ind in TECHNICAL_INDICATORS:
                technical_requested.append(ind)
    
    return unsupported, technical_requested

def get_indicator_from_mcp(symbol, indicators):
    """Get indicators from MCP server (A-shares only)"""
    technical_indicators = list(TECHNICAL_INDICATORS)
    
    if any(ind in indicators for ind in technical_indicators):
        depth = "full"
    elif any(ind in indicators for ind in ["revenue", "net_profit", "eps", "bvps", "roe"]):
        depth = "medium"
    else:
        depth = "brief"
    
    result = query_mcp(symbol, depth)
    if not result:
        return None
    
    data = result.get("data", {})
    output = {}
    
    if "price" in indicators and "price" in data:
        output["price"] = data["price"]
    if "change_pct" in indicators and "change_pct" in data:
        output["change_pct"] = data["change_pct"]
    if "pe_ratio" in indicators and "pe_ratio" in data:
        output["pe_ratio"] = data["pe_ratio"]
    if "pb_ratio" in indicators and "pb_ratio" in data:
        output["pb_ratio"] = data["pb_ratio"]
    if "roe" in indicators and "roe" in data:
        output["roe"] = data["roe"]
    
    return {
        "symbol": result["symbol"],
        "name": result["name"],
        "source": "mcp",
        "indicators": output,
        "update_time": result.get("update_time", "")
    }

def get_indicator_from_akshare(symbol, indicators):
    """Get indicators from akshare"""
    output = {}
    
    try:
        if symbol.startswith("HK"):
            code = symbol[2:]
            data = ak.stock_hk_spot()
            if data is not None and len(data) > 0:
                row = data[data['代码'] == code]
                if len(row) > 0:
                    row = row.iloc[0]
                    if "price" in indicators:
                        output["price"] = float(row.get("最新价", 0))
                    if "change" in indicators:
                        output["change"] = float(row.get("涨跌额", 0))
                    if "change_pct" in indicators:
                        output["change_pct"] = float(row.get("涨跌幅", 0))
                    if "pe_ratio" in indicators and row.get("市盈率"):
                        output["pe_ratio"] = float(row.get("市盈率", 0))
                    if "pb_ratio" in indicators and row.get("市净率"):
                        output["pb_ratio"] = float(row.get("市净率", 0))
                    if "market_cap" in indicators and row.get("市值"):
                        output["market_cap"] = float(row.get("市值", 0))
        
        else:
            if any(ind in indicators for ind in ["pe_ratio", "pe_ttm", "pb_ratio", "market_cap", 
                                                   "float_market_cap", "total_shares", "float_shares",
                                                   "ps_ratio", "pcf_ratio", "peg_ratio"]):
                try:
                    data = ak.stock_value_em(symbol=symbol)
                    if data is not None and len(data) > 0:
                        row = data.iloc[0]
                        if "pe_ratio" in indicators:
                            output["pe_ratio"] = float(row.get("PE(TTM)", 0))
                        if "pe_ttm" in indicators:
                            output["pe_ttm"] = float(row.get("PE(TTM)", 0))
                        if "pe_static" in indicators:
                            output["pe_static"] = float(row.get("PE(静)", 0))
                        if "pb_ratio" in indicators:
                            output["pb_ratio"] = float(row.get("市净率", 0))
                        if "ps_ratio" in indicators:
                            output["ps_ratio"] = float(row.get("市销率", 0))
                        if "pcf_ratio" in indicators:
                            output["pcf_ratio"] = float(row.get("市现率", 0))
                        if "peg_ratio" in indicators:
                            output["peg_ratio"] = float(row.get("PEG 值", 0))
                        if "market_cap" in indicators:
                            output["market_cap"] = float(row.get("总市值", 0))
                        if "float_market_cap" in indicators:
                            output["float_market_cap"] = float(row.get("流通市值", 0))
                        if "total_shares" in indicators:
                            output["total_shares"] = float(row.get("总股本", 0))
                        if "float_shares" in indicators:
                            output["float_shares"] = float(row.get("流通股本", 0))
                except:
                    pass
        
        if not output:
            return None
        
        return {
            "symbol": symbol,
            "source": "akshare",
            "indicators": output,
            "update_time": ""
        }
    except Exception as e:
        return None

def main():
    if len(sys.argv) < 3:
        print(json.dumps({
            "error": "Missing arguments",
            "usage": "query_indicator.py <symbol> <indicator1> [indicator2] [...]",
            "examples": [
                "query_indicator.py 600000 price",
                "query_indicator.py 600519 pe_ratio pb_ratio",
                "query_indicator.py HK00700 price market_cap",
                "query_indicator.py 600000 五日均线 (Chinese supported)"
            ],
            "available_indicators": list(INDICATORS.keys())[:20],
            "total_indicators": len(INDICATORS),
            "note": "Both English and Chinese indicator names are supported. HK stocks support limited indicators."
        }, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    symbol = sys.argv[1]
    raw_indicators = sys.argv[2:]
    
    # Normalize indicators
    indicators = []
    invalid = []
    for ind in raw_indicators:
        normalized = normalize_indicator(ind)
        if normalized:
            indicators.append(normalized)
        else:
            invalid.append(ind)
    
    # Check indicator support
    unsupported, technical_requested = check_indicator_support(symbol, indicators)
    
    if invalid:
        print(json.dumps({
            "error": "Invalid indicators",
            "invalid": invalid,
            "valid_indicators": list(INDICATORS.keys()),
            "hint": "Use English names (e.g., pe_ratio) or Chinese names (e.g., 市盈率)"
        }, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    if unsupported:
        print(json.dumps({
            "error": "Indicators not supported for this market",
            "symbol": symbol,
            "market": "HK" if symbol.startswith("HK") else "A",
            "unsupported": unsupported,
            "hk_supported": list(HK_SUPPORTED_INDICATORS),
            "hint": "HK stocks support: price, change, PE, PB, dividend yield, market cap only. Technical indicators (MA, KDJ, MACD, RSI) are A-share only."
        }, indent=2, ensure_ascii=False))
        sys.exit(1)
    
    result = None
    
    # Try MCP first for A-shares (especially for technical indicators)
    if not symbol.startswith("HK") and technical_requested:
        result = get_indicator_from_mcp(symbol, indicators)
    
    # Fallback to akshare
    if not result:
        result = get_indicator_from_akshare(symbol, indicators)
    
    if result:
        result["indicator_names"] = {ind: INDICATORS.get(ind, ind) for ind in indicators}
        if technical_requested:
            result["note"] = "Technical indicators from MCP (A-shares only)"
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps({
            "error": "Failed to get indicators",
            "symbol": symbol,
            "indicators": indicators
        }, indent=2, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
