#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LightGBM 机器学习模型训练

使用历史数据训练股票收益率预测模型

作者：小巴
日期：2026-03-26
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np

# 尝试安装依赖
try:
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    import joblib
    import lightgbm as lgb
except ImportError as e:
    print(f"❌ 缺少依赖：{e}")
    print("正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "lightgbm", "scikit-learn", "joblib", "-q"])
    import lightgbm as lgb
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    import joblib

# ============ 配置 ============
BASE_DIR = Path('/Users/zhaoxf/.openclaw/skills/港股量化投资')
DATA_DIR = BASE_DIR / 'data'
MODEL_DIR = BASE_DIR / 'models'

# 确保目录存在
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ============================


def prepare_training_data(data_file: str, target_period: int = 20) -> pd.DataFrame:
    """
    准备训练数据
    
    特征：当前因子值
    标签：未来 N 日收益率
    """
    print(f"正在加载数据：{data_file}")
    
    df = pd.read_csv(data_file)
    
    # 按股票代码分组处理
    all_data = []
    
    for code in df['code'].unique():
        stock_data = df[df['code'] == code].sort_values('date').copy()
        
        if len(stock_data) < target_period + 60:  # 至少需要 target_period+60 天数据
            continue
        
        # 计算未来 N 日收益率（标签）
        stock_data['future_return'] = stock_data['close'].shift(-target_period) / stock_data['close'] - 1
        
        # 移除未来数据
        stock_data = stock_data.iloc[:-target_period]
        
        # 移除缺失值
        stock_data = stock_data.dropna()
        
        if len(stock_data) > 0:
            all_data.append(stock_data)
    
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        print(f"✅ 训练数据准备完成：{len(result)} 条样本")
        return result
    else:
        print("❌ 无法准备训练数据")
        return pd.DataFrame()


def select_features(df: pd.DataFrame) -> list:
    """选择特征列"""
    feature_cols = [
        # 动量因子
        'momentum_20d', 'momentum_5d', 'rsi_14',
        # 价值因子（需要从财务数据获取，这里用技术面替代）
        'volatility_20d',
        # 质量因子（需要从财务数据获取，这里用技术面替代）
        'volume_ratio', 'turnover_rate',
        # 情绪因子
        'change_percent' if 'change_percent' in df.columns else None
    ]
    
    # 过滤掉不存在的列
    feature_cols = [col for col in feature_cols if col is not None and col in df.columns]
    
    print(f"✅ 选择 {len(feature_cols)} 个特征：{feature_cols}")
    return feature_cols


def train_lightgbm_model(df: pd.DataFrame, feature_cols: list):
    """训练 LightGBM 模型"""
    
    print(f"\n{'='*60}")
    print(f"训练 LightGBM 模型")
    print(f"{'='*60}")
    print(f"样本数：{len(df):,}")
    print(f"特征数：{len(feature_cols)}")
    
    # 准备数据
    X = df[feature_cols].values
    y = df['future_return'].values
    
    # 时间序列分割（避免未来函数）
    tscv = TimeSeriesSplit(n_splits=5)
    
    # LightGBM 参数
    params = {
        'objective': 'regression',
        'metric': 'mse',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'n_estimators': 1000,
        'early_stopping_rounds': 50
    }
    
    # 交叉验证
    cv_scores = []
    feature_importance = np.zeros(len(feature_cols))
    
    print("\n开始 5 折交叉验证...")
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        # 创建模型
        model = lgb.LGBMRegressor(**params)
        
        # 训练
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
        )
        
        # 预测
        y_pred = model.predict(X_val)
        
        # 评估
        mse = mean_squared_error(y_val, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        
        cv_scores.append({
            'fold': fold,
            'rmse': rmse,
            'mae': mae,
            'r2': r2
        })
        
        feature_importance += model.feature_importances_
        
        print(f"  Fold {fold}: RMSE={rmse:.4f}, MAE={mae:.4f}, R²={r2:.4f}")
    
    # 平均分数
    avg_rmse = np.mean([s['rmse'] for s in cv_scores])
    avg_mae = np.mean([s['mae'] for s in cv_scores])
    avg_r2 = np.mean([s['r2'] for s in cv_scores])
    
    print(f"\n{'='*60}")
    print(f"平均表现:")
    print(f"  RMSE: {avg_rmse:.4f}")
    print(f"  MAE: {avg_mae:.4f}")
    print(f"  R²: {avg_r2:.4f}")
    print(f"{'='*60}")
    
    # 特征重要性
    feature_importance /= 5
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': feature_importance
    }).sort_values('importance', ascending=False)
    
    print(f"\n特征重要性 Top 5:")
    for i, row in importance_df.head(5).iterrows():
        print(f"  {row['feature']}: {row['importance']:.2f}")
    
    # 用全部数据训练最终模型
    print(f"\n用全部数据训练最终模型...")
    final_model = lgb.LGBMRegressor(**{k: v for k, v in params.items() if k != 'early_stopping_rounds'})
    final_model.fit(X, y)
    
    # 保存模型
    model_file = MODEL_DIR / f'lightgbm_model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pkl'
    joblib.dump(final_model, model_file)
    
    # 保存配置
    config = {
        'model_file': str(model_file),
        'feature_cols': feature_cols,
        'target_period': 20,
        'cv_scores': {
            'avg_rmse': avg_rmse,
            'avg_mae': avg_mae,
            'avg_r2': avg_r2
        },
        'feature_importance': importance_df.to_dict('records'),
        'training_date': datetime.now().isoformat(),
        'training_samples': len(df)
    }
    
    config_file = MODEL_DIR / f'lightgbm_config_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    import json
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 模型已保存到：{model_file}")
    print(f"✅ 配置已保存到：{config_file}")
    
    return final_model, config


def predict_with_model(model, feature_cols: list, current_data: pd.DataFrame) -> pd.DataFrame:
    """使用模型预测"""
    
    print(f"正在预测...")
    
    # 准备特征
    X = current_data[feature_cols].values
    
    # 预测
    predictions = model.predict(X)
    
    # 添加到数据
    current_data['predicted_return'] = predictions
    
    # 排序
    current_data = current_data.sort_values('predicted_return', ascending=False)
    
    print(f"✅ 预测完成，Top 5 股票:")
    for i, (_, row) in enumerate(current_data.head(5).iterrows(), 1):
        print(f"  {i}. {row['code']} ({row.get('name', 'N/A')}): {row['predicted_return']*100:.2f}%")
    
    return current_data


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"🤖 LightGBM 模型训练")
    print(f"{'='*60}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # 查找数据文件
    data_files = list(DATA_DIR.glob('hk_history_akshare_*.csv'))
    
    if not data_files:
        print("❌ 未找到历史数据文件")
        return
    
    # 使用最新的数据文件
    data_file = max(data_files, key=lambda p: p.stat().st_mtime)
    print(f"使用数据文件：{data_file.name}")
    
    # 准备训练数据
    train_data = prepare_training_data(str(data_file), target_period=20)
    
    if train_data.empty:
        return
    
    # 选择特征
    feature_cols = select_features(train_data)
    
    if not feature_cols:
        print("❌ 没有可用特征")
        return
    
    # 训练模型
    model, config = train_lightgbm_model(train_data, feature_cols)
    
    print(f"\n{'='*60}")
    print(f"✅ LightGBM 模型训练完成！")
    print(f"{'='*60}")
    print(f"模型文件：{config['model_file']}")
    print(f"特征数：{len(feature_cols)}")
    print(f"训练样本：{config['training_samples']:,}")
    print(f"平均 R²: {config['cv_scores']['avg_r2']:.4f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
