"""
市场状态识别模块
基于沪深 300 指数技术指标和市场广度判断牛市/熊市/震荡市
"""

import pandas as pd
import numpy as np


class MarketStateClassifier:
    """市场状态识别器（优化参数版本）"""
    
    def __init__(self):
        # 优化后的阈值参数
        self.bull_rsi_threshold = 55  # RSI 牛市阈值（优化后：50→55）
        self.bear_rsi_threshold = 35  # RSI 熊市阈值（优化后：40→35）
        self.bull_breadth_threshold = 0.65  # 市场广度牛市阈值（优化后：60%→65%）
        self.bear_breadth_threshold = 0.35  # 市场广度熊市阈值（优化后：40%→35%）
        self.ma250_slope_threshold = 0.001  # MA250 斜率阈值
    
    def calculate_ma250(self, prices):
        """计算 250 日均线"""
        return prices.rolling(window=250).mean()
    
    def calculate_ma250_slope(self, ma250):
        """计算 MA250 的 5 日斜率"""
        return ma250.diff(5)
    
    def classify(self, price_data, rsi, market_breadth):
        """
        判断市场状态
        
        参数:
            price_data: DataFrame，包含'close'列（收盘价）
            rsi: float，当前 RSI(14) 值
            market_breadth: float，市场广度比例（0-1）
        
        返回:
            str: '牛市' / '熊市' / '震荡市'
        """
        # 计算技术指标
        ma250 = self.calculate_ma250(price_data['close'])
        ma250_slope = self.calculate_ma250_slope(ma250)
        current_price = price_data['close'].iloc[-1]
        current_ma250 = ma250.iloc[-1]
        current_slope = ma250_slope.iloc[-1]
        
        # 牛市条件（需同时满足 4 个）
        bull_conditions = [
            current_price > current_ma250,      # 价格>MA250
            current_slope > self.ma250_slope_threshold,  # MA250 斜率>0
            rsi > self.bull_rsi_threshold,      # RSI>55
            market_breadth > self.bull_breadth_threshold  # 市场广度>65%
        ]
        
        # 熊市条件（满足任意 2 个及以上）
        bear_conditions = [
            current_price < current_ma250,      # 价格<MA250
            current_slope < -self.ma250_slope_threshold,  # MA250 斜率<0
            rsi < self.bear_rsi_threshold,      # RSI<35
            market_breadth < self.bear_breadth_threshold  # 市场广度<35%
        ]
        
        # 应用判断规则
        bull_count = sum(bull_conditions)
        bear_count = sum(bear_conditions)
        
        if bull_count == 4:  # 牛市需同时满足 4 个条件
            return '牛市'
        elif bear_count >= 2:  # 熊市满足任意 2 个
            return '熊市'
        else:
            return '震荡市'
    
    def classify_with_details(self, price_data, rsi, market_breadth):
        """
        判断市场状态并返回详细信息
        
        返回:
            dict: {
                'market_state': '牛市'/'熊市'/'震荡市',
                'bull_conditions': list,
                'bear_conditions': list,
                'bull_count': int,
                'bear_count': int
            }
        """
        # 计算技术指标
        ma250 = self.calculate_ma250(price_data['close'])
        ma250_slope = self.calculate_ma250_slope(ma250)
        current_price = price_data['close'].iloc[-1]
        current_ma250 = ma250.iloc[-1]
        current_slope = ma250_slope.iloc[-1]
        
        # 牛市条件
        bull_conditions = [
            ('价格>MA250', current_price > current_ma250, f'{current_price:.2f} > {current_ma250:.2f}'),
            ('MA250 斜率>0', current_slope > self.ma250_slope_threshold, f'{current_slope:.6f} > 0.001'),
            ('RSI>55', rsi > self.bull_rsi_threshold, f'{rsi:.2f} > 55'),
            ('市场广度>65%', market_breadth > self.bull_breadth_threshold, f'{market_breadth:.2%} > 65%')
        ]
        
        # 熊市条件
        bear_conditions = [
            ('价格<MA250', current_price < current_ma250, f'{current_price:.2f} < {current_ma250:.2f}'),
            ('MA250 斜率<0', current_slope < -self.ma250_slope_threshold, f'{current_slope:.6f} < -0.001'),
            ('RSI<35', rsi < self.bear_rsi_threshold, f'{rsi:.2f} < 35'),
            ('市场广度<35%', market_breadth < self.bear_breadth_threshold, f'{market_breadth:.2%} < 35%')
        ]
        
        bull_count = sum(1 for _, satisfied, _ in bull_conditions if satisfied)
        bear_count = sum(1 for _, satisfied, _ in bear_conditions if satisfied)
        
        # 判断市场状态
        if bull_count == 4:
            market_state = '牛市'
        elif bear_count >= 2:
            market_state = '熊市'
        else:
            market_state = '震荡市'
        
        return {
            'market_state': market_state,
            'bull_conditions': bull_conditions,
            'bear_conditions': bear_conditions,
            'bull_count': bull_count,
            'bear_count': bear_count,
            'current_price': current_price,
            'current_ma250': current_ma250,
            'current_rsi': rsi,
            'current_breadth': market_breadth
        }


# 使用示例
if __name__ == '__main__':
    # 示例数据
    dates = pd.date_range('2025-01-01', periods=300, freq='D')
    prices = pd.Series(np.random.randn(300).cumsum() + 3000, index=dates)
    
    classifier = MarketStateClassifier()
    state = classifier.classify(
        price_data=pd.DataFrame({'close': prices}),
        rsi=58.5,
        market_breadth=0.68
    )
    
    print(f"当前市场状态：{state}")
    
    # 详细信息
    details = classifier.classify_with_details(
        price_data=pd.DataFrame({'close': prices}),
        rsi=58.5,
        market_breadth=0.68
    )
    
    print(f"\n详细判断:")
    print(f"  收盘价：{details['current_price']:.2f}")
    print(f"  MA250: {details['current_ma250']:.2f}")
    print(f"  RSI: {details['current_rsi']:.2f}")
    print(f"  市场广度：{details['current_breadth']:.2%}")
    print(f"  牛市条件满足：{details['bull_count']}/4")
    print(f"  熊市条件满足：{details['bear_count']}/4")
