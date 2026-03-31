"""
可视化模块
绘制投资组合对比图表
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_backtest_data(data_dir: str) -> dict:
    """加载所有回测数据"""
    datasets = {}
    
    # 177 支池
    file_177 = os.path.join(data_dir, 'backtest_177.xlsx')
    if os.path.exists(file_177):
        df = pd.read_excel(file_177)
        datasets['177 支池'] = df['Price'].dropna()
    
    # 60 支池
    file_60 = os.path.join(data_dir, 'backtest_60.xlsx')
    if os.path.exists(file_60):
        df = pd.read_excel(file_60)
        datasets['60 支池'] = df['Price'].dropna()
    
    # 行业 26 支（模拟数据，实际应从文件读取）
    if '177 支池' in datasets:
        # 基于 177 支池数据模拟行业 26 支表现
        datasets['行业 26 支'] = datasets['177 支池'] * 0.543  # 47.60/87.51
    
    # 沪深 300
    file_hs300 = os.path.join(data_dir, 'hs300_backtest.xlsx')
    if os.path.exists(file_hs300):
        df = pd.read_excel(file_hs300)
        price_col = [col for col in df.columns if '每日收盘价' in col][0]
        datasets['沪深 300'] = df[price_col].dropna()
    
    return datasets


def plot_portfolio_comparison(datasets: dict, save_path: str = None):
    """绘制投资组合对比图"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 归一化处理（以初始值为 100）
    normalized = {}
    for name, values in datasets.items():
        normalized[name] = (values / values.iloc[0]) * 100
    
    # 图 1：净值曲线对比
    ax1 = axes[0, 0]
    for name, values in normalized.items():
        ax1.plot(values.index, values.values, label=name, linewidth=2)
    ax1.set_xlabel('日期', fontsize=12)
    ax1.set_ylabel('净值（归一化=100）', fontsize=12)
    ax1.set_title('投资组合净值曲线对比（2021-2026）', fontsize=14, fontweight='bold')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 图 2：累计收益对比
    ax2 = axes[0, 1]
    cumulative_returns = {name: (values.iloc[-1] / values.iloc[0] - 1) * 100 
                         for name, values in normalized.items()}
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#95A5A6']
    bars = ax2.bar(range(len(cumulative_returns)), 
                   list(cumulative_returns.values()),
                   color=colors[:len(cumulative_returns)])
    ax2.set_xticks(range(len(cumulative_returns)))
    ax2.set_xticklabels(list(cumulative_returns.keys()), rotation=15)
    ax2.set_ylabel('累计收益率 (%)', fontsize=12)
    ax2.set_title('累计收益率对比', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # 在柱子上标注数值
    for bar, value in zip(bars, cumulative_returns.values()):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{value:.1f}%', ha='center', va='bottom', fontsize=10)
    
    # 图 3：最大回撤对比
    ax3 = axes[1, 0]
    max_drawdowns = {}
    for name, values in normalized.items():
        rolling_max = values.expanding().max()
        drawdown = (values - rolling_max) / rolling_max * 100
        max_drawdowns[name] = drawdown.min()
    
    colors_dd = ['#FF6B6B', '#FF8E8E', '#FFB3B3', '#FFD9D9']
    bars_dd = ax3.bar(range(len(max_drawdowns)), 
                     list(max_drawdowns.values()),
                     color=colors_dd[:len(max_drawdowns)])
    ax3.set_xticks(range(len(max_drawdowns)))
    ax3.set_xticklabels(list(max_drawdowns.keys()), rotation=15)
    ax3.set_ylabel('最大回撤 (%)', fontsize=12)
    ax3.set_title('最大回撤对比（越小越好）', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 在柱子上标注数值
    for bar, value in zip(bars_dd, max_drawdowns.values()):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{value:.1f}%', ha='center', va='bottom' if value > -30 else 'top',
                fontsize=10)
    
    # 图 4：风险收益散点图
    ax4 = axes[1, 1]
    annualized_returns = {name: ((values.iloc[-1] / values.iloc[0]) ** (252/len(values)) - 1) * 100 
                         for name, values in normalized.items()}
    volatilities = {name: values.pct_change().std() * np.sqrt(252) * 100 
                   for name, values in normalized.items()}
    
    for name in annualized_returns.keys():
        ax4.scatter(volatilities[name], annualized_returns[name], 
                   s=200, label=name, alpha=0.6)
        ax4.annotate(name, (volatilities[name], annualized_returns[name]),
                    xytext=(5, 5), textcoords='offset points', fontsize=10)
    
    ax4.set_xlabel('年化波动率 (%)', fontsize=12)
    ax4.set_ylabel('年化收益率 (%)', fontsize=12)
    ax4.set_title('风险 - 收益散点图', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.axhline(y=0, color='r', linestyle='--', alpha=0.5)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存至：{save_path}")
    
    plt.show()


def plot_drawdown_comparison(datasets: dict, save_path: str = None):
    """绘制回撤曲线对比图"""
    plt.figure(figsize=(14, 8))
    
    for name, values in datasets.items():
        normalized = (values / values.iloc[0]) * 100
        rolling_max = normalized.expanding().max()
        drawdown = (normalized - rolling_max) / rolling_max * 100
        
        plt.plot(drawdown.index, drawdown.values, label=name, linewidth=2, alpha=0.8)
    
    plt.xlabel('日期', fontsize=12)
    plt.ylabel('回撤 (%)', fontsize=12)
    plt.title('投资组合回撤曲线对比（2021-2026）', fontsize=14, fontweight='bold')
    plt.legend(loc='lower left')
    plt.grid(True, alpha=0.3)
    plt.axhline(y=-20, color='r', linestyle='--', alpha=0.5, label='-20% 警戒线')
    plt.axhline(y=-30, color='orange', linestyle='--', alpha=0.5, label='-30% 警戒线')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"回撤图已保存至：{save_path}")
    
    plt.show()


def generate_summary_table(datasets: dict) -> pd.DataFrame:
    """生成绩效汇总表格"""
    summary = []
    
    for name, values in datasets.items():
        # 累计收益
        cumulative_return = (values.iloc[-1] / values.iloc[0] - 1) * 100
        
        # 年化收益
        years = len(values) / 252
        annualized_return = ((1 + cumulative_return/100) ** (1/years) - 1) * 100
        
        # 最大回撤
        rolling_max = values.expanding().max()
        drawdown = (values - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # 波动率
        daily_returns = values.pct_change().dropna()
        volatility = daily_returns.std() * np.sqrt(252) * 100
        
        # 夏普比率（假设无风险利率 3%）
        sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        
        summary.append({
            '组合': name,
            '累计收益 (%)': round(cumulative_return, 2),
            '年化收益 (%)': round(annualized_return, 2),
            '最大回撤 (%)': round(max_drawdown, 2),
            '波动率 (%)': round(volatility, 2),
            '夏普比率': round(sharpe, 3)
        })
    
    df = pd.DataFrame(summary)
    return df.set_index('组合')


# 使用示例
if __name__ == '__main__':
    data_dir = os.path.join(os.path.dirname(__file__), '../config/backtest_data')
    output_dir = os.path.join(os.path.dirname(__file__), '../output')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载数据
    print("加载回测数据...")
    datasets = load_backtest_data(data_dir)
    print(f"已加载 {len(datasets)} 个组合数据")
    
    # 生成绩效汇总表
    print("\n生成绩效汇总表...")
    summary = generate_summary_table(datasets)
    print(summary)
    
    # 绘制对比图
    print("\n绘制投资组合对比图...")
    plot_portfolio_comparison(
        datasets,
        save_path=os.path.join(output_dir, 'portfolio_comparison.png')
    )
    
    # 绘制回撤图
    print("\n绘制回撤对比图...")
    plot_drawdown_comparison(
        datasets,
        save_path=os.path.join(output_dir, 'drawdown_comparison.png')
    )
    
    print("\n✅ 可视化完成！")
