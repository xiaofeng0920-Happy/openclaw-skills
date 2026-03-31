#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 AkShare 获取港股历史数据

作者：小巴
日期：2026-03-26
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# 尝试安装 akshare
try:
    import akshare as ak
except ImportError:
    print("❌ 未安装 akshare，正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "akshare", "-q"])
    import akshare as ak

# ============ 配置 ============
BASE_DIR = Path('/Users/zhaoxf/.openclaw/skills/港股量化投资')
DATA_DIR = BASE_DIR / 'data'
BACKTEST_DIR = BASE_DIR / 'backtest'

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)
BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

# 回测期间（近 5 年）
START_DATE = '20210101'
END_DATE = '20260326'

# 港股成分股（恒生指数主要成分股）
HK_BLUE_CHIPS = [
    '00700', '09988', '00883', '02318', '00941',  # 腾讯、阿里、中海油、平安、中移动
    '00388', '01299', '00005', '02628', '03988',  # 港交所、友邦、汇丰、国寿、中行
    '00939', '01398', '02388', '00011', '00012',  # 建行、工行、中银香港、恒银、恒地
    '00001', '00002', '00003', '00006', '00016',  # 长实、中电、港灯、电能、新鸿基
    '00017', '00019', '00027', '00066', '00101',  # 新世界、太古 A、银河娱乐、港铁、恒隆地
    '00144', '00175', '00267', '00386', '00688',  # 招商局、吉利、中信、中石化、中海地
    '00857', '00966', '00992', '01038', '01044',  # 中石油、太平、联想、长建、恒安
    '01088', '01109', '01113', '01211', '01928',  # 神华、华润置地、长实、比亚迪、金沙
    '01997', '02007', '02018', '02313', '02382',  # 九龙仓、碧桂园、申洲、舜宇
    '02688', '03328', '03690', '03968', '06098',  # 新奥能源、交行、美团、招行、碧桂园服务
    '06618', '09618', '09988', '09999'  # 京东、京东数科、阿里、网易
]

# ============================


def get_hk_daily(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """获取港股日线数据"""
    try:
        # AkShare 港股数据接口
        df = ak.stock_hk_daily(symbol=stock_code, adjust="qfq")
        
        if df.empty:
            return pd.DataFrame()
        
        # 筛选日期范围
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y%m%d')
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        
        if df.empty:
            return pd.DataFrame()
        
        # 添加股票代码
        df['code'] = stock_code
        
        return df
    
    except Exception as e:
        print(f"⚠️ 获取 {stock_code} 数据失败：{e}")
        return pd.DataFrame()


def calculate_factors(df: pd.DataFrame) -> pd.DataFrame:
    """计算因子数据"""
    if df.empty:
        return df
    
    data = df.copy()
    
    # 动量因子
    if len(data) >= 20:
        data['momentum_20d'] = data['close'].pct_change(20)
        data['momentum_5d'] = data['close'].pct_change(5)
    
    # RSI (14 日)
    if len(data) >= 14:
        delta = data['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['rsi_14'] = 100 - (100 / (1 + rs))
    
    # 成交量比率
    if len(data) >= 5:
        data['volume_ratio'] = data['volume'] / data['volume'].rolling(window=5).mean()
    
    # 波动率
    if len(data) >= 20:
        data['volatility_20d'] = data['close'].pct_change().rolling(window=20).std()
    
    # 换手率（简化处理）
    data['turnover_rate'] = data['volume'] / data['volume'].rolling(window=20).mean() * 100
    
    return data


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"📊 AkShare 港股历史数据获取")
    print(f"{'='*60}")
    print(f"回测期间：{START_DATE} 到 {END_DATE}")
    print(f"股票池：{len(HK_BLUE_CHIPS)} 只港股蓝筹")
    print(f"{'='*60}\n")
    
    # 获取历史数据
    print(f"正在获取历史 K 线数据（{START_DATE} 到 {END_DATE}）...\n")
    
    all_data = []
    success_count = 0
    fail_count = 0
    
    for i, code in enumerate(HK_BLUE_CHIPS, 1):
        print(f"[{i}/{len(HK_BLUE_CHIPS)}] 获取 {code} 数据...", end=' ')
        
        df = get_hk_daily(code, START_DATE, END_DATE)
        
        if len(df) > 0:
            # 计算因子
            df_with_factors = calculate_factors(df)
            all_data.append(df_with_factors)
            success_count += 1
            print(f"✅ {len(df)} 条")
        else:
            fail_count += 1
            print(f"❌ 无数据")
        
        # 避免请求过快
        if i % 10 == 0:
            import time
            time.sleep(1)
    
    # 合并所有数据
    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        
        # 保存数据
        kline_file = DATA_DIR / f'hk_history_akshare_{START_DATE}_{END_DATE}.csv'
        combined_data.to_csv(kline_file, index=False, encoding='utf-8-sig')
        
        print(f"\n{'='*60}")
        print(f"✅ 数据获取完成！")
        print(f"{'='*60}")
        print(f"成功：{success_count} 只股票")
        print(f"失败：{fail_count} 只股票")
        print(f"总记录数：{len(combined_data):,} 条")
        print(f"数据文件：{kline_file}")
        print(f"文件大小：{kline_file.stat().st_size / 1024 / 1024:.2f} MB")
        print(f"{'='*60}\n")
        
        # 生成数据说明
        generate_data_description(kline_file)
        
        # 运行回测
        print("\n正在运行回测...")
        run_backtest(combined_data)
    else:
        print(f"\n❌ 未能获取任何数据")


def generate_data_description(data_file: Path):
    """生成数据说明文件"""
    desc = f"""# 📊 港股历史数据说明（AkShare）

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**数据源**: AkShare  
**回测期间**: {START_DATE} 到 {END_DATE}

---

## 📁 数据文件

**文件**: `{data_file.name}`  
**大小**: {data_file.stat().st_size / 1024 / 1024:.2f} MB

**字段**:
- `code`: 股票代码
- `date`: 日期
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `turnover`: 成交额
- `amplitude`: 振幅
- `change_percent`: 涨跌幅
- `change_amount`: 涨跌额
- `momentum_20d`: 20 日动量
- `momentum_5d`: 5 日动量
- `rsi_14`: RSI(14)
- `volume_ratio`: 成交量比率
- `volatility_20d`: 20 日波动率
- `turnover_rate`: 换手率

---

## 📊 数据统计

"""
    
    try:
        df = pd.read_csv(data_file)
        desc += f"""
**股票数量**: {df['code'].nunique()} 只  
**交易日数**: {df['date'].nunique()} 天  
**总记录数**: {len(df):,} 条  
**日期范围**: {df['date'].min()} 到 {df['date'].max()}

**数据完整性**:
- 缺失值比例：{df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100:.2f}%
"""
    except Exception as e:
        desc += f"数据统计失败：{e}\n"
    
    desc += f"""
---

## ⚠️ 使用说明

1. **复权处理**: 已使用前复权（QFQ）
2. **因子计算**: 动量、RSI 等因子已计算
3. **回测使用**: 直接加载 CSV 文件即可

---

*数据说明生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""
    
    # 保存说明文件
    desc_file = DATA_DIR / 'data_description_akshare.md'
    with open(desc_file, 'w', encoding='utf-8') as f:
        f.write(desc)
    
    print(f"✅ 数据说明已保存到：{desc_file}")


def run_backtest(data: pd.DataFrame):
    """运行回测"""
    from backtest_multi_strategy import STRATEGIES, backtest_strategy, generate_comparison_report
    
    # 回测每个策略
    results_list = []
    for strategy_name, strategy_config in STRATEGIES.items():
        if strategy_config['market'] == 'HK':  # 只回测港股策略
            results = backtest_strategy(data, strategy_name, strategy_config)
            results_list.append(results)
    
    # 生成对比报告
    if results_list:
        generate_comparison_report(results_list)


if __name__ == "__main__":
    main()
