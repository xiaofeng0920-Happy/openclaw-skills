#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
港股量化组合 - 实盘建仓脚本（小资金测试）

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
TOTAL_CAPITAL = 100000  # 10 万港元实盘测试资金
TRD_ENV = TrdEnv.REAL  # 实盘交易

# ============================


def connect_opend() -> tuple:
    """连接 OpenD"""
    quote_ctx = OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    ret, state = quote_ctx.get_global_state()
    
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！")
        return None, None
    
    print("✅ OpenD 行情连接成功")
    
    # 创建交易上下文
    trd_ctx = OpenSecTradeContext(host=OPEND_HOST, port=OPEND_PORT)
    print("✅ 交易上下文创建成功")
    
    return quote_ctx, trd_ctx


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


def check_trade_unlock(trd_ctx) -> bool:
    """检查交易是否已解锁"""
    ret, data = trd_ctx.get_acc_list()
    if ret == RET_OK:
        print("✅ 交易账户已解锁")
        return True
    else:
        print("❌ 交易未解锁，请在 OpenD GUI 界面点击「解锁交易」")
        return False


def place_real_orders(quote_ctx: OpenQuoteContext, trd_ctx, portfolio: pd.DataFrame):
    """执行实盘下单"""
    
    print(f"\n{'='*60}")
    print(f"🔴 开始实盘建仓")
    print(f"{'='*60}")
    print(f"总资金：{TOTAL_CAPITAL:,.0f} HKD")
    print(f"交易环境：实盘")
    print(f"{'='*60}\n")
    
    # 检查交易解锁
    if not check_trade_unlock(trd_ctx):
        print("\n⚠️ 请先在 OpenD GUI 界面解锁交易，然后重新运行脚本")
        return
    
    orders_placed = []
    total_used = 0
    
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
        
        # 确认订单
        print(f"📈 {code} | {name}")
        print(f"   权重：{weight*100:.1f}% | 价格：${current_price:.2f} | 数量：{quantity}股 | 金额：${amount:,.0f}")
        
        # 用户确认
        confirm = input(f"   确认下单？(y/n/skip): ").strip().lower()
        
        if confirm == 'y':
            # 实盘下单
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
                orders_placed.append({
                    'code': code,
                    'name': name,
                    'quantity': quantity,
                    'price': current_price,
                    'amount': amount,
                    'status': 'success'
                })
                total_used += amount
            else:
                print(f"   ❌ 下单失败：{data}")
                orders_placed.append({
                    'code': code,
                    'name': name,
                    'quantity': quantity,
                    'price': current_price,
                    'amount': amount,
                    'status': 'failed',
                    'error': str(data)
                })
        elif confirm == 'skip':
            print(f"   ⏭️ 跳过")
        else:
            print(f"   ❌ 已取消")
    
    # 总结
    print(f"\n{'='*60}")
    print(f"📊 实盘建仓总结")
    print(f"{'='*60}")
    print(f"总资金：{TOTAL_CAPITAL:,.0f} HKD")
    print(f"已使用：${total_used:,.0f} ({total_used/TOTAL_CAPITAL*100:.1f}%)")
    print(f"剩余：${TOTAL_CAPITAL - total_used:,.0f}")
    print(f"成功：{len([o for o in orders_placed if o['status'] == 'success'])} 只")
    print(f"失败：{len([o for o in orders_placed if o['status'] == 'failed'])} 只")
    print(f"跳过：{len([o for o in orders_placed if o['status'] == 'skipped'])} 只")
    
    # 保存订单记录
    order_file = f'/Users/zhaoxf/.openclaw/workspace/agents/stock-system/reports/real_orders_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(order_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_capital': TOTAL_CAPITAL,
            'trd_env': 'REAL',
            'orders': orders_placed,
            'total_used': total_used
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 订单记录已保存到：{order_file}")


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"🔴 港股量化组合 - 实盘建仓（小资金测试）")
    print(f"{'='*60}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"资金：{TOTAL_CAPITAL:,.0f} HKD")
    print(f"{'='*60}\n")
    
    # 连接 OpenD
    quote_ctx, trd_ctx = connect_opend()
    
    if quote_ctx is None or trd_ctx is None:
        return
    
    try:
        # 加载组合
        portfolio = load_portfolio()
        if portfolio.empty:
            return
        
        # 执行下单
        place_real_orders(quote_ctx, trd_ctx, portfolio)
        
        # 总结
        print(f"\n{'='*60}")
        print(f"✅ 实盘建仓完成")
        print(f"{'='*60}")
    
    finally:
        quote_ctx.close()
        trd_ctx.close()


if __name__ == "__main__":
    main()
