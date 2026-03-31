#!/usr/bin/env python3
"""
A 股数据接口 - AkShare
集成到 TwoCities Portfolio 监控系统

功能:
- A 股实时行情
- 历史 K 线数据
- 财务数据查询
- 板块分析

用法:
    python3 akshare_data.py --symbol 000001
    python3 akshare_data.py --symbol 600519 --kline
    python3 akshare_data.py --financial 000001
"""

import akshare as ak
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

OUTPUT_DIR = Path.home() / ".openclaw/workspace/agents/twocities-portfolio/data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class AkShareDataFetcher:
    """A 股数据获取器"""
    
    def __init__(self):
        self.cache = {}
    
    def get_stock_spot(self, symbol: str = None) -> Optional[Dict]:
        """获取 A 股实时行情"""
        try:
            print(f"📊 获取 A 股实时行情...")
            df = ak.stock_zh_a_spot_em()
            
            if df.empty:
                print("⚠️  无实时行情数据")
                return None
            
            if symbol:
                # 查询单只股票
                stock_data = df[df['代码'] == symbol]
                if not stock_data.empty:
                    row = stock_data.iloc[0]
                    result = {
                        "symbol": symbol,
                        "name": row['名称'],
                        "price": float(row['最新价']),
                        "change": float(row['涨跌额']),
                        "change_percent": float(row['涨跌幅']),
                        "volume": float(row['成交量']),
                        "amount": float(row['成交额']),
                        "high": float(row['最高']),
                        "low": float(row['最低']),
                        "open": float(row['今开']),
                        "prev_close": float(row['昨收']),
                        "timestamp": datetime.now().isoformat(),
                        "source": "akshare"
                    }
                    print(f"✅ {symbol} {row['名称']}: ¥{row['最新价']} ({row['涨跌幅']}%)")
                    return result
                else:
                    print(f"⚠️  未找到股票：{symbol}")
                    return None
            else:
                # 返回全部
                print(f"✅ 获取到 {len(df)} 只 A 股实时行情")
                return {"total": len(df), "data": df.to_dict('records')}
                
        except Exception as e:
            print(f"❌ 获取实时行情失败：{e}")
            return None
    
    def get_stock_kline(self, symbol: str, period: str = "daily", 
                        start_date: str = None, end_date: str = None,
                        adjust: str = "qfq") -> Optional[Dict]:
        """获取 A 股历史 K 线"""
        try:
            if not start_date:
                start_date = "20260301"
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            
            print(f"📈 获取 {symbol} K 线数据 ({period})...")
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
            
            if df.empty:
                print(f"⚠️  {symbol} 无 K 线数据")
                return None
            
            print(f"✅ 获取到 {len(df)} 天数据")
            
            # 最新数据
            latest = df.iloc[-1]
            result = {
                "symbol": symbol,
                "period": period,
                "adjust": adjust,
                "data_count": len(df),
                "latest": {
                    "date": latest['日期'],
                    "open": float(latest['开盘']),
                    "high": float(latest['最高']),
                    "low": float(latest['最低']),
                    "close": float(latest['收盘']),
                    "volume": float(latest['成交量']),
                    "amount": float(latest['成交额']),
                    "change_percent": float(latest['涨跌幅'])
                },
                "timestamp": datetime.now().isoformat(),
                "source": "akshare"
            }
            
            # 显示最新数据
            print(f"   最新：{latest['日期']} 收盘¥{latest['收盘']} ({latest['涨跌幅']}%)")
            
            return result
            
        except Exception as e:
            print(f"❌ 获取 K 线数据失败：{e}")
            return None
    
    def get_financial_data(self, symbol: str) -> Optional[Dict]:
        """获取财务数据"""
        try:
            print(f"📊 获取 {symbol} 财务数据...")
            
            # 财务报表
            df = ak.stock_financial_abstract_ths(symbol=symbol)
            
            if df.empty:
                print(f"⚠️  {symbol} 无财务数据")
                return None
            
            print(f"✅ 获取到 {len(df)} 期财务数据")
            
            # 最新一期
            latest = df.iloc[0] if len(df) > 0 else None
            if latest is not None:
                result = {
                    "symbol": symbol,
                    "report_date": latest.get('报告期', 'N/A'),
                    "net_profit": float(latest.get('净利润', 0)) if '净利润' in latest else None,
                    "net_profit_yoy": float(latest.get('净利润同比增长率', 0)) if '净利润同比增长率' in latest else None,
                    "data_count": len(df),
                    "timestamp": datetime.now().isoformat(),
                    "source": "akshare"
                }
                print(f"   最新报告期：{latest.get('报告期', 'N/A')}")
                if '净利润' in latest:
                    print(f"   净利润：¥{latest.get('净利润', 0)}亿")
                return result
            
            return None
            
        except Exception as e:
            print(f"❌ 获取财务数据失败：{e}")
            return None
    
    def get_industry_board(self) -> Optional[Dict]:
        """获取行业板块"""
        try:
            print(f"📊 获取行业板块...")
            df = ak.stock_board_industry_name_em()
            
            if df.empty:
                print("⚠️  无行业板块数据")
                return None
            
            print(f"✅ 获取到 {len(df)} 个行业板块")
            
            result = {
                "total": len(df),
                "boards": df.to_dict('records') if len(df) > 0 else [],
                "timestamp": datetime.now().isoformat(),
                "source": "akshare"
            }
            
            return result
            
        except Exception as e:
            print(f"❌ 获取行业板块失败：{e}")
            return None

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="A 股数据接口 - AkShare")
    parser.add_argument("--symbol", type=str, help="股票代码 (例如：000001)")
    parser.add_argument("--kline", action="store_true", help="获取 K 线数据")
    parser.add_argument("--financial", type=str, help="获取财务数据")
    parser.add_argument("--board", action="store_true", help="获取行业板块")
    parser.add_argument("--export", action="store_true", help="导出数据")
    
    args = parser.parse_args()
    
    fetcher = AkShareDataFetcher()
    results = {}
    
    # 获取实时行情
    if args.symbol:
        spot_data = fetcher.get_stock_spot(args.symbol)
        if spot_data:
            results["spot"] = spot_data
    
    # 获取 K 线
    if args.kline and args.symbol:
        kline_data = fetcher.get_stock_kline(args.symbol)
        if kline_data:
            results["kline"] = kline_data
    
    # 获取财务数据
    if args.financial:
        financial_data = fetcher.get_financial_data(args.financial)
        if financial_data:
            results["financial"] = financial_data
    
    # 获取行业板块
    if args.board:
        board_data = fetcher.get_industry_board()
        if board_data:
            results["board"] = board_data
    
    # 导出
    if args.export and results:
        output_file = OUTPUT_DIR / f"akshare_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✅ 数据已保存：{output_file}")

if __name__ == "__main__":
    main()
