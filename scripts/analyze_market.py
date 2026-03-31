#!/usr/bin/env python3
"""
股票行情分析 Skill
读取 stock-data-fetcher/data 目录下的最新 JSON 文件，分析市场行情
"""

import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(os.path.expanduser("~/.agents/skills/stock-data-fetcher/data"))

def load_latest_data() -> dict:
    """加载最新的数据文件"""
    json_files = list(DATA_DIR.glob("market-*.json"))
    
    if not json_files:
        print("❌ 未找到数据文件")
        sys.exit(1)
    
    # 按文件名排序（日期排序）
    latest = sorted(json_files, reverse=True)[0]
    
    with open(latest, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_market(data: dict, top_n: int = 10) -> dict:
    """分析市场数据"""
    stocks = data.get('stocks', [])
    
    # 按涨跌幅排序
    sorted_stocks = sorted(stocks, key=lambda x: x.get('change_pct', 0), reverse=True)
    
    # 统计
    total = len(stocks)
    up = sum(1 for s in stocks if s.get('change_pct', 0) > 0)
    down = sum(1 for s in stocks if s.get('change_pct', 0) < 0)
    flat = sum(1 for s in stocks if s.get('change_pct', 0) == 0)
    
    # 行业统计
    sectors = {}
    for stock in stocks:
        sector = stock.get('sector', '其他')
        if sector not in sectors:
            sectors[sector] = []
        sectors[sector].append(stock)
    
    sector_stats = {}
    for sector, sector_stocks in sectors.items():
        avg_change = sum(s.get('change_pct', 0) for s in sector_stocks) / len(sector_stocks)
        up_count = sum(1 for s in sector_stocks if s.get('change_pct', 0) > 0)
        total_amount = sum(s.get('amount', 0) for s in sector_stocks)
        sector_stats[sector] = {
            'avg_change': avg_change,
            'up_count': up_count,
            'total_count': len(sector_stocks),
            'total_amount': total_amount
        }
    
    # 资金流向（简化版：根据涨跌幅和成交额估算）
    for stock in stocks:
        change = stock.get('change_pct', 0)
        amount = stock.get('amount', 0)
        # 简化算法：上涨为正流入，下跌为负流出
        stock['net_flow'] = amount * change / 100 if change != 0 else 0
    
    # 资金流向排名
    sorted_by_flow = sorted(stocks, key=lambda x: x.get('net_flow', 0), reverse=True)
    
    return {
        'total': total,
        'up': up,
        'down': down,
        'flat': flat,
        'top_gainers': sorted_stocks[:top_n],
        'top_losers': sorted_stocks[-top_n:],
        'sector_stats': sector_stats,
        'top_inflow': sorted_by_flow[:5],
        'top_outflow': sorted_by_flow[-5:]
    }

def print_report(analysis: dict, data: dict):
    """打印分析报告"""
    timestamp = data.get('timestamp', 'Unknown')
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        date_str = dt.strftime('%Y-%m-%d %H:%M')
    except:
        date_str = timestamp
    
    print("=" * 70)
    print(f"📊 A 股市场行情分析 | {date_str}")
    print("=" * 70)
    print()
    
    # 市场概况
    print("【市场概况】")
    print(f"  统计股票：{analysis['total']} 支")
    print(f"  📈 上涨：{analysis['up']} 支 ({analysis['up']/analysis['total']*100:.1f}%)")
    print(f"  📉 下跌：{analysis['down']} 支 ({analysis['down']/analysis['total']*100:.1f}%)")
    print(f"  ➖ 平盘：{analysis['flat']} 支")
    print()
    
    # 涨幅榜
    print(f"【涨幅 TOP {len(analysis['top_gainers'])}】")
    for i, stock in enumerate(analysis['top_gainers'], 1):
        print(f"  {i}. {stock['name']} ({stock['code']}): ¥{stock['price']:.2f}  {stock['change_pct']:+.2f}%  {stock.get('sector', '')}")
        print(f"     成交量：{stock.get('volume', 0):.1f}万手  成交额：¥{stock.get('amount', 0):.2f}亿")
        print(f"     MA5: ¥{stock.get('ma5', 0):.2f}  RSI: {stock.get('rsi', 0):.1f}")
    print()
    
    # 跌幅榜
    print(f"【跌幅 TOP {len(analysis['top_losers'])}】")
    for i, stock in enumerate(analysis['top_losers'], 1):
        print(f"  {i}. {stock['name']} ({stock['code']}): ¥{stock['price']:.2f}  {stock['change_pct']:+.2f}%  {stock.get('sector', '')}")
        print(f"     成交量：{stock.get('volume', 0):.1f}万手  成交额：¥{stock.get('amount', 0):.2f}亿")
        print(f"     MA5: ¥{stock.get('ma5', 0):.2f}  RSI: {stock.get('rsi', 0):.1f}")
    print()
    
    # 行业表现
    print("【行业表现】")
    sorted_sectors = sorted(analysis['sector_stats'].items(), key=lambda x: x[1]['avg_change'], reverse=True)
    for sector, stats in sorted_sectors:
        icon = "📈" if stats['avg_change'] > 0.5 else ("📉" if stats['avg_change'] < -0.5 else "➖")
        print(f"  {icon} {sector}: {stats['avg_change']:+.2f}%  (上涨{stats['up_count']}/{stats['total_count']} 成交额¥{stats['total_amount']:.2f}亿)")
    print()
    
    # 资金流向
    print("【资金流向】")
    print("  净流入 TOP5:")
    for stock in analysis['top_inflow'][:5]:
        print(f"    {stock['name']} ({stock['code']}): ¥{stock.get('net_flow', 0):.2f}亿")
    
    print("  净流出 TOP5:")
    for stock in analysis['top_outflow'][:5]:
        print(f"    {stock['name']} ({stock['code']}): ¥{stock.get('net_flow', 0):.2f}亿")
    print()
    
    # 市场情绪
    sentiment = "偏多" if analysis['up'] > analysis['down'] * 1.2 else ("偏空" if analysis['down'] > analysis['up'] * 1.2 else "震荡")
    print("=" * 70)
    print(f"市场情绪：{sentiment}")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='A 股行情数据分析')
    parser.add_argument('--date', type=str, help='指定日期 (YYYYMMDD)')
    parser.add_argument('--top', type=int, default=10, help='显示前 N 名 (默认 10)')
    parser.add_argument('--json', action='store_true', help='输出 JSON 格式')
    
    args = parser.parse_args()
    
    # 加载数据
    data = load_latest_data()
    
    # 分析
    analysis = analyze_market(data, args.top)
    
    # 保存 Markdown 报告
    output_dir = Path(__file__).parent.parent / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    from datetime import datetime
    output_file = output_dir / f"market-{datetime.now().strftime('%Y%m%d')}.md"
    
    import io
    from contextlib import redirect_stdout
    
    f = io.StringIO()
    with redirect_stdout(f):
        print_report(analysis, data)
    
    with open(output_file, 'w', encoding='utf-8') as md:
        md.write(f.getvalue())
    
    print(f"\n✅ 报告已保存：{output_file}")
    
    # 输出
    if args.json:
        print(json.dumps(analysis, ensure_ascii=False, indent=2))
    else:
        print_report(analysis, data)

if __name__ == '__main__':
    main()
