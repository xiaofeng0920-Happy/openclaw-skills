"""
富途 OpenD 数据加载器
获取实时行情和交易数据
"""

import yaml
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# 尝试导入富途 API（如果已安装）
try:
    from futu import OpenQuoteContext, OpenHKTradeContext, OpenUSTradeContext, OpenCNTradeContext, RET_OK
    FUTU_AVAILABLE = True
except ImportError:
    FUTU_AVAILABLE = False


class FutuDataLoader:
    """富途 OpenD 数据加载器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化数据加载器
        
        参数:
            config_path: 配置文件路径
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), 
            '../config/futu_config.yaml'
        )
        self.config = self._load_config()
        self.quote_ctx = None
        self.trade_ctx = None
        self.connected = False
    
    def _load_config(self) -> Dict:
        """加载配置文件"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            # 默认配置
            return {
                'connection': {
                    'host': '127.0.0.1',
                    'port': 11111,
                    'timeout': 30
                }
            }
    
    def connect(self) -> Tuple[bool, str]:
        """
        连接到富途 OpenD
        
        返回:
            (success, message): 连接是否成功及消息
        """
        if not FUTU_AVAILABLE:
            return False, "富途 API 未安装"
        
        try:
            host = self.config['connection']['host']
            port = self.config['connection']['port']
            timeout = self.config['connection']['timeout']
            
            # 创建行情上下文
            self.quote_ctx = OpenQuoteContext(host=host, port=port)
            
            # 测试连接
            ret, data = self.quote_ctx.get_market_snapshot('HK.00700')
            
            if ret == RET_OK:
                self.connected = True
                return True, f"成功连接到 {host}:{port}"
            else:
                return False, f"连接失败：{data}"
        
        except Exception as e:
            return False, f"连接异常：{str(e)}"
    
    def disconnect(self):
        """断开连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
            self.quote_ctx = None
        if self.trade_ctx:
            self.trade_ctx.close()
            self.trade_ctx = None
        self.connected = False
    
    def get_realtime_quote(self, stock_codes: List[str]) -> Optional[Dict]:
        """
        获取实时行情
        
        参数:
            stock_codes: 股票代码列表（如 ['HK.00700', 'SH.600519']）
        
        返回:
            行情数据字典
        """
        if not self.connected:
            print("⚠️  未连接到富途 OpenD")
            return None
        
        try:
            ret, data = self.quote_ctx.get_market_snapshot(stock_codes)
            
            if ret == RET_OK:
                return data.to_dict('records')
            else:
                print(f"获取行情失败：{data}")
                return None
        
        except Exception as e:
            print(f"获取行情异常：{str(e)}")
            return None
    
    def subscribe_quote(self, stock_codes: List[str], quote_types: List[str] = None):
        """
        订阅行情
        
        参数:
            stock_codes: 股票代码列表
            quote_types: 订阅类型（默认 ['QUOTE']）
        """
        if not self.connected:
            print("⚠️  未连接到富途 OpenD")
            return
        
        if quote_types is None:
            quote_types = ['QUOTE']
        
        try:
            self.quote_ctx.subscribe(stock_codes, quote_types)
            print(f"✅ 已订阅 {len(stock_codes)} 支股票行情")
        
        except Exception as e:
            print(f"订阅异常：{str(e)}")
    
    def get_stock_pool_prices(self, stock_pool: List[Dict]) -> List[Dict]:
        """
        获取股票池的实时价格
        
        参数:
            stock_pool: 股票池配置（包含 symbol 字段）
        
        返回:
            带价格的股票池数据
        """
        if not self.connected:
            # 返回模拟数据（用于测试）
            print("⚠️  未连接到富途 OpenD，返回模拟数据")
            for stock in stock_pool:
                stock['price'] = stock.get('price', 50.0)
                stock['update_time'] = datetime.now().isoformat()
            return stock_pool
        
        # 转换股票代码格式
        stock_codes = []
        for stock in stock_pool:
            symbol = stock['symbol']
            if '.SZ' in symbol or '.SH' in symbol:
                code = symbol.replace('.SZ', '.SZ').replace('.SH', '.SH')
            else:
                code = f"HK.{symbol}"
            stock_codes.append(code)
        
        # 批量获取（每次最多 300 支）
        updated_stocks = []
        for i in range(0, len(stock_codes), 300):
            batch = stock_codes[i:i+300]
            quotes = self.get_realtime_quote(batch)
            
            if quotes:
                for quote in quotes:
                    # 匹配股票
                    for stock in stock_pool:
                        if stock['symbol'] in quote.get('code', ''):
                            stock['price'] = quote.get('last_price', 0)
                            stock['update_time'] = quote.get('update_time', '')
                            updated_stocks.append(stock)
        
        return updated_stocks
    
    def test_connection(self) -> Dict:
        """
        测试连接
        
        返回:
            测试结果字典
        """
        result = {
            'futu_api_installed': FUTU_AVAILABLE,
            'config_loaded': os.path.exists(self.config_path),
            'connected': False,
            'message': ''
        }
        
        if not FUTU_AVAILABLE:
            result['message'] = '富途 API 未安装'
            return result
        
        success, message = self.connect()
        result['connected'] = success
        result['message'] = message
        
        if success:
            # 测试获取行情
            test_quote = self.get_realtime_quote(['HK.00700'])
            if test_quote:
                result['quote_test'] = '成功'
                result['sample_price'] = test_quote[0].get('last_price', 0)
            else:
                result['quote_test'] = '失败'
        
        return result


# 使用示例
if __name__ == '__main__':
    print("🧪 测试富途 OpenD 数据加载器")
    print("=" * 60)
    
    loader = FutuDataLoader()
    result = loader.test_connection()
    
    print(f"富途 API 已安装：{result['futu_api_installed']}")
    print(f"配置文件存在：{result['config_loaded']}")
    print(f"连接状态：{result['connected']}")
    print(f"消息：{result['message']}")
    
    if result.get('quote_test'):
        print(f"行情测试：{result['quote_test']}")
        print(f"示例价格：{result.get('sample_price', 0)}")
    
    print("=" * 60)
    
    # 断开连接
    loader.disconnect()
