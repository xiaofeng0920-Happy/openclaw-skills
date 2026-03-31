"""
投资组合构建模块
根据市场状态选择股票池和配置权重
"""

import json
import os
from typing import Dict, List, Tuple


class PortfolioConstructor:
    """投资组合构建器"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), 
            '../config/config.yaml'
        )
        
        # 优化后的仓位配置
        self.position_config = {
            '牛市': {
                'stock_pool_size': (160, 170),  # 股票池规模
                'position_ratio': (0.85, 0.95),  # 仓位范围
                'single_stock_max': 0.05,  # 单只股票上限 5%
                'industry_max': 0.20  # 行业集中度上限 20%
            },
            '熊市': {
                'stock_pool_size': (50, 55),
                'position_ratio': (0.40, 0.60),
                'single_stock_max': 0.05,
                'industry_max': 0.20
            },
            '震荡市': {
                'stock_pool_size': (110, 115),
                'position_ratio': (0.65, 0.80),
                'single_stock_max': 0.05,
                'industry_max': 0.20
            }
        }
        
        # 行业权重策略
        self.sector_weights = {
            '牛市': {
                '超配': {'周期': 0.20, '成长': 0.15},  # 超配周期 +20%, 成长 +15%
                '低配': {'防御': -0.10}  # 低配防御 -10%
            },
            '熊市': {
                '超配': {'防御': 0.25, '高股息': 0.15},  # 超配防御 +25%
                '低配': {'周期': -0.20},  # 低配周期 -20%
                '回避': {'高波动': '科技、可选消费'}
            },
            '震荡市': {
                '超配': {'消费': 0.05, '医药': 0.05, '公用事业': 0.05},
                '低配': {'金融': -0.05, '地产': -0.05, '原材料': -0.05}
            }
        }
        
        # 个股筛选规则
        self.stock_selection_rules = {
            '牛市': {
                'beta_min': 1.2,  # 优先高 Beta 股票
                'pe_max': 35,  # PE 放宽至 35
                'revenue_growth_min': 0.20,  # 营收增长>20%
                'momentum_weight': 0.40  # 增加动量因子权重
            },
            '熊市': {
                'debt_ratio_max': 0.40,  # 负债率<40%
                'dividend_yield_min': 0.03,  # 股息率>3%
                'fcf_margin_min': 0.10,  # FCF/营收>10%
                'volatility_max': '行业平均'  # 低波动股票
            },
            '震荡市': {
                'roe_stability': '高',  # ROE 稳定性
                'pe_max': 25,  # PE<25
                'volatility_max': '行业平均',  # 低波动
                'dividend_years_min': 3  # 连续 3 年分红
            }
        }
    
    def construct(self, market_state: str, stock_pools: Dict) -> Dict:
        """
        构建投资组合
        
        参数:
            market_state: '牛市' / '熊市' / '震荡市'
            stock_pools: 股票池字典 {bull: [], bear: [], sideways: []}
        
        返回:
            dict: {
                'stock_pool': list,  # 选定的股票池
                'position_ratio': float,  # 仓位比例
                'sector_weights': dict,  # 行业权重
                'selection_rules': dict  # 选股规则
            }
        """
        if market_state not in self.position_config:
            raise ValueError(f"无效的市场状态：{market_state}")
        
        # 根据市场状态选择股票池
        if market_state == '牛市':
            stock_pool = stock_pools.get('bull', [])
        elif market_state == '熊市':
            stock_pool = stock_pools.get('bear', [])
        else:  # 震荡市
            stock_pool = stock_pools.get('sideways', [])
        
        # 获取仓位配置
        position_config = self.position_config[market_state]
        position_ratio = sum(position_config['position_ratio']) / 2  # 取中值
        
        # 获取行业权重策略
        sector_weight_strategy = self.sector_weights[market_state]
        
        # 获取选股规则
        selection_rules = self.stock_selection_rules[market_state]
        
        return {
            'market_state': market_state,
            'stock_pool': stock_pool,
            'stock_pool_size': len(stock_pool),
            'position_ratio': position_ratio,
            'position_range': position_config['position_ratio'],
            'sector_weights': sector_weight_strategy,
            'selection_rules': selection_rules,
            'risk_control': {
                'single_stock_max': position_config['single_stock_max'],
                'industry_max': position_config['industry_max']
            }
        }
    
    def generate_target_portfolio(self, market_state: str, 
                                   stock_pool: List[Dict],
                                   total_capital: float = 10000000) -> Dict:
        """
        生成目标持仓配置
        
        参数:
            market_state: 市场状态
            stock_pool: 股票池（包含股票信息）
            total_capital: 总资金（默认 1000 万）
        
        返回:
            dict: 目标持仓配置
        """
        config = self.construct(market_state, {market_state: stock_pool})
        
        # 计算单只股票权重（等权重）
        stock_count = len(stock_pool)
        if stock_count == 0:
            return {'error': '股票池为空'}
        
        # 等权重分配
        weight_per_stock = config['position_ratio'] / stock_count
        
        # 生成目标持仓
        target_positions = []
        for stock in stock_pool[:20]:  # 限制最多 20 只
            target_value = total_capital * weight_per_stock
            target_shares = int(target_value / stock.get('price', 1))
            
            target_positions.append({
                'symbol': stock.get('symbol', ''),
                'name': stock.get('name', ''),
                'target_weight': weight_per_stock,
                'target_value': target_value,
                'target_shares': target_shares,
                'current_price': stock.get('price', 0)
            })
        
        return {
            'market_state': market_state,
            'total_capital': total_capital,
            'target_position_ratio': config['position_ratio'],
            'target_stock_count': len(target_positions),
            'positions': target_positions,
            'cash_ratio': 1 - config['position_ratio'],
            'risk_control': config['risk_control']
        }


# 使用示例
if __name__ == '__main__':
    constructor = PortfolioConstructor()
    
    # 模拟股票池数据
    mock_stock_pool = [
        {'symbol': '000858.SZ', 'name': '五粮液', 'price': 150.0, 'roe': 0.156},
        {'symbol': '600519.SH', 'name': '贵州茅台', 'price': 1800.0, 'roe': 0.264},
        {'symbol': '300628.SZ', 'name': '亿联网络', 'price': 45.0, 'roe': 0.222},
        # ... 更多股票
    ]
    
    # 构建牛市组合
    portfolio = constructor.generate_target_portfolio(
        market_state='牛市',
        stock_pool=mock_stock_pool * 10,  # 模拟 177 支
        total_capital=10000000
    )
    
    print(f"市场状态：{portfolio['market_state']}")
    print(f"目标仓位：{portfolio['target_position_ratio']:.1%}")
    print(f"股票数量：{portfolio['target_stock_count']}")
    print(f"现金比例：{portfolio['cash_ratio']:.1%}")
    print(f"\n前 5 大持仓:")
    for pos in portfolio['positions'][:5]:
        print(f"  {pos['symbol']} {pos['name']}: {pos['target_weight']:.2%}")
