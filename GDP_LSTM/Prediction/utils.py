import numpy as np
from matplotlib import pyplot as plt
import pandas as pd
def create_training_sequences(data, input_window, output_steps, target_index):
    X, Y = [], []
    N_total = len(data)
    #17到22年
    N_sequences = N_total - input_window - output_steps + 1

    for i in range(N_sequences):

        x_sequence = data[i : i + input_window, :]
        X.append(x_sequence)

        y_sequence = data[i + input_window : i + input_window + output_steps, target_index]
        Y.append(y_sequence)

    X_train_np = np.array(X)
    Y_train_np = np.array(Y)

    # 验证集，18到23，预测24和25年
    val_index_Y2025 = N_sequences
    # 验证集，19到24，预测25和26年
    val_index_Y2026 = N_sequences + 1
    X_val_Y2025 = data[val_index_Y2025: val_index_Y2025 + input_window, :]
    X_val_Y2025 = data[val_index_Y2026: val_index_Y2026 + input_window, :]
    # 确保 Y 数组形状为 (N, P, 1)
    if Y_train_np.size > 0:
        Y_train_np = Y_train_np.reshape(-1, output_steps, 1)
    else:
        Y_train_np = Y_train_np.reshape(0, output_steps, 1)

    return X_train_np, Y_train_np, X_val_Y2025, X_val_Y2025

def create_plot_sequences(data,province:str):
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体（以 SimHei 黑体为例）
    plt.rcParams['axes.unicode_minus'] = False
    N = len(data)
    # 创建x轴刻度的位置
    tick_positions = np.arange(N)
    # 创建x轴刻度的标签
    custom_labels = np.arange(2005, 2005 + N, +1)

    fig, ax = plt.subplots(figsize=(14, 7))

    ax = data.plot(
        kind='line',
        ax=ax,
        secondary_y=['polulation']
    )

    plt.xticks(
        ticks=tick_positions,
        labels=custom_labels,
        rotation=45,
        ha='right'
    )

    # 设置左侧 Y 轴标签
    ax.set_ylabel('数值 (单位: 亿)', fontsize=12, color='C0')
    # 设置右侧Y 轴标签
    ax.right_ax.set_ylabel('人口 (单位: 万)', fontsize=12, color='tab:red')

    ax.set_title(f'{province}GDP等数值趋势', fontsize=16)

    ax.set_xlabel('year', fontsize=12)

    ax.legend(title='Data', loc='upper left')
    ax.right_ax.legend(title='Population', loc='upper right')

    ax.grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.show()


def plot_training_comparison(origin_data: pd.DataFrame, data_x, data_y_pred: np.ndarray, data_y_true: np.ndarray,
                             province: str, window_size: int, gdp_col_name: str):
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 1. 获取真实 GDP 序列的起始年份
    real_years = origin_data.index.tolist()

    start_index_y = window_size
    # 序列的年份范围: [real_years[start_index_y], ..., real_years[-1]]
    start_year = real_years[start_index_y]

    # data_y_true 和 data_y_pred 的长度是 N_sequences
    N_sequences = data_y_true.shape[0]

    # 创建年份标签
    # 假设我们只比较每个序列的第一个预测步 (P=1)
    comparison_years = list(range(start_year, start_year + N_sequences))

    # 2. 准备数据
    # data_y_true 的形状: (N_sequences, 4)，我们只取 GDP (索引 2)
    GDP_COL_INDEX = 2
    true_gdp_values = data_y_true[:, GDP_COL_INDEX]  # (N_sequences,)

    # data_y_pred 的形状: (N_sequences, 4)，包含反归一化的 4 个特征，我们只取 GDP
    pred_gdp_values = data_y_pred[:, GDP_COL_INDEX] # (N_sequences,)

    fig, ax = plt.subplots(figsize=(14, 7))

    # 3. 绘制真实值
    ax.plot(comparison_years, true_gdp_values, label=f'真实 {province} {gdp_col_name} (Y_t+1)', marker='o', linestyle='-', color='blue')

    # 4. 绘制预测值
    ax.plot(comparison_years, pred_gdp_values, label=f'模型预测 {province} {gdp_col_name} (Y_t+1)', marker='x', linestyle='--', color='red')

    # 5. 设置图表属性
    ax.set_title(f'{province} {gdp_col_name} 真实值与模型预测值对比 (训练序列)', fontsize=16)
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel(f'{gdp_col_name} (单位: 亿)', fontsize=12)

    # 设置 X 轴刻度
    plt.xticks(comparison_years, rotation=45, ha='right')

    ax.legend(loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.show()

# 新增：用于绘制未来年份预测结果的函数
def plot_gdp_comparison(origin_data: pd.DataFrame, province: str, pred_years: list[int], pred_gdp_values: np.ndarray, gdp_col_name: str):
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False

    # 1. 准备真实数据
    gdp_data = origin_data[gdp_col_name]
    real_years = gdp_data.index.tolist()
    real_gdp_values = gdp_data.values

    # 2. 准备预测数据
    pred_gdp_series = pd.Series(pred_gdp_values, index=pred_years)

    # 3. 合并数据以进行绘图
    plot_data = pd.concat([gdp_data, pred_gdp_series])

    all_years = plot_data.index.astype(int).tolist()
    all_gdp_values = plot_data.values

    fig, ax = plt.subplots(figsize=(14, 7))

    # 绘制全部数据
    ax.plot(all_years, all_gdp_values, label=f'全部 {province} {gdp_col_name}', marker='o', linestyle='-', color='gray', alpha=0.5)

    # 突出真实值
    ax.plot(real_years, real_gdp_values, label=f'真实 {province} {gdp_col_name}', marker='o', linestyle='-', color='blue')

    # 突出预测值
    ax.plot(pred_years, pred_gdp_values, label=f'预测 {province} {gdp_col_name}', marker='x', linestyle='--', color='red')

    # 突出预测起始点
    last_real_year = real_years[-1]
    last_real_gdp = real_gdp_values[-1]
    ax.scatter(last_real_year, last_real_gdp, color='black', s=100, zorder=5, label='历史数据截止点')

    # 设置图表属性
    ax.set_title(f'{province} 真实 {gdp_col_name} 与预测 {gdp_col_name} 对比', fontsize=16)
    ax.set_xlabel('年份', fontsize=12)
    ax.set_ylabel(f'{gdp_col_name} (单位: 亿)', fontsize=12)

    # 设置 X 轴刻度
    plt.xticks(all_years, rotation=45, ha='right')

    ax.legend(loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.show()


