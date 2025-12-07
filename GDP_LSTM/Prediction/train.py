import data_setup
import os
import torch
import model_builder
import utils
from torch import nn
import engine
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import numpy as np
import onnx
import json
import datetime
import sys

# ---超参数定义--- #
INPUT_FEATURE_SIZE = 4     #输入特征
OUTPUT_FEATURE_SIZE = 1    #输出GDP预测值
HIDDEN_SIZE = INPUT_FEATURE_SIZE * 2       #隐藏层
NUM_LAYERS = 2 #LSTM堆叠层数
PREDICT_STEPS = 2 #预测未来一年的GDP数据
device = 'cuda' if torch.cuda.is_available() else 'cpu'
BATCH_SIZE = 1
WINDOW_SIZE = 6 #历史窗口
GDP_COL_INDEX = 2 #
NUM_EPOCHS = 100

PROVINCES = [
    "北京市",
    "天津市",
    "上海市",
    "重庆市",
    "内蒙古自治区",
    "广西壮族自治区",
    "西藏自治区",
    "宁夏回族自治区",
    "新疆维吾尔自治区",
    "河北省",
    "山西省",
    "辽宁省",
    "吉林省",
    "黑龙江省",
    "江苏省",
    "浙江省",
    "安徽省",
    "福建省",
    "江西省",
    "山东省",
    "河南省",
    "湖北省",
    "湖南省",
    "广东省",
    "海南省",
    "四川省",
    "贵州省",
    "云南省",
    "陕西省",
    "甘肃省",
    "青海省"
]
# --- END --- #

current_dir = os.getcwd()
parent_dir = os.path.dirname(current_dir)
data_dir = os.path.join(parent_dir, "data")

def main():

    for PROVINCE in PROVINCES:
        # 获取目标路径的数据
        scaler = MinMaxScaler()
        # origin_data是原始csv文件的数据，data是经过归一化的数据
        origin_data,data = data_setup.create_dataset(data_dir,PROVINCE)
        # 这个数据只是启动scaler
        data_scaled = scaler.fit_transform(origin_data.values)
        # data_x代表分化后的训练数据，data_y代表分化后的测试数据
        data_x,data_y,val_Y2025,val_Y2026 = utils.create_training_sequences(
            data,
            WINDOW_SIZE,
            PREDICT_STEPS,
            GDP_COL_INDEX
        )

        plot = utils.create_plot_sequences(origin_data, PROVINCE)
        # 构建模型
        model = model_builder.Seq2Seq(
            input_size=INPUT_FEATURE_SIZE,
            hidden_size=HIDDEN_SIZE,
            num_layers=NUM_LAYERS,
            output_size=OUTPUT_FEATURE_SIZE,
            predict_steps=PREDICT_STEPS
        ).to(device)
        # 定义损失函数和优化器
        loss_fn = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

        # 训练并获取每轮的指标结果
        results = engine.train(
            model,
            data_x,
            data_y,
            loss_fn,
            optimizer,
            NUM_EPOCHS,
            device)

        # 将训练指标保存为 JSON，按省份命名，便于后台通过 API 读取
        MODEL_PATH = "models"
        os.makedirs(MODEL_PATH, exist_ok=True)
        metrics_path = os.path.join(MODEL_PATH, f"{PROVINCE}_training_metrics.json")
        metrics_payload = {
            'province': PROVINCE,
            'saved_at': datetime.datetime.now().isoformat(),
            'num_epochs': NUM_EPOCHS,
            'hyperparams': {
                'input_feature_size': INPUT_FEATURE_SIZE,
                'hidden_size': HIDDEN_SIZE,
                'num_layers': NUM_LAYERS,
                'predict_steps': PREDICT_STEPS,
                'window_size': WINDOW_SIZE,
                'batch_size': BATCH_SIZE
            },
            'metrics': results
        }
        try:
            with open(metrics_path, 'w', encoding='utf-8') as mf:
                json.dump(metrics_payload, mf, ensure_ascii=False, indent=2)
            print(f"✅ 训练指标已保存: {metrics_path}")
        except Exception as e:
            print(f"❌ 保存训练指标失败: {e}")

        # 将训练指标保存到数据库
        try:
            # 导入数据库管理器
            sys.path.append(os.path.join(current_dir, 'backend_api'))
            from gdp_db_utils import gdp_db_manager
            
            # 保存到数据库
            gdp_db_manager.save_training_metrics(PROVINCE, metrics_payload)
            print(f"✅ 训练指标已保存到数据库: {PROVINCE}")
        except Exception as e:
            print(f"❌ 保存训练指标到数据库失败: {e}")

        # 1. 预测：使用 data_x 预测所有训练样本的输出（返回 scaled 后的结果，形状 (N, 4)）
        train_predictions_scaled = engine.predict(
            model,
            data_x,  # 使用训练数据作为输入
            device
        )

        # 2. 反归一化预测值 (形状 (N_sequences, 4))
        train_predictions_unscaled = scaler.inverse_transform(train_predictions_scaled)

        # 3. 反归一化 data_y_true
        data_y_gdp_only = data_y[:, 0, 0].reshape(-1, 1)

        # 创建一个临时数组，将 GDP 填入正确的位置 (GDP_COL_INDEX=2) 形状: (N_sequences, INPUT_FEATURE_SIZE)
        temp_y_true_scaled = np.zeros((data_y_gdp_only.shape[0], INPUT_FEATURE_SIZE))
        temp_y_true_scaled[:, GDP_COL_INDEX] = data_y_gdp_only.flatten()

        # 反归一化真实目标值 (形状 (N_sequences, 4))
        data_y_true_unscaled = scaler.inverse_transform(temp_y_true_scaled)

        # 4. 调用绘图函数进行训练序列对比
        utils.plot_training_comparison(
            origin_data=origin_data,
            data_x=data_x,
            data_y_pred=train_predictions_unscaled,  
            data_y_true=data_y_true_unscaled, 
            province=PROVINCE,
            window_size=WINDOW_SIZE,
            gdp_col_name='GDP'
        )

        final = engine.predict(model,
                               val_Y2025,
                               device)
        # 把最终的预测数据进行反归一化处理
        final_data = scaler.inverse_transform(final)
        final_gdp_values = final_data[:, GDP_COL_INDEX]

        # 计算未来预测的年份
        start_year = origin_data.index[-1] + 1
        years = range(start_year, start_year + len(final_gdp_values))

        # 将原始数据和预测数据传递给未来预测绘图函数
        utils.plot_gdp_comparison(
            origin_data=origin_data,
            province=PROVINCE,
            pred_years=list(years),
            pred_gdp_values=final_gdp_values,
            gdp_col_name='GDP'  
        )

        output_df = pd.DataFrame(
            final_gdp_values,
            index=years,
            columns=[f'{PROVINCE}GDP 预测值 (亿)']
        )
        print(output_df)

        MODEL_PATH = "models"
        os.makedirs(MODEL_PATH, exist_ok=True)

        # 1. 保存 PyTorch 模型参数 (.pth)
        model_save_path = os.path.join(MODEL_PATH, f"{PROVINCE}_seq2seq_gdp_model.pth")
        torch.save(model.state_dict(), model_save_path)
        print(f"✅ 模型参数已保存至: {model_save_path}")

        # 2. ONNX 导出
        dummy_input = torch.randn(BATCH_SIZE, WINDOW_SIZE, INPUT_FEATURE_SIZE).to(device)
        onnx_model_path = os.path.join(MODEL_PATH, f"{PROVINCE}_seq2seq_gdp_model.onnx")

        try:
            torch.onnx.export(
                model,
                dummy_input,
                onnx_model_path,
                export_params=True,
                opset_version=17,
                do_constant_folding=True,
                input_names=['input'],
                output_names=['output'],
                dynamic_axes={'input': {0: 'batch_size'},
                              'output': {0: 'batch_size'}}
            )
            onnx_model = onnx.load(onnx_model_path)
            onnx.checker.check_model(onnx_model)
            print(f"✅ ONNX 模型导出成功并已验证: {onnx_model_path}")
        except Exception as e:
            print(f"❌ ONNX 模型导出或验证失败: {e}")
if __name__ == "__main__":
    main()