import onnxruntime
import numpy as np
import os
import torch
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import sys

# -----------------------------------------------------
# 1. 修正跨目录导入和路径问题
# -----------------------------------------------------

# 1.1 获取当前脚本的绝对路径
current_file_path = os.path.abspath(__file__)
# current_file_path: ...\Prediction\backend_api\gdp_onnx_service.py

backend_api_dir = os.path.dirname(current_file_path)
# backend_api_dir: ...\Prediction\backend_api

prediction_dir = os.path.dirname(backend_api_dir)
# prediction_dir: ...\Prediction (data_setup.py 和 models/ 在这里)

project_root = os.path.dirname(prediction_dir)
# project_root: ...\GDP_LSTM (data/ )


if prediction_dir not in sys.path:
    sys.path.insert(0, prediction_dir)

# 1.3. 导入必要的模块
try:
    import data_setup
except ImportError:
    print(f"致命错误: 无法导入 data_setup.py。请检查文件是否位于 {prediction_dir}")
    sys.exit(1)


# -----------------------------------------------------
# 2. 路径配置 (使用上面定义的变量)
# -----------------------------------------------------

# data 位于项目根目录
DATA_DIR = os.path.join(project_root, "data")

# models 位于 Prediction 目录
MODEL_DIR = os.path.join(prediction_dir, "models")


# -----------------------------------------------------
# 3. 超参数定义 (必须与 train.py 保持一致)
# -----------------------------------------------------
INPUT_FEATURE_SIZE = 4
WINDOW_SIZE = 6
GDP_COL_INDEX = 2
PREDICT_STEPS = 2
PROVINCES = [
    "北京市", "天津市", "上海市", "重庆市", "内蒙古自治区", "广西壮族自治区",
    "西藏自治区", "宁夏回族自治区", "新疆维吾尔自治区", "河北省", "山西省",
    "辽宁省", "吉林省", "黑龙江省", "江苏省", "浙江省", "安徽省", "福建省",
    "江西省", "山东省", "河南省", "湖北省", "湖南省", "广东省", "海南省",
    "四川省", "贵州省", "云南省", "陕西省", "甘肃省", "青海省"
]


class GDPPredictorService:
    """
    使用 ONNX Runtime 预测指定省份 GDP 的服务类。
    """

    def __init__(self, province: str):
        if province not in PROVINCES:
            raise ValueError(f"无效的省份名称: {province}")

        self.province = province
        self.model_path = os.path.join(MODEL_DIR, f"{province}_seq2seq_gdp_model.onnx")
        self.session = None # onnx的计算器
        self.scaler = MinMaxScaler()
        self.origin_data = None
        self.last_sequence = None

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"ONNX 模型未找到: {self.model_path}. 请先运行 train.py 生成模型。")

        # 1. 初始化 ONNX Runtime Session
        try:
            self.session = onnxruntime.InferenceSession(self.model_path)
        except Exception as e:
            raise RuntimeError(f"ONNX 模型加载失败: {e}")

        # 2. 预加载数据和 Scaler
        self._load_data_and_scaler()

    def _load_data_and_scaler(self):
        """加载原始数据并拟合 MinMaxScaler，准备预测输入序列。"""
        # origin_data是原始csv文件的数据 (已翻转时间顺序)
        self.origin_data, data_scaled = data_setup.create_dataset(DATA_DIR, self.province)

        # 重新拟合 scaler (使用原始的未归一化数据)
        self.scaler.fit(self.origin_data.values)

        if len(data_scaled) < WINDOW_SIZE:
            raise ValueError(f"{self.province} 数据长度不足 ({len(data_scaled)})，无法形成历史窗口 ({WINDOW_SIZE})。")
        
        # data_scaled是20个长度的数据05到24年的数据，最后一个窗口就是14（19年到24年的数据）
        last_start_index = len(data_scaled) - WINDOW_SIZE
        self.last_sequence = data_scaled[last_start_index: last_start_index + WINDOW_SIZE]

    def load_custom_data(self, population_df, consumption_df, gdp_df, financial_df):
        """加载来自于api上传的自定义数据，并更新 scaler 和最后的输入序列"""
        try:
            print(f"[DEBUG] 正在加载自定义数据，省份: {self.province}")
            # 确保数据列名一致
            province = self.province
            # 检查数据类型
            print(f"[DEBUG] 数据类型检查: 人口({type(population_df)}), 消费({type(consumption_df)}), GDP({type(gdp_df)}), 财政({type(financial_df)})")
            population = population_df[province]  # 单位是万
            consumption = consumption_df[province]  # 单位是亿
            gdp = gdp_df[province]  # 单位是亿
            financial = financial_df[province]  # 单位是亿

            # 拼接表格
            origin_data = pd.concat(
                [population, consumption, gdp, financial],
                axis=1
            )
            origin_data.columns = ['population', 'consumption', 'GDP', 'financial']

            # 翻转时间顺序
            origin_data_reversed = origin_data.iloc[::-1].reset_index(drop=True)

            # 转换为numpy数组并进行归一化
            data_for_scaling = origin_data_reversed.values
            self.scaler = MinMaxScaler()
            data_scaled = self.scaler.fit_transform(data_for_scaling)

            # 更新原始数据
            self.origin_data = origin_data_reversed

            # 也使用data_for_scaling和data_scaled
            # 更新实例变量
            self.scaler.fit(self.origin_data.values)

            # 获取最后WINDOW_SIZE长度的数据作为预测输入
            if len(data_scaled) < WINDOW_SIZE:
                raise ValueError(f"自定义数据长度不足 ({len(data_scaled)})，无法形成历史窗口 ({WINDOW_SIZE})。")
            
            last_start_index = len(data_scaled) - WINDOW_SIZE
            self.last_sequence = data_scaled[last_start_index: last_start_index + WINDOW_SIZE]

        except Exception as e:
            raise RuntimeError(f"加载自定义数据失败: {str(e)}")
        

    def predict_gdp(self) -> dict:
        """执行 ONNX 模型推理并返回反归一化的预测结果。"""
        if self.session is None or self.last_sequence is None:
            raise RuntimeError("预测服务未正确初始化。")

        # 1. 准备输入数据 (形状: (1, WINDOW_SIZE, INPUT_FEATURE_SIZE))
        # ONNX 模型期望 float32
        input_data = self.last_sequence.astype(np.float32)[np.newaxis, :, :]

        # 2. 执行推理
        input_name = self.session.get_inputs()[0].name
        output_name = self.session.get_outputs()[0].name

        # predictions_np 形状: (1, PREDICT_STEPS, 1)
        predictions_np = self.session.run([output_name], {input_name: input_data})[0]

        # 3. 后处理和反归一化
        pre_np = predictions_np.squeeze()  

        # 确保是二维数组 (PREDICT_STEPS, 1)
        pre_2d = pre_np.reshape(-1, 1)

        # 创建一个临时数组，将预测的 GDP 填入正确的位置 (用于反归一化)
        temp_inverse_input = np.zeros((PREDICT_STEPS, INPUT_FEATURE_SIZE))
        temp_inverse_input[:, GDP_COL_INDEX] = pre_2d.flatten()

        # 反归一化并提取 GDP 列
        final_data_unscaled = self.scaler.inverse_transform(temp_inverse_input)
        final_gdp_values = final_data_unscaled[:, GDP_COL_INDEX]

        # 4. 构建结果字典
        # 预测结果的年份应该是 2025, 2026
        # 由于原始计算可能是 25, 26，所以加上 2000
        start_year = self.origin_data.index[-1] + 6
        years = range(start_year, start_year + PREDICT_STEPS)

        result = {
            "province": self.province,
            "predictions": [
                {"year": int(y) + 2000, "gdp": round(float(gdp), 2)}  # year + 2000 转换为实际年份
                for y, gdp in zip(years, final_gdp_values)
            ]
        }
        return result


# 缓存预测器实例，避免重复加载 ONNX 模型和数据
_predictors_cache = {}


def get_predictor_service(province: str) -> GDPPredictorService:
    """获取指定省份的预测服务实例 (使用缓存)。"""
    if province not in _predictors_cache:
        _predictors_cache[province] = GDPPredictorService(province)
    return _predictors_cache[province]


# 启动时预加载所有模型 (可选，加速首次请求)
def preload_all_models():
    for p in PROVINCES:
        try:
            get_predictor_service(p)
            # print(f"预加载成功: {p}")
        except Exception as e:
            # print(f"预加载 {p} 失败: {e}")
            pass
