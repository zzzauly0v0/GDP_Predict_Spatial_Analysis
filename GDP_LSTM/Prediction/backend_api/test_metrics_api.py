#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试训练指标 API 的简单脚本
"""
import os
import json
import sys

# 添加路径以便导入
current_dir = os.path.dirname(os.path.abspath(__file__))
prediction_dir = os.path.dirname(current_dir)
sys.path.insert(0, prediction_dir)

def test_metrics_file_logic():
    """测试指标文件读取逻辑"""
    print("=== 测试训练指标文件读取逻辑 ===")
    
    # 模拟 PROVINCES 列表
    PROVINCES = ["北京市", "上海市", "广东省"]
    
    models_dir = os.path.join(prediction_dir, 'models')
    print(f"模型目录: {models_dir}")
    
    for province in PROVINCES:
        metrics_file = os.path.join(models_dir, f"{province}_training_metrics.json")
        print(f"\n检查省份: {province}")
        print(f"指标文件路径: {metrics_file}")
        
        if os.path.exists(metrics_file):
            try:
                with open(metrics_file, 'r', encoding='utf-8') as mf:
                    metrics = json.load(mf)
                print(f"✅ 成功读取指标文件")
                print(f"   - 省份: {metrics.get('province', 'N/A')}")
                print(f"   - 保存时间: {metrics.get('saved_at', 'N/A')}")
                print(f"   - 训练轮数: {metrics.get('num_epochs', 'N/A')}")
                if 'metrics' in metrics:
                    train_loss = metrics['metrics'].get('train_loss', [])
                    print(f"   - 训练损失数据点: {len(train_loss)} 个")
                    if train_loss:
                        print(f"   - 最终训练损失: {train_loss[-1]:.4f}")
            except Exception as e:
                print(f"❌ 读取指标文件失败: {e}")
        else:
            print(f"❌ 指标文件不存在")
            # 检查是否有对应的模型文件
            model_pth = os.path.join(models_dir, f"{province}_seq2seq_gdp_model.pth")
            model_onnx = os.path.join(models_dir, f"{province}_seq2seq_gdp_model.onnx")
            if os.path.exists(model_pth) or os.path.exists(model_onnx):
                print(f"   💡 但存在模型文件，需要重新训练以生成指标")

def create_sample_metrics_file():
    """创建一个示例指标文件用于测试"""
    print("\n=== 创建示例指标文件 ===")
    
    models_dir = os.path.join(prediction_dir, 'models')
    os.makedirs(models_dir, exist_ok=True)
    
    sample_metrics = {
        'province': '测试省份',
        'saved_at': '2025-12-07T10:30:00',
        'num_epochs': 5,
        'hyperparams': {
            'input_feature_size': 4,
            'hidden_size': 8,
            'num_layers': 2,
            'predict_steps': 2,
            'window_size': 6,
            'batch_size': 1
        },
        'metrics': {
            'train_loss': [0.5, 0.4, 0.3, 0.25, 0.2],
            'train_mae': [0.3, 0.25, 0.2, 0.18, 0.15],
            'train_mse': [0.5, 0.4, 0.3, 0.25, 0.2],
            'train_mape': [15.0, 12.0, 10.0, 9.0, 8.0],
            'test_loss': [0.52, 0.42, 0.32, 0.27, 0.22],
            'test_mae': [0.32, 0.27, 0.22, 0.20, 0.17],
            'test_mse': [0.52, 0.42, 0.32, 0.27, 0.22],
            'test_mape': [16.0, 13.0, 11.0, 10.0, 9.0]
        }
    }
    
    sample_file = os.path.join(models_dir, "测试省份_training_metrics.json")
    try:
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump(sample_metrics, f, ensure_ascii=False, indent=2)
        print(f"✅ 示例指标文件已创建: {sample_file}")
        return True
    except Exception as e:
        print(f"❌ 创建示例文件失败: {e}")
        return False

if __name__ == "__main__":
    test_metrics_file_logic()
    create_sample_metrics_file()
    print("\n=== 测试完成 ===")
    print("💡 提示:")
    print("1. 如果想要真实的指标文件，需要运行 train.py 重新训练模型")
    print("2. API 路由 /api/gdp/metrics/<province> 已添加到 app.py")
    print("3. 启动服务器后可以访问: http://localhost:5000/api/gdp/metrics/测试省份")