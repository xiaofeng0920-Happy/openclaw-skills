#!/usr/bin/env python3
"""
财报数据分析模块
为小巴股票日报提供财报数据支持

用法:
    python analyze_earnings.py --date 2026-03-19
    python analyze_earnings.py --ticker NVDA
    python analyze_earnings.py --summary
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# 数据目录
DATA_DIR = Path.home() / ".openclaw/workspace/agents/xiaoba-portfolio/data"

def load_earnings_data(date_str: str = None) -> dict:
    """加载指定日期的财报数据"""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    earnings_file = DATA_DIR / f"market_data_{date_str}.json"
    
    if not earnings_file.exists():
        # 尝试前一天的文件
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        earnings_file = DATA_DIR / f"market_data_{yesterday}.json"
    
    if not earnings_file.exists():
        return {"error": f"未找到财报数据文件"}
    
    with open(earnings_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_earnings_summary(data: dict) -> dict:
    """生成财报摘要"""
    if "earnings" not in data:
        return {"error": "无财报数据"}
    
    earnings = data["earnings"]
    
    beat_stocks = []
    miss_stocks = []
    inline_stocks = []
    
    for symbol, info in earnings.items():
        if "error" in info:
            continue
        
        beat = info.get("beat_estimate")
        surprise = info.get("surprise_percent", 0)
        
        stock_data = {
            "symbol": symbol,
            "surprise": surprise,
            "eps": info.get("actual_eps"),
            "quarter": info.get("fiscal_quarter"),
            "market_cap": info.get("market_cap"),
            "pe_ratio": info.get("pe_ratio")
        }
        
        if beat is True:
            beat_stocks.append(stock_data)
        elif beat is False:
            miss_stocks.append(stock_data)
        else:
            inline_stocks.append(stock_data)
    
    return {
        "total": len(beat_stocks) + len(miss_stocks) + len(inline_stocks),
        "beat_count": len(beat_stocks),
        "miss_count": len(miss_stocks),
        "inline_count": len(inline_stocks),
        "beat_stocks": sorted(beat_stocks, key=lambda x: x["surprise"], reverse=True),
        "miss_stocks": sorted(miss_stocks, key=lambda x: x["surprise"]),
        "inline_stocks": inline_stocks
    }

def format_report(summary: dict, date_str: str) -> str:
    """格式化财报报告"""
    lines = []
    lines.append(f"📊 持仓财报数据分析 | {date_str}")
    lines.append("=" * 60)
    lines.append("")
    
    # 概览
    lines.append("**财报概览**:")
    lines.append(f"- 总计：{summary['total']} 只股票")
    lines.append(f"- ✅ 超预期：{summary['beat_count']} 只 ({summary['beat_count']/summary['total']*100:.1f}%)")
    lines.append(f"- ❌ 低于预期：{summary['miss_count']} 只 ({summary['miss_count']/summary['total']*100:.1f}%)")
    lines.append(f"- ➖ 符合预期：{summary['inline_count']} 只")
    lines.append("")
    
    # 超预期亮点
    if summary['beat_stocks']:
        lines.append("**超预期亮点**:")
        for stock in summary['beat_stocks'][:5]:
            lines.append(f"- **{stock['symbol']}**: EPS ${stock['eps']} (+{stock['surprise']:.1f}%)")
        lines.append("")
    
    # 低于预期
    if summary['miss_stocks']:
        lines.append("**低于预期**:")
        for stock in summary['miss_stocks'][:3]:
            lines.append(f"- **{stock['symbol']}**: EPS ${stock['eps']} ({stock['surprise']:.1f}%)")
        lines.append("")
    
    # 投资启示
    lines.append("**投资启示**:")
    if summary['beat_count'] > summary['miss_count'] * 2:
        lines.append("- ✅ 财报季整体乐观，多数公司超预期")
        lines.append("- 建议：积极参与，重点关注超预期股票的后续表现")
    elif summary['miss_count'] > summary['beat_count']:
        lines.append("- ⚠️ 财报季表现不佳，多家公司低于预期")
        lines.append("- 建议：谨慎观望，控制仓位，等待明确信号")
    else:
        lines.append("- ➖ 财报季表现分化，好坏参半")
        lines.append("- 建议：精选个股，关注基本面强劲的公司")
    
    return "\n".join(lines)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="财报数据分析模块")
    parser.add_argument("--date", type=str, help="查询日期 (YYYY-MM-DD)")
    parser.add_argument("--ticker", type=str, help="查询单只股票")
    parser.add_argument("--summary", action="store_true", help="显示摘要报告")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    
    args = parser.parse_args()
    
    # 加载数据
    data = load_earnings_data(args.date)
    
    if "error" in data:
        print(f"❌ {data['error']}")
        sys.exit(1)
    
    # 查询单只股票
    if args.ticker:
        earnings = data.get("earnings", {})
        if args.ticker in earnings:
            info = earnings[args.ticker]
            if args.json:
                print(json.dumps(info, indent=2))
            else:
                print(f"📊 {args.ticker} 财报数据:")
                print(f"  财季：{info.get('fiscal_quarter', 'N/A')}")
                print(f"  EPS: ${info.get('actual_eps', 'N/A')}")
                print(f"  超预期：{info.get('surprise_percent', 0):.1f}%")
                print(f"  市值：${info.get('market_cap', 0):,.0f}M")
        else:
            print(f"⚠️  未找到 {args.ticker} 的财报数据")
        return
    
    # 生成摘要报告
    summary = get_earnings_summary(data)
    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        report = format_report(summary, date_str)
        print(report)
        
        # 保存到文件
        output_file = DATA_DIR / f"earnings_analysis_{date_str}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("")
        print(f"✅ 报告已保存：{output_file}")

if __name__ == "__main__":
    main()
