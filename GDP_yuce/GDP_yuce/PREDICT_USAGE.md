# GDP预测功能使用说明

## 功能优化说明

### 1. 主要改进

- ✅ **响应式数据管理**：使用 Vue 3 的响应式系统替代直接 DOM 操作
- ✅ **完整的预测流程**：加载数据 → 执行预测 → 显示结果和指标
- ✅ **训练指标展示**：自动加载并展示模型训练指标
- ✅ **图表自动更新**：数据加载后自动渲染图表
- ✅ **错误处理**：完善的错误提示和日志输出

### 2. 使用流程

#### 方式一：使用省份数据预测

1. **选择数据来源**：选择"使用省份数据"
2. **选择省份**：从下拉列表中选择要预测的省份
3. **加载历史数据**：点击"加载数据"按钮，查看历史GDP数据
4. **执行预测**：点击"执行预测"按钮，系统将：
   - 加载历史GDP数据
   - 调用预测模型生成未来预测
   - 加载训练指标数据
   - 自动渲染图表
   - 显示统计信息

#### 方式二：使用自定义数据预测

1. **选择数据来源**：选择"导入自定义数据"
2. **选择模型省份**：选择要使用的预测模型对应的省份
3. **上传数据文件**：上传包含年份和GDP两列的CSV文件
4. **执行预测**：点击"执行预测"按钮

### 3. 数据展示

#### 历史GDP数据
- 表格形式展示历史数据
- 支持按年份排序
- 显示记录总数

#### 预测结果
- 表格形式展示未来预测值
- 高亮显示预测数据
- 显示预测年份数量

#### 训练指标（新增）
- **训练信息**：省份、训练时间、训练轮次
- **超参数**：输入特征数、隐藏层大小、LSTM层数等
- **训练过程指标**：每轮的训练/测试损失、MAE、MSE、MAPE
- **高亮显示**：最后5轮训练数据（收敛情况）

#### GDP趋势图表
- 折线图/柱状图切换
- 历史数据（实线）+ 预测数据（虚线）
- 支持窗口大小自适应

#### 统计信息
- 最新历史GDP
- 预测起始值
- 预测最终值
- 预测期间增长率

### 4. API 路由

确保后端API正确配置：

```javascript
// src/api/index.js
export const getGDPHistoricalData = (province) => {
  return request.get(`/gdp/historical/${encodeURIComponent(province)}`)
}

export const getGDPPrediction = (province) => {
  return request.get(`/gdp/predict/${encodeURIComponent(province)}`)
}

export const getGDPMetrics = (province) => {
  return request.get(`/gdp/metrics/${encodeURIComponent(province)}`)
}
```

### 5. 后端API要求

#### GET /api/gdp/historical/{province}
返回格式：
```json
{
  "success": true,
  "province": "北京市",
  "data": [
    {"year": 2010, "gdp": 14000.00},
    {"year": 2011, "gdp": 16000.00}
  ]
}
```

#### GET /api/gdp/predict/{province}
返回格式：
```json
{
  "success": true,
  "province": "北京市",
  "data": [
    {"year": 2025, "gdp": 45000.00},
    {"year": 2026, "gdp": 47000.00}
  ]
}
```

#### GET /api/gdp/metrics/{province}
返回格式：
```json
{
  "success": true,
  "province": "北京市",
  "metrics": {
    "province": "北京市",
    "saved_at": "2024-12-07T10:00:00",
    "num_epochs": 100,
    "hyperparams": {
      "input_feature_size": 4,
      "hidden_size": 64,
      "num_layers": 2,
      "predict_steps": 5,
      "window_size": 10,
      "batch_size": 32
    },
    "metrics": {
      "train_loss": [0.5, 0.4, ...],
      "train_mae": [100, 90, ...],
      "train_mse": [10000, 8000, ...],
      "train_mape": [5.0, 4.5, ...],
      "test_loss": [0.6, 0.5, ...],
      "test_mae": [110, 100, ...],
      "test_mse": [12000, 10000, ...],
      "test_mape": [5.5, 5.0, ...]
    }
  }
}
```

### 6. 调试技巧

打开浏览器控制台查看日志：
- 历史数据响应
- 预测数据响应
- 训练指标响应
- 错误信息

### 7. 常见问题

**Q: 点击"执行预测"后没有反应？**
A: 检查：
1. 是否选择了省份
2. 浏览器控制台是否有错误
3. 后端API是否正常运行（http://localhost:5000）

**Q: 训练指标不显示？**
A: 检查：
1. 后端是否有对应省份的训练指标文件
2. API响应格式是否正确
3. 控制台是否有警告信息

**Q: 图表不显示？**
A: 检查：
1. 是否有历史数据或预测数据
2. echarts是否正确加载
3. 容器元素是否存在

### 8. 性能优化

- 使用 `Promise.all` 并行加载数据
- 使用 `computed` 计算属性缓存结果
- 使用 `nextTick` 确保DOM更新后再渲染图表
- 响应式数据自动更新视图，无需手动操作DOM
