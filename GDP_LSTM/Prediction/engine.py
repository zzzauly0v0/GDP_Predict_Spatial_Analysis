from typing import Any
import numpy as np
import torch
from tqdm.auto import tqdm
from timeit import default_timer as timer
import matplotlib.pyplot as plt
import os

torch.manual_seed(42)

###  性能观测指标 ###

# 计算绝对误差的平均值。
def mae_metric(predictions, targets):
    return torch.nn.functional.l1_loss(predictions, targets)

# 计算误差平方的平均值。
def mse_metric(predictions, targets):
    return torch.nn.functional.mse_loss(predictions, targets)

def mape_metric(predictions, targets):
    epsilon = 1e-8
    return torch.mean(torch.abs((targets - predictions) / (targets + epsilon))) * 10

def train_step(
        model,
        data_x,
        data_y,
        loss_fn:torch.nn.Module,
        optimizer:torch.optim.Optimizer,
        device:str,
) -> tuple[float, float, float, float] | None:
    model.train()
    N = len(data_x)
    if N == 0:
        print("警告: 训练样本数为 0，请检查数据长度和 WINDOW/PREDICT_STEPS 设置。")
        return
    train_loss = 0.0
    train_mae = 0.0
    train_mse = 0.0
    train_mape = 0.0

    for i in range(N):
        # 转换为 Tensor 并增加批次维度 (Batch=1)
        x_sample = torch.from_numpy(data_x[i]).float().unsqueeze(0).to(device)
        y_sample = torch.from_numpy(data_y[i]).float().unsqueeze(0).to(device)

        optimizer.zero_grad()
        predictions = model(x_sample)

        loss = loss_fn(predictions, y_sample)
        mae = mae_metric(predictions, y_sample)
        mse = mse_metric(predictions, y_sample)
        mape = mape_metric(predictions, y_sample)

        loss.backward()
        optimizer.step()

        train_loss += loss.item()
        train_mae += mae.item()
        train_mse += mse.item()
        train_mape += mape.item()

    avg_loss = train_loss / N
    avg_mae = train_mae / N
    avg_mse = train_mse/N
    avg_mape = train_mape / N

    return avg_loss, avg_mae, avg_mse, avg_mape

def test_step(
        model,
        data_x,
        data_y,
        loss_fn:torch.nn.Module,
        device:str,
) -> tuple[float, float, float, float] | None:
    model.eval()
    N = len(data_x)
    test_loss = 0.0
    train_mae = 0.0
    train_mse = 0.0
    train_mape = 0.0

    if N == 0:
        print("警告: 训练样本数为 0，请检查数据长度和 WINDOW/PREDICT_STEPS 设置。")
        return
    for i in range(N):

        x_sample = torch.from_numpy(data_x[i]).float().unsqueeze(0).to(device)
        y_sample = torch.from_numpy(data_y[i]).float().unsqueeze(0).to(device)

        predictions = model(x_sample)
        loss = loss_fn(predictions, y_sample)
        mae = mae_metric(predictions, y_sample)
        mse = mse_metric(predictions, y_sample)
        mape = mape_metric(predictions, y_sample)

        test_loss += loss.item()
        train_mae += mae.item()
        train_mse += mse.item()
        train_mape += mape.item()

    avg_loss = test_loss / N
    avg_mae = train_mae / N
    avg_mse = train_mse / N
    avg_mape = train_mape / N

    return avg_loss, avg_mae, avg_mse, avg_mape

def train(model,
          data_x,
          data_y,
          loss_fn:torch.nn.Module,
          optimizer:torch.optim.Optimizer,
          num_epochs:int,
          device:str) -> dict[str, list[Any]]:
    results = {
        'train_loss':[],
        'train_mae':[],
        'train_mse':[],
        'train_mape':[],
        'test_loss':[],
        'test_mae':[],
        'test_mse':[],
        'test_mape':[],
    }
    model.to(device)
    for epoch in tqdm(range(num_epochs)):
        train_loss,train_mae,train_mse,train_mape = train_step(model=model,
                                data_x=data_x,
                                data_y=data_y,
                                loss_fn=loss_fn,
                                optimizer=optimizer,
                                device=device)
        test_loss,test_mae,test_mse,test_mape = test_step(model=model,
                              data_x=data_x,
                              data_y=data_y,
                              loss_fn=loss_fn,
                              device=device)
        print(
            f"轮次: {epoch + 1} | "
            f"train_loss: {train_loss:.4f} | "
            f"train_mae: {train_mae:.4f} | "
            f"train_mse: {train_mse:.4f} | "
            f"train_mape: {train_mape:.4f} | "
            f"test_loss: {test_loss:.4f} | "
            f"test_mae: {test_mae:.4f} | "
            f"test_mse: {test_mse:.4f} | "
            f"test_mape: {test_mape:.4f} | "
            )
        results['train_loss'].append(train_loss)
        results['train_mae'].append(train_mae)
        results['train_mse'].append(train_mse)
        results['train_mape'].append(train_mape)
        results['test_loss'].append(test_loss)
        results['test_mae'].append(test_mae)
        results['test_mse'].append(test_mse)
        results['test_mape'].append(test_mape)
    # 创建保存图像的目录
    os.makedirs('parm', exist_ok=True)
    
    # 绘制并保存训练指标图表
    epochs = range(1, num_epochs + 1)
    
    # MAE趋势图
    plt.figure(figsize=(10, 6))
    plt.plot(epochs, results['train_mae'], 'b-', label='Training MAE')
    plt.plot(epochs, results['test_mae'], 'r-', label='Testing MAE')
    plt.title('MAE Trend')
    plt.xlabel('Epochs')
    plt.ylabel('MAE')
    plt.legend()
    plt.savefig(os.path.join('parm', 'mae_plot.png'))
    plt.close()

    # MSE趋势图
    plt.figure(figsize=(10, 6))
    plt.plot(epochs, results['train_mse'], 'b-', label='Training MSE')
    plt.plot(epochs, results['test_mse'], 'r-', label='Testing MSE')
    plt.title('MSE Trend')
    plt.xlabel('Epochs')
    plt.ylabel('MSE')
    plt.legend()
    plt.savefig(os.path.join('parm', 'mse_plot.png'))
    plt.close()

    # MAPE趋势图
    plt.figure(figsize=(10, 6))
    plt.plot(epochs, results['train_mape'], 'b-', label='Training MAPE')
    plt.plot(epochs, results['test_mape'], 'r-', label='Testing MAPE')
    plt.title('MAPE Trend (%)')
    plt.xlabel('Epochs')
    plt.ylabel('MAPE (%)')
    plt.legend()
    plt.savefig(os.path.join('parm', 'mape_plot.png'))
    plt.close()

    return results

def predict(model,
            data,
            device: str):
    model.eval()
    # 1. 确保转为 Tensor
    if not torch.is_tensor(data):
        data = torch.from_numpy(data).float()

    # 2. 增加批次维度 (如果输入是单个样本 (W, F))
    if data.dim() == 2:
        data = data.unsqueeze(0)

    data = data.to(device)

    # 3. 模型预测 (一次性算出所有结果)
    with torch.no_grad():
        predictions = model(data)

    # predictions 的形状现在是 (N_sequences, PREDICT_STEPS, 1)
    pre_np = predictions.cpu().detach().numpy()

    # 新的 pre_2d 保持形状 (N_sequences, PREDICT_STEPS)
    pre_2d = pre_np.squeeze(-1)  

    if pre_2d.ndim == 1:  
        pre_2d = pre_2d.reshape(-1, 1)
    else:  
        pre_2d = pre_2d[:, 0].reshape(-1, 1)

    GDP_COL_INDEX = 2

    temp_inverse_input = np.zeros((pre_2d.shape[0], 4))
    temp_inverse_input[:, GDP_COL_INDEX] = pre_2d.flatten()

    return temp_inverse_input
