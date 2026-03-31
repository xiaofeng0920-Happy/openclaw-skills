#!/usr/bin/env python3
"""
History Price: Get historical stock price data and statistics.
Supports: A-shares and HK stocks

Usage:
  history_price.py <symbol> [days]
  
Examples:
  history_price.py 600000 30      # A-share, last 30 days
  history_price.py HK00700 90     # HK stock, last 90 days
"""

import sys
import json
from datetime import date, datetime

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print(json.dumps({"error": "akshare not installed", "message": "Run: pip3 install akshare -U"}), file=sys.stderr)
    sys.exit(1)

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

def get_history_data(symbol, days=30):
    """Get historical price data"""
    try:
        # A-shares - use stock_zh_a_daily
        if symbol.isdigit() and (symbol.startswith("6") or symbol.startswith("0") or symbol.startswith("3")):
            # Convert to sh/sz format
            prefix = "sh" if symbol.startswith("6") else "sz"
            full_symbol = f"{prefix}{symbol}"
            
            # Get last 60 days to ensure we have enough data
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - pd.Timedelta(days=days*2)).strftime('%Y%m%d')
            
            df = ak.stock_zh_a_daily(symbol=full_symbol, start_date=start_date, end_date=end_date)
            if df is not None and len(df) > 0:
                # Rename columns to standard format
                df = df.rename(columns={
                    'date': 'date',
                    'open': 'open',
                    'close': 'close',
                    'high': 'high',
                    'low': 'low',
                    'volume': 'volume'
                })
                df = df.head(days)
                return df
        
        # HK stocks
        elif symbol.startswith("HK"):
            code = symbol[2:]
            df = ak.stock_hk_daily(symbol=code)
            if df is not None and len(df) > 0:
                df = df.head(days)
                return df
        
        return None
    except Exception as e:
        return None

def calculate_statistics(df):
    """Calculate statistical indicators"""
    if df is None or len(df) == 0:
        return {}
    
    stats = {
        "period_high": float(df["high"].max()),
        "period_low": float(df["low"].min()),
        "period_avg": float(df["close"].mean()),
        "total_volume": float(df["volume"].sum()),
        "avg_volume": float(df["volume"].mean()),
    }
    
    if len(df) > 1:
        # Price change
        stats["price_change"] = float(df["close"].iloc[-1] - df["close"].iloc[0])
        stats["price_change_pct"] = float((df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100) if df["close"].iloc[0] > 0 else 0
        
        # Volatility
        daily_returns = df["close"].pct_change().dropna()
        stats["volatility"] = float(daily_returns.std() * 100)
        stats["avg_daily_change"] = float(daily_returns.abs().mean() * 100)
    else:
        stats["price_change"] = 0
        stats["price_change_pct"] = 0
        stats["volatility"] = 0
        stats["avg_daily_change"] = 0
    
    # Latest price
    latest = df.iloc[0]
    stats["latest_price"] = float(latest["close"])
    stats["latest_date"] = str(latest.get("date", ""))
    
    return stats

def get_history_info(symbol, days=30):
    """Get historical price info with statistics"""
    df = get_history_data(symbol, days)
    
    if df is None or len(df) == 0:
        return None
    
    stats = calculate_statistics(df)
    
    return {
        "symbol": symbol,
        "days": days,
        "data_points": len(df),
        "statistics": stats,
        "latest_data": {
            "date": str(df.iloc[0].get("date", "")),
            "open": float(df.iloc[0].get("open", 0)),
            "high": float(df.iloc[0].get("high", 0)),
            "low": float(df.iloc[0].get("low", 0)),
            "close": float(df.iloc[0].get("close", 0)),
            "volume": float(df.iloc[0].get("volume", 0))
        },
        "note": "Use query_indicator.py for specific indicators"
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: history_price.py <symbol> [days]", file=sys.stderr)
        print("Examples:")
        print("  history_price.py 600000 30     # A-share, 30 days")
        print("  history_price.py HK00700 90    # HK stock, 90 days")
        sys.exit(1)
    
    symbol = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    result = get_history_info(symbol, days)
    
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "Failed to get history data", "symbol": symbol}))
        sys.exit(1)

if __name__ == "__main__":
    main()
