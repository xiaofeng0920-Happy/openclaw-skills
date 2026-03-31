#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股量化组合 - 模拟盘建仓脚本

作者：小巴
日期：2026-03-26
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from futu import *
except ImportError:
    print("❌ 未安装 futu-api，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "futu-api", "-q"])
    from futu import *

# ============ 配置 ============
OPEND_HOST = '127.0.0.1'
OPEND_PORT = 11111
PORTFOLIO_FILE = '/Users/zhaoxf/.openclaw/workspace/agents/stock-system/reports/portfolio_HK_20260326.csv'
TOTAL_CAPITAL = 1000000  # 100 万港元模拟资金
TRD_ENV = TrdEnv.SIMULATE  # 模拟交易

# ============================


def connect_opend() -> OpenQuoteContext:
    """连接 OpenD"""
    quote_ctx = OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    ret, state = quote_ctx.get_global_state()
    
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！")
        return None
    
    print("✅ OpenD 连接成功")
    return quote_ctx


def load_portfolio() -> pd.DataFrame:
    """加载组合权重"""
    if not Path(PORTFOLIO_FILE).exists():
        print(f"❌ 组合文件不存在：{PORTFOLIO_FILE}")
        return pd.DataFrame()
    
    df = pd.read_csv(PORTFOLIO_FILE)
    print(f"✅ 加载组合：{len(df)} 只股票")
    return df


def get_current_price(quote_ctx: OpenQuoteContext, code: str) -> float:
    """获取当前价格"""
    try:
        ret, data = quote_ctx.get_market_snapshot(code)
        if ret == RET_OK and len(data) > 0:
            return float(data['last_price'].iloc[0])
        return None
    except Exception as e:
        return None


def calculate_order_quantity(weight: float, price: float, total_capital: float) -> int:
    """计算下单数量（取整到 100 股的倍数）"""
    amount = total_capital * weight
    quantity = int(amount / price / 100) * 100  # 港股最小交易单位 100 股
    return max(100, quantity)  # 至少 100 股


def place_orders(quote_ctx: OpenQuoteContext, portfolio: pd.DataFrame):
    """执行下单"""
    
    print(f"\n{'='*60}")
    print(f"💼 开始模拟盘建仓")
    print(f"{'='*60}")
    print(f"总资金：{TOTAL_CAPITAL:,.0f} HKD")
    print(f"交易环境：模拟盘\n")
    
    orders = []
    
    for _, row in portfolio.iterrows():
        code = row['code']
        name = row['name']
        weight = row['weight']
        
        # 获取当前价格
        current_price = get_current_price(quote_ctx, code)
        if current_price is None:
            print(f"⚠️ {code} 获取价格失败，跳过")
            continue
        
        # 计算下单数量
        quantity = calculate_order_quantity(weight, current_price, TOTAL_CAPITAL)
        amount = quantity * current_price
        
        print(f"📈 {code} | {name}")
        print(f"   权重：{weight*100:.1f}% | 价格：${current_price:.2f} | 数量：{quantity}股 | 金额：${amount:,.0f}")
        
        # 记录订单（不实际下单，仅展示）
        orders.append({
            'code': code,
            'name': name,
            'weight': weight,
            'price': current_price,
            'quantity': quantity,
            'amount': amount
        })
        
        # 实际下单（模拟环境）
        # 注意：需要用户确认后才执行
        """
        from futu import OpenSecTradeContext, TrdSide, OrderType
        
        trd_ctx = OpenSecTradeContext(host=OPEND_HOST, port=OPEND_PORT)
        ret, data = trd_ctx.place_order(
            price=current_price,
            qty=quantity,
            code=code,
            trd_side=TrdSide.BUY,
            order_type=OrderType.NORMAL,
            trd_env=TRD_ENV
        )
        
        if ret == RET_OK:
            print(f"   ✅ 下单成功")
        else:
            print(f"   ❌ 下单失败：{data}")
        """
    
    # 保存订单计划
    order_file = '/Users/zhaoxf/.openclaw/workspace/agents/stock-system/reports/simulation_orders_20260326.json'
    with open(order_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_capital': TOTAL_CAPITAL,
            'trd_env': 'SIMULATE',
            'orders': orders
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 订单计划已保存到：{order_file}")
    print(f"\n⚠️ 注意：以上仅为订单计划，未实际下单")
    print(f"如需实际下单，请取消脚本中的 place_order 调用注释")


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"🤖 港股量化组合 - 模拟盘建仓")
    print(f"{'='*60}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # 连接 OpenD
    quote_ctx = connect_opend()
    if quote_ctx is None:
        return
    
    try:
        # 加载组合
        portfolio = load_portfolio()
        if portfolio.empty:
            return
        
        # 执行下单
        place_orders(quote_ctx, portfolio)
        
        # 总结
        print(f"\n{'='*60}")
        print(f"✅ 模拟盘建仓计划完成")
        print(f"{'='*60}")
    
    finally:
        quote_ctx.close()


if __name__ == "__main__":
    main()
