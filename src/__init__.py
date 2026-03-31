"""
锋哥量化投资助手 (feng-quant-invest)
基于巴菲特价值投资理念的多因子动态配置策略系统
"""

from .market_state_classifier import MarketStateClassifier
from .portfolio_constructor import PortfolioConstructor
from .backtest_engine import DynamicAllocationBacktest
from .performance_analyzer import PerformanceAnalyzer
from .visualize import (
    load_backtest_data,
    plot_portfolio_comparison,
    plot_drawdown_comparison,
    generate_summary_table
)
from .data_loader import FutuDataLoader

__version__ = '1.0.0'
__author__ = '小巴 (锋哥量化投资助手)'

__all__ = [
    'MarketStateClassifier',
    'PortfolioConstructor',
    'DynamicAllocationBacktest',
    'PerformanceAnalyzer',
    'FutuDataLoader',
    'load_backtest_data',
    'plot_portfolio_comparison',
    'plot_drawdown_comparison',
    'generate_summary_table'
]
