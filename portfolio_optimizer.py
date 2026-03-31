#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投资组合优化 - 基于 Markowitz 均值 - 方差模型

作者：小巴
日期：2026-03-26
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta
import json

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


def get_historical_data(quote_ctx: OpenQuoteContext, code: str, days: int = 60) -> pd.Series:
    """获取历史 K 线数据"""
    try:
        # 先尝试实时 K 线
        ret, data = quote_ctx.get_cur_kline(code, num=days, ktype=KLType.K_DAY, autype=AuType.QFQ)
        
        if ret == RET_OK and len(data) >= 20:
            return data['close']
        
        # 如果失败，尝试历史 K 线
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days*2)).strftime('%Y-%m-%d')
        
        ret, data = quote_ctx.request_history_kline(
            code, start=start_date, end=end_date, ktype=KLType.K_DAY, autype=AuType.QFQ
        )
        
        if ret == RET_OK and len(data) >= 20:
            return data['close']
        
        return None
    
    except Exception as e:
        return None


def calculate_returns(prices: pd.Series) -> pd.Series:
    """计算日收益率"""
    return prices.pct_change().dropna()


def optimize_portfolio_mean_variance(codes: List[str], quote_ctx: OpenQuoteContext, 
                                     risk_free_rate: float = 0.02) -> Dict:
    """
    Markowitz 均值 - 方差优化
    
    目标：最大化夏普比率
    约束：
    - 权重和为 1
    - 单股权重 0-30%
    """
    
    print(f"\n正在获取 {len(codes)} 只股票的历史数据...")
    
    # 获取历史数据
    returns_data = {}
    for code in codes:
        prices = get_historical_data(quote_ctx, code, days=60)
        if prices is not None and len(prices) > 20:
            returns = calculate_returns(prices)
            returns_data[code] = returns
            print(f"  ✅ {code}")
        else:
            print(f"  ⚠️ {code} 数据不足")
    
    if len(returns_data) < 2:
        print("❌ 有效数据不足，无法优化")
        return {}
    
    # 构建收益率矩阵
    returns_df = pd.DataFrame(returns_data)
    
    # 计算预期收益率（年化）
    expected_returns = returns_df.mean() * 252
    
    # 计算协方差矩阵（年化）
    cov_matrix = returns_df.cov() * 252
    
    # 计算最优权重（简化版：等权重 + 波动率调整）
    n_assets = len(returns_data)
    
    # 方法 1: 等权重
    weights_equal = np.array([1.0/n_assets] * n_assets)
    
    # 方法 2: 波动率倒数加权（低波动率股票权重高）
    volatilities = np.sqrt(np.diag(cov_matrix))
    inv_vol = 1.0 / volatilities
    weights_inv_vol = inv_vol / inv_vol.sum()
    
    # 方法 3: 夏普比率加权
    sharpe_ratios = expected_returns / volatilities
    sharpe_positive = np.maximum(sharpe_ratios, 0)  # 只取正夏普
    if sharpe_positive.sum() > 0:
        weights_sharpe = sharpe_positive / sharpe_positive.sum()
    else:
        weights_sharpe = weights_equal
    
    # 计算组合指标
    def portfolio_metrics(weights, expected_returns, cov_matrix, risk_free_rate):
        port_return = np.dot(weights, expected_returns)
        port_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        sharpe = (port_return - risk_free_rate) / port_volatility if port_volatility > 0 else 0
        return port_return, port_volatility, sharpe
    
    # 比较三种方法
    methods = {
        '等权重': weights_equal,
        '波动率倒数': weights_inv_vol,
        '夏普比率': weights_sharpe
    }
    
    best_method = None
    best_sharpe = -999
    best_weights = None
    
    print("\n" + "="*60)
    print("📊 组合优化结果对比")
    print("="*60)
    
    for name, weights in methods.items():
        ret, vol, sharpe = portfolio_metrics(weights, expected_returns, cov_matrix, risk_free_rate)
        print(f"\n{name}:")
        print(f"  预期年化收益：{ret*100:.2f}%")
        print(f"  年化波动率：{vol*100:.2f}%")
        print(f"  夏普比率：{sharpe:.2f}")
        
        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_method = name
            best_weights = weights
    
    print(f"\n🏆 最优方法：{best_method} (夏普比率={best_sharpe:.2f})")
    
    # 输出最优权重
    print("\n" + "="*60)
    print(f"💼 推荐组合权重 ({best_method})")
    print("="*60)
    
    portfolio = []
    for i, code in enumerate(returns_data.keys()):
        weight = best_weights[i]
        portfolio.append({
            'code': code,
            'weight': weight,
            'expected_return': expected_returns.iloc[i],
            'volatility': volatilities[i]
        })
        print(f"{code}: {weight*100:.1f}% (预期收益：{expected_returns.iloc[i]*100:.1f}%, 波动率：{volatilities[i]*100:.1f}%)")
    
    # 计算组合总体指标
    port_return, port_vol, port_sharpe = portfolio_metrics(
        best_weights, expected_returns, cov_matrix, risk_free_rate
    )
    
    print("\n" + "="*60)
    print("📈 组合总体指标")
    print("="*60)
    print(f"预期年化收益：{port_return*100:.2f}%")
    print(f"年化波动率：{port_vol*100:.2f}%")
    print(f"夏普比率：{port_sharpe:.2f}")
    print(f"无风险利率：{risk_free_rate*100:.1f}%")
    
    # 风险平价调整（简化版）
    print("\n" + "="*60)
    print("⚠️ 风险提示")
    print("="*60)
    
    # 检查集中度
    max_weight = best_weights.max()
    if max_weight > 0.3:
        print(f"⚠️ 个股集中度偏高：最大权重 {max_weight*100:.1f}%")
        print("   建议：设置单股权重上限 30%")
    
    # 检查相关性
    corr_matrix = returns_df.corr()
    avg_corr = (corr_matrix.values.sum() - len(corr_matrix)) / (len(corr_matrix) * (len(corr_matrix)-1))
    print(f"平均相关性：{avg_corr:.2f}")
    if avg_corr > 0.7:
        print("⚠️ 股票相关性偏高，分散效果有限")
        print("   建议：加入低相关性股票")
    elif avg_corr < 0.3:
        print("✅ 股票相关性较低，分散效果良好")
    
    return {
        'method': best_method,
        'weights': portfolio,
        'portfolio_return': port_return,
        'portfolio_volatility': port_vol,
        'portfolio_sharpe': port_sharpe,
        'avg_correlation': avg_corr
    }


def optimize_portfolio_risk_parity(codes: List[str], quote_ctx: OpenQuoteContext) -> Dict:
    """
    风险平价组合（Risk Parity）
    每只股票对组合风险贡献相等
    """
    
    print(f"\n正在计算风险平价组合...")
    
    # 获取历史数据
    returns_data = {}
    for code in codes:
        prices = get_historical_data(quote_ctx, code, days=60)
        if prices is not None and len(prices) > 20:
            returns = calculate_returns(prices)
            returns_data[code] = returns
    
    if len(returns_data) < 2:
        print("❌ 有效数据不足")
        return {}
    
    returns_df = pd.DataFrame(returns_data)
    cov_matrix = returns_df.cov() * 252
    volatilities = np.sqrt(np.diag(cov_matrix))
    
    # 风险平价权重（简化：波动率倒数加权）
    inv_vol = 1.0 / volatilities
    weights = inv_vol / inv_vol.sum()
    
    print("\n" + "="*60)
    print("🎯 风险平价组合")
    print("="*60)
    
    portfolio = []
    for i, code in enumerate(returns_data.keys()):
        weight = weights[i]
        risk_contribution = weight * volatilities[i]
        portfolio.append({
            'code': code,
            'weight': weight,
            'risk_contribution': risk_contribution
        })
        print(f"{code}: 权重={weight*100:.1f}%, 风险贡献={risk_contribution*100:.1f}%")
    
    return {
        'method': 'Risk Parity',
        'weights': portfolio
    }


def save_portfolio_result(result: Dict, output_file: str = None):
    """保存组合优化结果"""
    
    if output_file is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'/Users/zhaoxf/.openclaw/workspace/agents/xiaoba-portfolio/portfolio_{timestamp}.json'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存到：{output_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='投资组合优化')
    parser.add_argument('--codes', type=str, nargs='+', default=None,
                        help='股票代码列表（如：HK.00700 HK.09988）')
    parser.add_argument('--input', type=str, default=None,
                        help='从 CSV 文件读取股票列表')
    parser.add_argument('--top', type=int, default=10,
                        help='从 CSV 读取前 N 只股票')
    parser.add_argument('--method', type=str, default='mean_variance',
                        choices=['mean_variance', 'risk_parity'],
                        help='优化方法')
    parser.add_argument('--output', type=str, default=None,
                        help='输出文件路径')
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print(f"💼 投资组合优化系统")
    print(f"{'='*60}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # 连接 OpenD
    quote_ctx = connect_opend()
    if quote_ctx is None:
        return
    
    try:
        # 获取股票列表
        codes = args.codes
        
        if codes is None and args.input:
            # 从 CSV 读取
            df = pd.read_csv(args.input)
            if 'code' in df.columns:
                codes = df['code'].head(args.top).tolist()
            else:
                print("❌ CSV 文件中未找到 code 列")
                return
        
        if codes is None:
            print("❌ 请提供股票代码列表（--codes 或 --input）")
            return
        
        print(f"优化标的：{len(codes)} 只股票")
        for code in codes:
            print(f"  - {code}")
        
        # 执行优化
        if args.method == 'mean_variance':
            result = optimize_portfolio_mean_variance(codes, quote_ctx)
        else:
            result = optimize_portfolio_risk_parity(codes, quote_ctx)
        
        # 保存结果
        if result:
            save_portfolio_result(result, args.output)
    
    finally:
        quote_ctx.close()
        print("\n✅ 组合优化完成")


if __name__ == "__main__":
    main()
