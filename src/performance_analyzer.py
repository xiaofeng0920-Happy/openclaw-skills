"""
绩效分析模块
计算投资组合的各项绩效指标
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


class PerformanceAnalyzer:
    """绩效分析器"""
    
    def __init__(self, risk_free_rate: float = 0.03):
        """
        初始化绩效分析器
        
        参数:
            risk_free_rate: 无风险利率（默认 3%）
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_returns(self, values: pd.Series) -> pd.Series:
        """计算日收益率"""
        return values.pct_change().dropna()
    
    def calculate_cumulative_return(self, values: pd.Series) -> float:
        """计算累计收益率"""
        return (values.iloc[-1] / values.iloc[0] - 1) * 100
    
    def calculate_annualized_return(self, values: pd.Series) -> float:
        """计算年化收益率"""
        years = len(values) / 252
        total_return = values.iloc[-1] / values.iloc[0] - 1
        return ((1 + total_return) ** (1 / years) - 1) * 100
    
    def calculate_max_drawdown(self, values: pd.Series) -> float:
        """计算最大回撤"""
        rolling_max = values.expanding().max()
        drawdown = (values - rolling_max) / rolling_max * 100
        return drawdown.min()
    
    def calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        """计算夏普比率"""
        excess_returns = returns - self.risk_free_rate / 252
        return (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)
    
    def calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """计算索提诺比率（只考虑下行波动）"""
        excess_returns = returns - self.risk_free_rate / 252
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_std = downside_returns.std()
        return (excess_returns.mean() / downside_std) * np.sqrt(252)
    
    def calculate_calmar_ratio(self, annualized_return: float, 
                               max_drawdown: float) -> float:
        """计算卡尔玛比率（年化收益/最大回撤）"""
        if max_drawdown == 0:
            return float('inf')
        return annualized_return / abs(max_drawdown)
    
    def calculate_alpha_beta(self, returns: pd.Series, 
                            benchmark_returns: pd.Series) -> Dict:
        """
        计算阿尔法和贝塔
        
        返回:
            dict: {'alpha': float, 'beta': float}
        """
        # 对齐数据
        aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(aligned) < 2:
            return {'alpha': np.nan, 'beta': np.nan}
        
        returns_aligned = aligned.iloc[:, 0]
        benchmark_aligned = aligned.iloc[:, 1]
        
        # 计算协方差和方差
        covariance = returns_aligned.cov(benchmark_aligned)
        benchmark_variance = benchmark_aligned.var()
        
        if benchmark_variance == 0:
            return {'alpha': np.nan, 'beta': np.nan}
        
        beta = covariance / benchmark_variance
        
        # 阿尔法 = 组合收益 - 贝塔 * 基准收益
        alpha = returns_aligned.mean() - beta * benchmark_aligned.mean()
        
        # 年化处理
        alpha_annualized = alpha * 252
        
        return {
            'alpha': alpha_annualized,
            'beta': beta
        }
    
    def calculate_win_rate(self, returns: pd.Series) -> float:
        """计算胜率（上涨交易日占比）"""
        winning_days = (returns > 0).sum()
        total_days = len(returns)
        return (winning_days / total_days) * 100 if total_days > 0 else 0
    
    def calculate_profit_loss_ratio(self, returns: pd.Series) -> float:
        """计算盈亏比"""
        winning_returns = returns[returns > 0]
        losing_returns = returns[returns < 0]
        
        if len(losing_returns) == 0:
            return float('inf')
        
        avg_win = winning_returns.mean()
        avg_loss = abs(losing_returns.mean())
        
        return avg_win / avg_loss if avg_loss > 0 else float('inf')
    
    def calculate_turnover_rate(self, positions_history: list) -> float:
        """计算换手率"""
        if len(positions_history) < 2:
            return 0
        
        total_turnover = 0
        for i in range(1, len(positions_history)):
            old_positions = set(positions_history[i-1].keys())
            new_positions = set(positions_history[i].keys())
            
            # 计算调仓比例
            changed = len(old_positions - new_positions) + len(new_positions - old_positions)
            total = len(old_positions | new_positions)
            
            if total > 0:
                total_turnover += changed / total
        
        return (total_turnover / (len(positions_history) - 1)) * 100
    
    def calculate(self, portfolio_values: pd.Series, 
                 benchmark_values: Optional[pd.Series] = None) -> Dict:
        """
        计算完整的绩效指标
        
        参数:
            portfolio_values: 组合价值时间序列
            benchmark_values: 基准价值时间序列（可选）
        
        返回:
            dict: 完整的绩效指标
        """
        returns = self.calculate_returns(portfolio_values)
        
        # 基础指标
        cumulative_return = self.calculate_cumulative_return(portfolio_values)
        annualized_return = self.calculate_annualized_return(portfolio_values)
        max_drawdown = self.calculate_max_drawdown(portfolio_values)
        sharpe_ratio = self.calculate_sharpe_ratio(returns)
        sortino_ratio = self.calculate_sortino_ratio(returns)
        calmar_ratio = self.calculate_calmar_ratio(annualized_return, max_drawdown)
        
        # 胜率
        win_rate = self.calculate_win_rate(returns)
        profit_loss_ratio = self.calculate_profit_loss_ratio(returns)
        
        result = {
            '累计收益率 (%)': round(cumulative_return, 2),
            '年化收益率 (%)': round(annualized_return, 2),
            '最大回撤 (%)': round(max_drawdown, 2),
            '夏普比率': round(sharpe_ratio, 3),
            '索提诺比率': round(sortino_ratio, 3),
            '卡尔玛比率': round(calmar_ratio, 3),
            '胜率 (%)': round(win_rate, 2),
            '盈亏比': round(profit_loss_ratio, 2),
            '交易日数': len(returns),
            '年化波动率 (%)': round(returns.std() * np.sqrt(252) * 100, 2)
        }
        
        # 如果有基准数据，计算阿尔法和贝塔
        if benchmark_values is not None:
            benchmark_returns = self.calculate_returns(benchmark_values)
            alpha_beta = self.calculate_alpha_beta(returns, benchmark_returns)
            
            # 计算基准对比
            benchmark_cumulative = self.calculate_cumulative_return(benchmark_values)
            benchmark_annualized = self.calculate_annualized_return(benchmark_values)
            
            result.update({
                '阿尔法 (%)': round(alpha_beta['alpha'], 2),
                '贝塔': round(alpha_beta['beta'], 2),
                '基准累计收益 (%)': round(benchmark_cumulative, 2),
                '基准年化收益 (%)': round(benchmark_annualized, 2),
                '超额收益 (%)': round(cumulative_return - benchmark_cumulative, 2)
            })
        
        return result
    
    def generate_report(self, portfolio_values: pd.Series,
                       benchmark_values: Optional[pd.Series] = None,
                       title: str = "投资组合绩效报告") -> str:
        """
        生成文本格式的绩效报告
        
        返回:
            str: 格式化的绩效报告
        """
        metrics = self.calculate(portfolio_values, benchmark_values)
        
        report = f"""
{'='*60}
{title}
{'='*60}

📈 收益指标
  累计收益率：    {metrics['累计收益率 (%)']:>8.2f}%
  年化收益率：    {metrics['年化收益率 (%)']:>8.2f}%
  超额收益：      {metrics.get('超额收益 (%)', 'N/A'):>8}

📉 风险指标
  最大回撤：      {metrics['最大回撤 (%)']:>8.2f}%
  年化波动率：    {metrics['年化波动率 (%)']:>8.2f}%

⚖️ 风险调整收益
  夏普比率：      {metrics['夏普比率']:>8.3f}
  索提诺比率：    {metrics['索提诺比率']:>8.3f}
  卡尔玛比率：    {metrics['卡尔玛比率']:>8.3f}

🎯 交易统计
  胜率：          {metrics['胜率 (%)']:>8.2f}%
  盈亏比：        {metrics['盈亏比']:>8.2f}
  交易日数：      {metrics['交易日数']:>8d}

📊 市场对比
  阿尔法：        {metrics.get('阿尔法 (%)', 'N/A'):>8}
  贝塔：          {metrics.get('贝塔', 'N/A'):>8}

{'='*60}
"""
        return report


# 使用示例
if __name__ == '__main__':
    # 创建模拟数据
    dates = pd.date_range('2021-01-01', '2026-03-28', freq='D')
    
    # 模拟组合价值（年化 12%）
    portfolio_values = pd.Series(
        10000000 * np.cumprod(1 + np.random.randn(len(dates)) * 0.02 + 0.12/252),
        index=dates
    )
    
    # 模拟基准价值（年化 6%）
    benchmark_values = pd.Series(
        10000000 * np.cumprod(1 + np.random.randn(len(dates)) * 0.015 + 0.06/252),
        index=dates
    )
    
    # 计算绩效
    analyzer = PerformanceAnalyzer()
    report = analyzer.generate_report(
        portfolio_values, 
        benchmark_values,
        title="锋哥量化策略绩效报告（2021-2026）"
    )
    
    print(report)
