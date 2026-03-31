#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器学习增强选股系统

结合 XGBoost 预测 + 因子评分

作者：小巴
日期：2026-03-26
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import joblib
import json

# ============ 配置 ============
BASE_DIR = Path('/Users/zhaoxf/.openclaw/skills/港股量化投资')
DATA_DIR = BASE_DIR / 'data'
MODEL_DIR = BASE_DIR / 'models'

# ============================


def load_latest_model():
    """加载最新的 XGBoost 模型"""
    model_files = list(MODEL_DIR.glob('xgboost_model_*.pkl'))
    
    if not model_files:
        print("❌ 未找到 XGBoost 模型")
        return None, None
    
    latest_model = max(model_files, key=lambda p: p.stat().st_mtime)
    config_file = MODEL_DIR / latest_model.name.replace('.pkl', '.json')
    
    print(f"加载模型：{latest_model.name}")
    model = joblib.load(latest_model)
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = None
    
    return model, config


def prepare_features(df: pd.DataFrame, feature_cols: list) -> np.ndarray:
    """准备特征数据"""
    X = df[feature_cols].values
    
    # 处理缺失值
    X = np.nan_to_num(X, nan=0.0)
    
    return X


def predict_with_ml(model, config, current_data: pd.DataFrame) -> pd.DataFrame:
    """使用机器学习预测"""
    
    if config is None:
        print("❌ 模型配置缺失")
        return current_data
    
    feature_cols = config['feature_cols']
    
    print(f"使用特征：{feature_cols}")
    
    # 按股票分组预测
    all_predictions = []
    
    for code in current_data['code'].unique():
        stock_data = current_data[current_data['code'] == code].iloc[-1:].copy()
        
        # 准备特征
        X = prepare_features(stock_data, feature_cols)
        
        # 预测
        pred = model.predict(X)[0]
        
        stock_data['ml_predicted_return'] = pred
        all_predictions.append(stock_data)
    
    result = pd.concat(all_predictions, ignore_index=True)
    result = result.sort_values('ml_predicted_return', ascending=False)
    
    print(f"✅ ML 预测完成，Top 5:")
    for i, (_, row) in enumerate(result.head(5).iterrows(), 1):
        print(f"  {i}. {row['code']}: {row['ml_predicted_return']*100:.2f}%")
    
    return result


def combine_with_factor_score(df: pd.DataFrame, ml_weight: float = 0.3) -> pd.DataFrame:
    """
    结合 ML 预测和因子评分
    
    最终评分 = ML 预测 * ml_weight + 因子评分 * (1 - ml_weight)
    """
    
    # 归一化 ML 预测
    ml_pred = df['ml_predicted_return']
    ml_norm = (ml_pred - ml_pred.min()) / (ml_pred.max() - ml_pred.min() + 1e-8)
    
    # 归一化因子评分（如果有的话）
    if 'total_score' in df.columns:
        factor_score = df['total_score']
        factor_norm = (factor_score - factor_score.min()) / (factor_score.max() - factor_score.min() + 1e-8)
    else:
        # 如果没有因子评分，只用 ML
        factor_norm = pd.Series(0.5, index=df.index)
    
    # 综合评分
    df['combined_score'] = ml_norm * ml_weight + factor_norm * (1 - ml_weight)
    df = df.sort_values('combined_score', ascending=False)
    
    print(f"\n✅ 综合评分完成（ML 权重 {ml_weight*100:.0f}%）")
    print(f"Top 5:")
    for i, (_, row) in enumerate(df.head(5).iterrows(), 1):
        ml_ret = row['ml_predicted_return'] * 100
        combined = row['combined_score']
        print(f"  {i}. {row['code']}: ML 预测 {ml_ret:+.2f}% | 综合评分 {combined:.3f}")
    
    return df


def main():
    """主函数"""
    print(f"\n{'='*60}")
    print(f"🤖 机器学习增强选股")
    print(f"{'='*60}")
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")
    
    # 加载模型
    model, config = load_latest_model()
    
    if model is None:
        return
    
    # 加载当前数据
    data_files = list(DATA_DIR.glob('hk_history_akshare_*.csv'))
    
    if not data_files:
        print("❌ 未找到数据文件")
        return
    
    data_file = max(data_files, key=lambda p: p.stat().st_mtime)
    print(f"数据：{data_file.name}")
    
    df = pd.read_csv(data_file)
    
    # 获取最新交易日数据
    latest_date = df['date'].max()
    current_data = df[df['date'] == latest_date].copy()
    
    print(f"当前数据：{len(current_data)} 只股票（{latest_date}）")
    
    # ML 预测
    predicted = predict_with_ml(model, config, current_data)
    
    # 结合因子评分
    combined = combine_with_factor_score(predicted, ml_weight=0.3)
    
    # 保存结果
    output_file = DATA_DIR / f'ml_enhanced_selection_{latest_date}.csv'
    combined.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\n✅ 结果已保存：{output_file.name}")
    print(f"\n{'='*60}")
    print(f"✅ 机器学习增强选股完成！")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
