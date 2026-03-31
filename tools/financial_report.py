#!/usr/bin/env python3
"""
Financial Report: Financial data for A-shares and HK stocks via akshare.
Supports comprehensive financial indicators for HK stocks.
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

def parse_float(value):
    """安全解析浮点数"""
    if value is None or value == '' or value == 'N/A':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def query_financial(symbol):
    try:
        symbol = str(symbol).strip()
        result = {}
        
        # A-shares
        if symbol.isdigit() and (symbol.startswith("6") or symbol.startswith("0") or symbol.startswith("3")):
            data = ak.stock_value_em(symbol=symbol)
            if data is not None and len(data) > 0:
                row = data.iloc[0]
                return {
                    "source": "akshare",
                    "type": "financial",
                    "symbol": symbol,
                    "name": symbol,
                    "data": {
                        "pe_ratio": parse_float(row.get("PE(TTM)", 0)),
                        "pe_static": parse_float(row.get("PE(静)", 0)),
                        "pb_ratio": parse_float(row.get("市净率", 0)),
                        "ps_ratio": parse_float(row.get("市销率", 0)),
                        "market_cap": parse_float(row.get("总市值", 0)),
                        "float_market_cap": parse_float(row.get("流通市值", 0)),
                        "price": parse_float(row.get("当日收盘价", 0))
                    },
                    "update_time": str(row.get("数据日期", ""))
                }
        
        # HK stocks - use comprehensive financial APIs
        elif symbol.startswith("HK"):
            code = symbol[2:]
            result = {}
            
            # Data source 1: stock_hk_financial_indicator_em
            try:
                df1 = ak.stock_hk_financial_indicator_em(symbol=code)
                if df1 is not None and len(df1) > 0:
                    row1 = df1.iloc[0]
                    result.update({
                        # Valuation
                        "pe_ratio": parse_float(row1.get("市盈率")),
                        "pb_ratio": parse_float(row1.get("市净率")),
                        
                        # Per share data
                        "eps": parse_float(row1.get("基本每股收益 (元)")),
                        "bvps": parse_float(row1.get("每股净资产 (元)")),
                        "dividend_per_share": parse_float(row1.get("每股股息 TTM(港元)")),
                        "dividend_yield": parse_float(row1.get("股息率 TTM(%)")),
                        "payout_ratio": parse_float(row1.get("派息比率 (%)")),
                        "operating_cash_flow_per_share": parse_float(row1.get("每股经营现金流 (元)")),
                        
                        # Market cap
                        "market_cap": parse_float(row1.get("总市值 (港元)")),
                        
                        # Income
                        "revenue": parse_float(row1.get("营业总收入")),
                        "net_profit": parse_float(row1.get("净利润")),
                        "net_profit_margin": parse_float(row1.get("销售净利率 (%)")),
                        
                        # Returns
                        "roe": parse_float(row1.get("股东权益回报率 (%)")),
                        "roa": parse_float(row1.get("总资产回报率 (%)"))
                    })
            except Exception as e:
                pass
            
            # Data source 2: stock_financial_hk_analysis_indicator_em
            try:
                df2 = ak.stock_financial_hk_analysis_indicator_em(symbol=code)
                if df2 is not None and len(df2) > 0:
                    row2 = df2.iloc[0]
                    result.update({
                        # Growth rates
                        "revenue_yoy": parse_float(row2.get("OPERATE_INCOME_YOY")),
                        "gross_profit_yoy": parse_float(row2.get("GROSS_PROFIT_YOY")),
                        "net_profit_yoy": parse_float(row2.get("HOLDER_PROFIT_YOY")),
                        
                        # Margins
                        "gross_margin": parse_float(row2.get("GROSS_PROFIT_RATIO")),
                        "net_margin": parse_float(row2.get("NET_PROFIT_RATIO")),
                        
                        # Returns
                        "roe_avg": parse_float(row2.get("ROE_AVG")),
                        "roa": parse_float(row2.get("ROA")),
                        "roic": parse_float(row2.get("ROIC_YEARLY")),
                        
                        # Financial health
                        "debt_ratio": parse_float(row2.get("DEBT_ASSET_RATIO")),
                        "current_ratio": parse_float(row2.get("CURRENT_RATIO")),
                        
                        # Cash flow
                        "ocf_to_sales": parse_float(row2.get("OCF_SALES"))
                    })
            except Exception as e:
                pass
            
            if result:
                return {
                    "source": "akshare",
                    "type": "financial",
                    "symbol": symbol,
                    "name": symbol,
                    "data": result,
                    "update_time": ""
                }
        
        return None
    except Exception as e:
        print("Query failed: {}".format(e), file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: financial_report.py <symbol>", file=sys.stderr)
        sys.exit(1)
    
    result = query_financial(sys.argv[1])
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2, cls=DateEncoder))
    else:
        print(json.dumps({"error": "Financial query failed", "symbol": sys.argv[1]}))
        sys.exit(1)

if __name__ == "__main__":
    main()
