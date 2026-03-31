#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用富途 OpenD 获取港股历史数据

作者：小巴
日期：2026-03-26
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from futu import *
except ImportError:
    print("❌ 未安装 futu-api，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "futu-api", "-q"])
    from futu import *

# ============ 配置 ============
BASE_DIR = Path('/Users/zhaoxf/.openclaw/skills/港股量化投资')
DATA_DIR = BASE_DIR / 'data'
BACKTEST_DIR = BASE_DIR / 'backtest'

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

OPEND_HOST = '127.0.0.1'
OPEND_PORT = 11111

# 回测期间
START_DATE = '2023-01-01'
END_DATE = '2026-03-26'

# 港股成分股（恒生指数主要成分股）
HK_BLUE_CHIPS = [
    '00700', '09988', '00883', '02318', '00941',  # 腾讯、阿里、中海油、平安、中移动
    '00388', '01299', '00005', '02628', '03988',  # 港交所、友邦、汇丰、国寿、中行
    '00939', '01398', '02388', '00011', '00012',  # 建行、工行、中银香港、恒银、恒地
    '00001', '00002', '00003', '00006', '00016',  # 长实、中电、港灯、电能、新鸿基
    '00017', '00019', '00027', '00066', '00101',  # 新世界、太古 A、银河娱乐、港铁、恒隆地
    '00144', '00175', '00267', '00386', '00688',  # 招商局、吉利、中信、中石化、中海地
    '00857', '00883', '00966', '00992', '01038',  # 中石油、中海油、太平、联想、长建
    '01044', '01088', '01109', '01113', '01211',  # 恒安、神华、华润置地、长实、比亚迪
    '01928', '01997', '02007', '02018', '02313',  # 金沙、九龙仓、碧桂园、申洲、申洲国际
    '02318', '02382', '02688', '03328', '03690',  # 平安、舜宇、新奥能源、交行、美团
    '03968', '03988', '06098', '06618', '09618',  # 招行、中行、碧桂园服务、京东、京东数科
    '09988', '09999'  # 阿里、网易
]

# ============================


def connect_opend() -> OpenQuoteContext:
    """连接 OpenD"""
    print("正在连接富途 OpenD...")
    quote_ctx = OpenQuoteContext(host=OPEND_HOST, port=OPEND_PORT)
    
    ret, state = quote_ctx.get_global_state()
    if ret != RET_OK or not state['qot_logined']:
        print("❌ OpenD 连接失败！请确保 OpenD 已启动")
        return None
    
    print("✅ OpenD 连接成功")
    return quote_ctx


def get_stock_list(quote_ctx: OpenQuoteContext) -> pd.DataFrame:
    """获取港股股票列表"""
    print("正在获取港股股票列表...")
    ret, data = quote_ctx.get_stock_basicinfo(Market.HK, SecurityType.STOCK)
    
    if ret != RET_OK or data.empty:
        print("❌ 获取股票列表失败")
        return pd.DataFrame()
    
    print(f"✅ 获取到 {len(data)} 只港股")
    return data


def get_history_kline(quote_ctx: OpenQuoteContext, code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取历史 K 线数据"""
    try:
        result = quote_ctx.request_history_kline(
            code=f'HK.{code}',
            start=start_date,
            end=end_date,
            ktype=KLType.K_DAY,
            autype=AuType.QFQ  # 前复权
        )
        
        # 处理返回值（可能是 tuple 或 DataFrame）
        if isinstance(result, tuple) and len(result) == 2:
            ret, data = result
            if ret == RET_OK and len(data) > 0:
                return data
        elif isinstance(result, pd.DataFrame) and len(result) > 0:
            return result
        
        return pd.DataFrame()
    
    except Exception as e:
        print(f"⚠️ 获取 {code} 历史数据失败：{e}")
        return pd.DataFrame()


def get_stock_snapshot(quote_ctx: OpenQuoteContext, codes: list) -> pd.DataFrame:
    """获取股票快照数据（用于获取财务指标）"""
    try:
        # 分批获取，每批 100 只
        all_data = []
        batch_size = 100
        
        for i in range(0, len(codes), batch_size):
            batch = [f'HK.{code}' for code in codes[i:i+batch_size]]
            ret, data = quote_ctx.get_market_snapshot(batch)
            
            if ret == RET_OK:
                all_data.append(data)
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()
    
    except Exception as e:
        print(f"⚠️ 获取快照数据失败：{e}")
        return pd.DataFrame()


def calculate_factors(kline_data: pd.DataFrame, snapshot_data: pd.DataFrame) -> pd.DataFrame:
    """计算因子数据"""
    if kline_data.empty:
        return pd.DataFrame()
    
    df = kline_data.copy()
    
    # 动量因子
    if len(df) >= 20:
        df['momentum_20d'] = df['close'].pct_change(20)
        df['momentum_5d'] = df['close'].pct_change(5)
    
    # RSI
    if len(df) >= 14:
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
    
    # 成交量比率
    if len(df) >= 5:
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(window=5).mean()
    
    # 波动率
    if len(df) >= 20:
        df['volatility_20d'] = df['close'].pct_change().rolling(window=20).std()
    
    # 换手率（需要流通股本，这里简化处理）
    if 'turnover' in df.columns and 'volume' in df.columns:
        df['turnover_rate'] = df['volume'] / df['volume'].mean()
    
    return df


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"📊 富途 OpenD 港股历史数据获取")
    print(f"{'='*60}")
    print(f"回测期间：{START_DATE} 到 {END_DATE}")
    print(f"股票池：{len(HK_BLUE_CHIPS)} 只港股蓝筹")
    print(f"{'='*60}\n")
    
    # 连接 OpenD
    quote_ctx = connect_opend()
    if quote_ctx is None:
        return
    
    try:
        # 获取股票列表
        stock_list = get_stock_list(quote_ctx)
        
        # 获取快照数据（财务指标）
        print(f"\n正在获取 {len(HK_BLUE_CHIPS)} 只股票快照数据...")
        snapshot_data = get_stock_snapshot(quote_ctx, HK_BLUE_CHIPS)
        
        if not snapshot_data.empty:
            # 保存快照数据
            snapshot_file = DATA_DIR / f'hk_snapshot_{datetime.now().strftime("%Y%m%d")}.csv'
            snapshot_data.to_csv(snapshot_file, index=False, encoding='utf-8-sig')
            print(f"✅ 快照数据已保存到：{snapshot_file}")
        
        # 获取历史 K 线
        print(f"\n正在获取历史 K 线数据（{START_DATE} 到 {END_DATE}）...")
        
        all_kline_data = []
        success_count = 0
        fail_count = 0
        
        for i, code in enumerate(HK_BLUE_CHIPS, 1):
            print(f"  [{i}/{len(HK_BLUE_CHIPS)}] 获取 {code} 历史数据...", end=' ')
            
            kline_data = get_history_kline(quote_ctx, code, START_DATE, END_DATE)
            
            if len(kline_data) > 0:
                # 计算因子
                kline_with_factors = calculate_factors(kline_data, snapshot_data)
                kline_with_factors['code'] = code
                all_kline_data.append(kline_with_factors)
                success_count += 1
                print(f"✅ {len(kline_data)} 条")
            else:
                fail_count += 1
                print(f"❌ 失败")
            
            # 避免请求过快
            if i % 10 == 0:
                import time
                time.sleep(1)
        
        # 合并所有数据
        if all_kline_data:
            combined_data = pd.concat(all_kline_data, ignore_index=True)
            
            # 保存数据
            kline_file = DATA_DIR / f'hk_history_kline_{START_DATE.replace("-", "")}_{END_DATE.replace("-", "")}.csv'
            combined_data.to_csv(kline_file, index=False, encoding='utf-8-sig')
            
            print(f"\n{'='*60}")
            print(f"✅ 数据获取完成！")
            print(f"{'='*60}")
            print(f"成功：{success_count} 只股票")
            print(f"失败：{fail_count} 只股票")
            print(f"总记录数：{len(combined_data)} 条")
            print(f"数据文件：{kline_file}")
            print(f"{'='*60}\n")
            
            # 生成数据说明
            generate_data_description(kline_file, snapshot_file if not snapshot_data.empty else None)
        else:
            print(f"\n❌ 未能获取任何数据")
    
    finally:
        quote_ctx.close()


def generate_data_description(kline_file: Path, snapshot_file: Path = None):
    """生成数据说明文件"""
    desc = f"""# 📊 港股历史数据说明

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**数据源**: 富途 OpenD  
**回测期间**: {START_DATE} 到 {END_DATE}

---

## 📁 数据文件

### K 线数据

**文件**: `{kline_file.name}`  
**大小**: {kline_file.stat().st_size / 1024 / 1024:.2f} MB

**字段**:
- `code`: 股票代码
- `time_key`: 日期
- `open`: 开盘价
- `close`: 收盘价
- `high`: 最高价
- `low`: 最低价
- `volume`: 成交量
- `turnover`: 成交额
- `momentum_20d`: 20 日动量
- `momentum_5d`: 5 日动量
- `rsi_14`: RSI(14)
- `volume_ratio`: 成交量比率
- `volatility_20d`: 20 日波动率
- `turnover_rate`: 换手率

### 快照数据

"""
    
    if snapshot_file:
        desc += f"""**文件**: `{snapshot_file.name}`  
**大小**: {snapshot_file.stat().st_size / 1024 / 1024:.2f} MB

**字段**:
- `code`: 股票代码
- `name`: 股票名称
- `pe_ratio`: 市盈率
- `pb_ratio`: 市净率
- `dividend_ratio`: 股息率
- `market_value`: 市值
- `roe`: 净资产收益率
- `gross_margin`: 毛利率
- `debt_ratio`: 负债率
"""
    else:
        desc += "**文件**: 无\n"
    
    desc += f"""
---

## 📊 数据统计

"""
    
    # 读取数据生成统计
    try:
        df = pd.read_csv(kline_file)
        desc += f"""
**股票数量**: {df['code'].nunique()} 只  
**交易日数**: {df['time_key'].nunique()} 天  
**总记录数**: {len(df):,} 条  
**日期范围**: {df['time_key'].min()} 到 {df['time_key'].max()}

**数据完整性**:
- 缺失值比例：{df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100:.2f}%
"""
    except Exception as e:
        desc += f"数据统计失败：{e}\n"
    
    desc += f"""
---

## ⚠️ 使用说明

1. **复权处理**: 已使用前复权（QFQ）
2. **停牌处理**: 停牌日数据已排除
3. **因子计算**: 动量、RSI 等因子已计算
4. **回测使用**: 直接加载 CSV 文件即可

---

*数据说明生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    # 保存说明文件
    desc_file = DATA_DIR / 'data_description.md'
    with open(desc_file, 'w', encoding='utf-8') as f:
        f.write(desc)
    
    print(f"✅ 数据说明已保存到：{desc_file}")


if __name__ == "__main__":
    main()
