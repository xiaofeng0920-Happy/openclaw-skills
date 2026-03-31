"""
回测引擎主模块
执行历史回测模拟
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class DynamicAllocationBacktest:
    """动态配置回测引擎"""
    
    def __init__(self, start_date: str, end_date: str, 
                 initial_capital: float = 10000000):
        """
        初始化回测引擎
        
        参数:
            start_date: 开始日期 'YYYY-MM-DD'
            end_date: 结束日期 'YYYY-MM-DD'
            initial_capital: 初始资金（默认 1000 万）
        """
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.initial_capital = initial_capital
        self.portfolio_value = initial_capital
        self.positions = {}
        self.cash = initial_capital
        self.daily_values = []
        self.rebalance_dates = []
        self.transaction_cost = 0.001  # 交易成本 0.1%
    
    def get_rebalance_dates(self) -> List[pd.Timestamp]:
        """获取季度调仓日期（每季度最后交易日）"""
        dates = pd.date_range(self.start_date, self.end_date, freq='Q')
        self.rebalance_dates = dates.tolist()
        return self.rebalance_dates
    
    def classify_market_state(self, date: pd.Timestamp, 
                              market_data: pd.DataFrame) -> str:
        """
        判断指定日期的市场状态
        
        简化版本，实际应使用 market_state_classifier 模块
        """
        if date not in market_data.index:
            return '震荡市'
        
        row = market_data.loc[date]
        
        # 简化判断逻辑
        if row.get('RSI', 50) > 55 and row.get('breadth', 0.5) > 0.65:
            return '牛市'
        elif row.get('RSI', 50) < 35 and row.get('breadth', 0.5) < 0.35:
            return '熊市'
        else:
            return '震荡市'
    
    def construct_portfolio(self, market_state: str, 
                           stock_data: pd.DataFrame) -> Dict:
        """
        构建投资组合
        
        简化版本，实际应使用 portfolio_constructor 模块
        """
        config = {
            '牛市': {'position': 0.95, 'stocks': 170},
            '熊市': {'position': 0.60, 'stocks': 55},
            '震荡市': {'position': 0.80, 'stocks': 115}
        }
        
        cfg = config[market_state]
        
        # 简单选择 ROE 最高的股票
        top_stocks = stock_data.nlargest(cfg['stocks'], 'ROE')
        
        # 等权重分配
        weight_per_stock = cfg['position'] / len(top_stocks)
        
        return {
            'stocks': top_stocks.to_dict('records'),
            'position_ratio': cfg['position'],
            'weights': {s['symbol']: weight_per_stock 
                       for s in top_stocks.to_dict('records')}
        }
    
    def rebalance_portfolio(self, portfolio: Dict, 
                           current_prices: pd.Series):
        """
        执行调仓
        
        参数:
            portfolio: 目标投资组合
            current_prices: 当前价格
        """
        target_value = self.portfolio_value * portfolio['position_ratio']
        
        # 计算每只股票的目标持仓
        new_positions = {}
        for symbol, weight in portfolio['weights'].items():
            target_stock_value = target_value * weight
            if symbol in current_prices.index:
                price = current_prices[symbol]
                shares = int(target_stock_value / price)
                if shares > 0:
                    new_positions[symbol] = {
                        'shares': shares,
                        'price': price,
                        'value': shares * price
                    }
        
        # 计算交易成本
        old_value = sum(p['value'] for p in self.positions.values())
        new_value = sum(p['value'] for p in new_positions.values())
        turnover = abs(new_value - old_value)
        cost = turnover * self.transaction_cost
        
        # 更新持仓和现金
        self.positions = new_positions
        self.cash = self.portfolio_value - sum(p['value'] for p in self.positions.values()) - cost
    
    def update_portfolio_value(self, date: pd.Timestamp, 
                              stock_data: pd.DataFrame):
        """更新组合价值"""
        total_value = 0
        
        for symbol, position in self.positions.items():
            if symbol in stock_data.columns:
                current_price = stock_data[symbol].loc[date]
                position['price'] = current_price
                position['value'] = position['shares'] * current_price
                total_value += position['value']
        
        self.portfolio_value = total_value + self.cash
        self.daily_values.append({
            'date': date,
            'value': self.portfolio_value,
            'cash': self.cash,
            'position_value': total_value
        })
    
    def run_backtest(self, market_data: pd.DataFrame, 
                    stock_data: pd.DataFrame) -> Dict:
        """
        运行完整回测
        
        参数:
            market_data: 市场数据（包含 RSI、广度等）
            stock_data: 个股数据（包含价格、ROE 等）
        
        返回:
            dict: 回测结果
        """
        print(f"开始回测：{self.start_date.date()} 至 {self.end_date.date()}")
        print(f"初始资金：{self.initial_capital:,.0f}")
        
        # 获取调仓日期
        rebalance_dates = self.get_rebalance_dates()
        print(f"调仓次数：{len(rebalance_dates)}")
        
        # 初始化
        current_date = self.start_date
        trading_days = stock_data.index
        
        while current_date <= self.end_date:
            # 检查是否需要调仓
            if current_date in rebalance_dates:
                print(f"\n[{current_date.date()}] 执行季度调仓")
                market_state = self.classify_market_state(current_date, market_data)
                print(f"  市场状态：{market_state}")
                
                portfolio = self.construct_portfolio(market_state, stock_data)
                self.rebalance_portfolio(portfolio, 
                                        stock_data.loc[current_date])
            
            # 更新组合价值
            if current_date in trading_days:
                self.update_portfolio_value(current_date, stock_data)
            
            current_date += timedelta(days=1)
        
        # 生成报告
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """生成回测报告"""
        if not self.daily_values:
            return {'error': '无回测数据'}
        
        df = pd.DataFrame(self.daily_values)
        df.set_index('date', inplace=True)
        
        # 计算绩效指标
        initial = self.initial_capital
        final = df['value'].iloc[-1]
        cumulative_return = (final / initial - 1) * 100
        
        # 年化收益率
        years = len(df) / 252
        annualized_return = ((final / initial) ** (1 / years) - 1) * 100
        
        # 最大回撤
        rolling_max = df['value'].expanding().max()
        drawdown = (df['value'] - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        # 日收益率
        daily_returns = df['value'].pct_change().dropna()
        
        # 夏普比率（假设无风险利率 3%）
        sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
        
        return {
            'start_date': self.start_date.date(),
            'end_date': self.end_date.date(),
            'initial_capital': initial,
            'final_value': final,
            'cumulative_return': cumulative_return,
            'annualized_return': annualized_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'total_trading_days': len(df),
            'rebalance_count': len(self.rebalance_dates),
            'daily_values': df
        }


# 使用示例
if __name__ == '__main__':
    # 创建模拟数据
    dates = pd.date_range('2021-01-01', '2026-03-28', freq='D')
    
    # 模拟市场数据
    market_data = pd.DataFrame({
        'RSI': np.random.randn(len(dates)) * 10 + 50,
        'breadth': np.random.randn(len(dates)) * 0.1 + 0.5
    }, index=dates)
    
    # 模拟股票数据
    stock_data = pd.DataFrame({
        '000858.SZ': np.random.randn(len(dates)).cumsum() + 100,
        '600519.SH': np.random.randn(len(dates)).cumsum() + 1500
    }, index=dates)
    stock_data['ROE'] = [0.15, 0.26]  # 模拟 ROE
    
    # 运行回测
    backtest = DynamicAllocationBacktest(
        start_date='2021-01-01',
        end_date='2026-03-28',
        initial_capital=10000000
    )
    
    result = backtest.run_backtest(market_data, stock_data)
    
    print(f"\n回测结果:")
    print(f"  累计收益：{result['cumulative_return']:.2f}%")
    print(f"  年化收益：{result['annualized_return']:.2f}%")
    print(f"  最大回撤：{result['max_drawdown']:.2f}%")
    print(f"  夏普比率：{result['sharpe_ratio']:.3f}")
