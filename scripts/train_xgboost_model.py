#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XGBoost 机器学习模型训练（替代 LightGBM）

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
    import xgboost as xgb
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    import joblib
except ImportError as e:
    print(f"❌ 缺少依赖：{e}")
    print("正在安装...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "xgboost", "scikit-learn", "-q"])
    import xgboost as xgb
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    import joblib

# ============ 配置 ============
BASE_DIR = Path('/Users/zhaoxf/.openclaw/skills/港股量化投资')
DATA_DIR = BASE_DIR / 'data'
MODEL_DIR = BASE_DIR / 'models'

MODEL_DIR.mkdir(parents=True, exist_ok=True)

# ============================


def prepare_training_data(data_file: str, target_period: int = 20) -> pd.DataFrame:
    """准备训练数据"""
    print(f"正在加载数据：{data_file}")
    
    df = pd.read_csv(data_file)
    
    all_data = []
    
    for code in df['code'].unique():
        stock_data = df[df['code'] == code].sort_values('date').copy()
        
        if len(stock_data) < target_period + 60:
            continue
        
        # 计算未来 N 日收益率
        stock_data['future_return'] = stock_data['close'].shift(-target_period) / stock_data['close'] - 1
        stock_data = stock_data.iloc[:-target_period]
        stock_data = stock_data.dropna()
        
        if len(stock_data) > 0:
            all_data.append(stock_data)
    
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        print(f"✅ 训练数据：{len(result):,} 条样本")
        return result
    else:
        print("❌ 无法准备训练数据")
        return pd.DataFrame()


def select_features(df: pd.DataFrame) -> list:
    """选择特征列"""
    feature_cols = []
    
    # 动量因子
    for col in ['momentum_20d', 'momentum_5d', 'rsi_14']:
        if col in df.columns:
            feature_cols.append(col)
    
    # 波动率
    if 'volatility_20d' in df.columns:
        feature_cols.append('volatility_20d')
    
    # 成交量
    for col in ['volume_ratio', 'turnover_rate']:
        if col in df.columns:
            feature_cols.append(col)
    
    # 涨跌幅
    if 'change_percent' in df.columns:
        feature_cols.append('change_percent')
    
    print(f"✅ 选择 {len(feature_cols)} 个特征：{feature_cols}")
    return feature_cols


def train_xgboost_model(df: pd.DataFrame, feature_cols: list):
    """训练 XGBoost 模型"""
    
    print(f"\n{'='*60}")
    print(f"训练 XGBoost 模型")
    print(f"{'='*60}")
    print(f"样本数：{len(df):,}")
    print(f"特征数：{len(feature_cols)}")
    
    X = df[feature_cols].values
    y = df['future_return'].values
    
    # 时间序列交叉验证
    tscv = TimeSeriesSplit(n_splits=5)
    
    # XGBoost 参数
    params = {
        'objective': 'reg:squarederror',
        'max_depth': 6,
        'learning_rate': 0.05,
        'n_estimators': 1000,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 3,
        'early_stopping_rounds': 50,
        'verbosity': 0
    }
    
    cv_scores = []
    feature_importance = np.zeros(len(feature_cols))
    
    print("\n5 折交叉验证...")
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        model = xgb.XGBRegressor(**params)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
        
        y_pred = model.predict(X_val)
        
        mse = mean_squared_error(y_val, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)
        
        cv_scores.append({'fold': fold, 'rmse': rmse, 'mae': mae, 'r2': r2})
        feature_importance += model.feature_importances_
        
        print(f"  Fold {fold}: RMSE={rmse:.4f}, R²={r2:.4f}")
    
    avg_rmse = np.mean([s['rmse'] for s in cv_scores])
    avg_r2 = np.mean([s['r2'] for s in cv_scores])
    
    print(f"\n{'='*60}")
    print(f"平均：RMSE={avg_rmse:.4f}, R²={avg_r2:.4f}")
    print(f"{'='*60}")
    
    # 特征重要性
    feature_importance /= 5
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': feature_importance
    }).sort_values('importance', ascending=False)
    
    print(f"\n特征重要性 Top 5:")
    for _, row in importance_df.head(5).iterrows():
        print(f"  {row['feature']}: {row['importance']:.2f}")
    
    # 训练最终模型
    print(f"\n训练最终模型...")
    final_model = xgb.XGBRegressor(**{k: v for k, v in params.items() if k != 'early_stopping_rounds'})
    final_model.fit(X, y)
    
    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_file = MODEL_DIR / f'xgboost_model_{timestamp}.pkl'
    joblib.dump(final_model, model_file)
    
    config = {
        'model_file': str(model_file),
        'feature_cols': feature_cols,
        'target_period': 20,
        'cv_scores': {'avg_rmse': avg_rmse, 'avg_r2': avg_r2},
        'feature_importance': importance_df.to_dict('records'),
        'training_date': datetime.now().isoformat(),
        'training_samples': len(df)
    }
    
    import json
    config_file = MODEL_DIR / f'xgboost_config_{timestamp}.json'
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 模型：{model_file.name}")
    print(f"✅ 配置：{config_file.name}")
    
    return final_model, config


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"🤖 XGBoost 模型训练")
    print(f"{'='*60}\n")
    
    data_files = list(DATA_DIR.glob('hk_history_akshare_*.csv'))
    if not data_files:
        print("❌ 未找到数据文件")
        return
    
    data_file = max(data_files, key=lambda p: p.stat().st_mtime)
    print(f"数据：{data_file.name}")
    
    train_data = prepare_training_data(str(data_file))
    if train_data.empty:
        return
    
    feature_cols = select_features(train_data)
    if not feature_cols:
        return
    
    model, config = train_xgboost_model(train_data, feature_cols)
    
    print(f"\n{'='*60}")
    print(f"✅ XGBoost 训练完成！")
    print(f"样本：{config['training_samples']:,} | R²: {config['cv_scores']['avg_r2']:.4f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
