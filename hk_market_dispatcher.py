#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股全市场分析 - 任务分发器
将 687 只股票分成多个 batch，启动多个 agent 并行分析
"""

import json
import os
from datetime import datetime
from futu import *

def get_all_hk_stocks():
    """获取所有港股列表"""
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    
    try:
        # 使用正确的 API 参数
        ret, data = quote_ctx.get_stock_basicinfo(market=TrdMarket.HK)
        
        print(f"  API 返回：ret={ret}")
        
        if ret == RET_OK and data is not None and not data.empty:
            print(f"  获取到 {len(data)} 条记录")
            stocks = []
            for _, row in data.iterrows():
                code = row.get('code', '')
                name = row.get('name', '')
                stock_type = row.get('stock_type', '')
                # 只保留普通股
                if code and name:
                    stocks.append({
                        'code': f'HK.{code}',
                        'name': name
                    })
            print(f"  过滤后：{len(stocks)} 只股票")
            return stocks
        print(f"  数据为空或 ret 不正确")
        return []
    except Exception as e:
        import traceback
        print(f"获取港股列表失败：{e}")
        traceback.print_exc()
        return []
    finally:
        quote_ctx.close()

def split_batches(stocks, batch_size=50):
    """分割成多个 batch"""
    batches = []
    for i in range(0, len(stocks), batch_size):
        batches.append(stocks[i:i + batch_size])
    return batches

def main():
    print("=" * 60)
    print("🚀 港股全市场分析 - 任务分发")
    print(f"🕐 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 获取所有港股
    print("\n📋 获取港股列表...")
    stocks = get_all_hk_stocks()
    
    if not stocks:
        print("❌ 获取港股列表失败")
        return
    
    print(f"✅ 共 {len(stocks)} 只港股")
    
    # 分割 batch
    batch_size = 50  # 每批 50 只
    batches = split_batches(stocks, batch_size)
    total_batches = len(batches)
    
    print(f"📦 分成 {total_batches} 个 batch (每批~{batch_size}只)")
    
    # 创建 batches 目录
    batches_dir = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/batches"
    os.makedirs(batches_dir, exist_ok=True)
    
    # 保存每个 batch
    print(f"\n💾 保存 batch 文件到 {batches_dir}...")
    for i, batch in enumerate(batches):
        batch_file = os.path.join(batches_dir, f"batch_{i}.json")
        with open(batch_file, 'w', encoding='utf-8') as f:
            json.dump({
                'batch_id': i,
                'total_batches': total_batches,
                'stocks': batch
            }, f, ensure_ascii=False, indent=2)
        print(f"  ✓ batch_{i}.json ({len(batch)} 只股票)")
    
    # 创建汇总脚本
    summary_script = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合并所有 batch 结果"""

import json
import os
from datetime import datetime
from glob import glob

def main():
    reports_dir = "/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/reports"
    batch_files = glob(os.path.join(reports_dir, "hk_market_scan_batch_*.json"))
    
    all_results = []
    
    for f in sorted(batch_files):
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            all_results.extend(data.get('results', []))
    
    # 排序
    all_results.sort(key=lambda x: x['score'], reverse=True)
    
    # 统计
    top = [r for r in all_results if r['score'] >= 75]
    recommend = [r for r in all_results if 60 <= r['score'] < 75]
    neutral = [r for r in all_results if 45 <= r['score'] < 60]
    caution = [r for r in all_results if r['score'] < 45]
    
    # 保存汇总
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_stocks': len(all_results),
        'top_stocks_count': len(top),
        'recommend_count': len(recommend),
        'neutral_count': len(neutral),
        'caution_count': len(caution),
        'top_stocks': top[:50],
        'all_results': all_results
    }
    
    output_file = os.path.join(reports_dir, "hk_market_full_summary.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print("=" * 60)
    print("📊 港股全市场分析 - 汇总报告")
    print("=" * 60)
    print(f"总股票数：{len(all_results)}")
    print(f"🔥 强烈推荐：{len(top)} 只")
    print(f"👍 推荐：{len(recommend)} 只")
    print(f"➖ 中性：{len(neutral)} 只")
    print(f"⚠️ 谨慎/回避：{len(caution)} 只")
    print(f"\\n💾 汇总报告：{output_file}")
    print("=" * 60)
    
    # 打印 Top 20
    print("\\n🏆 Top 20 股票:")
    for i, stock in enumerate(top[:20], 1):
        print(f"  {i}. {stock['name']} ({stock['code']}): HK$ {stock['price']}, {stock['score']}分")

if __name__ == "__main__":
    main()
'''
    
    summary_file = os.path.join(batches_dir, "merge_results.py")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary_script)
    
    print(f"\n✅ 任务分发完成!")
    print(f"\n📝 下一步:")
    print(f"  1. 启动 {total_batches} 个 agent 并行处理")
    print(f"  2. 每个 agent 运行：python3 hk_market_scan.py batches/batch_N.json")
    print(f"  3. 全部完成后运行：python3 batches/merge_results.py")
    print(f"\n💡 建议命令:")
    print(f"  # 后台运行所有 batch")
    for i in range(total_batches):
        print(f"  python3 hk_market_scan.py batches/batch_{i}.json &")
    print(f"\n  # 等待完成后合并")
    print(f"  python3 batches/merge_results.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
