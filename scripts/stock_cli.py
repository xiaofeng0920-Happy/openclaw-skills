#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股股票数据查询 CLI
基于 AKShare 库
"""

import akshare as ak
import json
import sys

def get_stock_spot(symbol: str = ""):
    """获取个股实时行情"""
    try:
        if symbol:
            df = ak.stock_zh_a_spot_em(symbol=symbol)
        else:
            df = ak.stock_zh_a_spot_em()
        print(df.to_json(orient='records', force_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

def get_stock_hist(symbol: str, period: str = "daily", start_date: str = "", end_date: str = ""):
    """获取历史 K 线"""
    try:
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        print(df.to_json(orient='records', force_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

def get_financial_indicator(symbol: str):
    """获取财务指标"""
    try:
        df = ak.stock_financial_analysis_indicator(symbol=symbol)
        print(df.to_json(orient='records', force_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

def get_board_industry(symbol: str):
    """获取行业板块"""
    try:
        df = ak.stock_board_industry_cons_em(symbol=symbol)
        print(df.to_json(orient='records', force_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

def get_fund_flow(stock: str, market: str = "sh"):
    """获取资金流向"""
    try:
        df = ak.stock_individual_fund_flow(stock=stock, market=market)
        print(df.to_json(orient='records', force_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python stock_cli.py <command> [args]")
        print("Commands: spot, hist, financial, industry, fundflow")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "spot":
        symbol = sys.argv[2] if len(sys.argv) > 2 else ""
        get_stock_spot(symbol)
    elif command == "hist":
        if len(sys.argv) < 3:
            print("Usage: python stock_cli.py hist <symbol> [period] [start_date] [end_date]")
            sys.exit(1)
        get_stock_hist(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "daily")
    elif command == "financial":
        if len(sys.argv) < 3:
            print("Usage: python stock_cli.py financial <symbol>")
            sys.exit(1)
        get_financial_indicator(sys.argv[2])
    elif command == "industry":
        if len(sys.argv) < 3:
            print("Usage: python stock_cli.py industry <sector>")
            sys.exit(1)
        get_board_industry(sys.argv[2])
    elif command == "fundflow":
        if len(sys.argv) < 3:
            print("Usage: python stock_cli.py fundflow <symbol> [market]")
            sys.exit(1)
        get_fund_flow(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "sh")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
