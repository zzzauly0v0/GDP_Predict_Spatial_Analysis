# GDP预测系统后端API技术文档

## 目录

1. [系统架构](#系统架架构)
2. [核心模块详解](#核心模块详解)
3. [API接口文档](#api接口文档)
4. [数据库设计](#数据库设计)
5. [部署指南](#部署指南)

---

## 系统架构

### 整体架构图

```
前端请求
    ↓
Flask API Gateway (app.py)
    ├── 基础数据API (db_utils.py)
    ├── 耦合协调度分析 (coupling_analysis.py)
    ├── 空间分析 (spatial_analysis.py)
    └── GDP预测服务 (gdp_onnx_service.py)
         ↓
    MySQL数据库 + ONNX模型
```

### 技术栈

| 组件 | 技术选型 | 版本要求 |
|------|---------|---------|
| Web框架 | Flask | 2.x+ |
| 数据库ORM | SQLAlchemy | 1.4+ |
| 跨域支持 | Flask-CORS | 最新 |
| 数据处理 | Pandas, NumPy | - |
| 空间分析 | GeoPandas, PySAL | - |
| 推理引擎 | ONNX Runtime | 1.12+ |
| 数据库 | MySQL | 5.7+ |

### 目录结构

```
backend_api/
├── app.py                    # Flask主应用
├── config.py                 # 配置参数
├── db_utils.py              # 数据库工具
├── coupling_analysis.py     # 耦合协调度分析
├── spatial_analysis.py      # 空间分析
├── gdp_onnx_service.py      # GDP预测服务
├── admin.html               # 后台管理页面
├── api_test.html            # API测试页面
└── output/                  # 空间分析结果输出
    ├── available_years.json
    └── *_spatial_analysis.shp
```

---

## 核心模块详解

## 1. app.py - Flask应用主文件

### 1.1 应用初始化

#### 核心配置

```python
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 280  # 连接池回收时间
app.config['JSON_AS_ASCII'] = False         # 支持中文响应
CORS(app)  # 启用跨域资源共享
```

#### 数据库初始化流程

```python
with app.app_context():
    # 1. 反射目标表结构
    reflect_tables(app)
    
    # 2. 初始化耦合分析引擎
    analyzer.init_engine()
    
    # 3. 预加载GDP预测模型 (可选优化)
    preload_all_models()
```

### 1.2 路由分类

#### 基础数据路由

| 路由 | 方法 | 功能 | 返回格式 |
|-----|------|------|---------|
| `/api/tables` | GET | 获取所有表列表 | JSON |
| `/api/<table_name>` | GET | 分页查询表数据 | JSON |
| `/api/<table_name>/<pk>` | GET | 查询单条记录 | JSON |

**示例请求**:

```bash
# 获取人口数据（第1页，每页20条，搜索"北京"）
GET /api/人口数据?page=1&size=20&search=北京
```

**响应格式**:

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "地区": "北京市",
      "2024年": "2188.60",
      "_pk": "abc123..."
    }
  ],
  "total": 31
}
```

#### 耦合协调度分析路由

| 路由 | 方法 | 功能 |
|-----|------|------|
| `/api/data` | GET | 获取指定年份GeoJSON数据 |
| `/api/regions` | GET | 获取地区排名列表 |
| `/api/all_trend` | GET | 获取2005-2024趋势数据 |
| `/api/years` | GET | 获取可用年份列表 |

**核心响应数据**:

```json
{
  "success": true,
  "year": "2024",
  "geojson": {
    "type": "FeatureCollection",
    "features": [...]
  },
  "statistics": {
    "total_regions": 31,
    "coordination_range": {"min": 0.35, "max": 0.92},
    "level_distribution": {"优质协调": 5, "中级协调": 12, ...},
    "average_coordination": 0.68
  }
}
```

#### GDP预测路由

| 路由 | 方法 | 功能 | 参数 |
|-----|------|------|------|
| `/api/gdp/historical/<province>` | GET | 获取历史GDP数据 | 省份名 |
| `/api/gdp/metrics/<province>` | GET | 获取训练指标 | 省份名 |
| `/api/gdp/predict/<province>` | GET | 获取GDP预测结果 | 省份名 |
| `/api/gdp/predict_custom` | POST | 自定义数据预测 | 4个CSV文件 |

**历史数据响应示例**:

```json
{
  "success": true,
  "province": "北京市",
  "data": [
    {"year": 2005, "gdp": 6814.5},
    {"year": 2006, "gdp": 7870.3},
    ...
    {"year": 2024, "gdp": 43760.7}
  ]
}
```

**预测结果响应示例**:

```json
{
  "success": true,
  "province": "北京市",
  "data": [
    {"year": 2025, "gdp": 46523.12},
    {"year": 2026, "gdp": 49384.56}
  ]
}
```

#### 空间分析路由

| 路由 | 方法 | 功能 |
|-----|------|------|
| `/api/spatial/available-years` | GET | 获取可用年份 |
| `/api/spatial/data/<year>` | GET | 获取空间分析GeoJSON |
| `/api/spatial/stats/<year>` | GET | 获取统计信息 |
| `/api/spatial/refresh` | POST | 刷新空间分析数据 |

---

## 2. config.py - 配置管理

### 2.1 全局配置字典

```python
CFG = {
    "shp_file": "china_province.geojson",  # 地理边界文件
    "db_config": {
        'host': 'localhost',
        'user': 'root',
        'database': '工程实践',
        'port': 3306,
        'password': '123456',
        'charset': 'utf8mb4'
    },
    "db_table": "年度数据",          # 主数据表
    "join_key_shp": "name",         # 地理数据关联字段
    "join_key_db": "地区",          # 数据库关联字段
    "out_dir": "output",            # 输出目录
    "perm": 99                      # 空间分析排列检验次数
}
```

### 2.2 数据库URI构建

```python
MYSQL_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_NAME}'
```

### 2.3 目标表配置

```python
TARGET_TABLES = [
    '人口数据', '地方财政支出数据', '季度指数数据',
    '季度数据', '年度数据', '消费品数据',
    'gdp_predictions',              # GDP预测结果表
    'model_training_metrics',       # 模型训练指标表
    'training_epoch_details'        # 训练详情表
]
```

### 2.4 单位映射表

**作用**: 自动为数值添加单位标识

```python
UNIT_MAP = {
    '人口数据': '万',
    '地方财政支出数据': '亿',
    '年度数据': '亿',
    'gdp_predictions': '亿',
    # ...
}
```

### 2.5 文本列定义

```python
TEXT_COLS = [
    '地区', '省份', '城市', '名称', 
    'province', 'model_version', 
    'hyperparams_json'
]
```

**用途**: 区分文本和数值列，文本列不进行格式化处理

---

## 3. db_utils.py - 数据库工具模块

### 3.1 数据库引擎初始化

#### `init_db_engine()`

**功能**: 创建SQLAlchemy引擎，配置连接池

**关键参数**:

```python
engine = create_engine(
    MYSQL_URI,
    pool_size=5,              # 连接池大小
    max_overflow=10,          # 最大溢出连接数
    pool_recycle=3600,        # 连接回收时间(秒)
    pool_pre_ping=True        # 连接前检测可用性
)
```

**连接池优势**:
- ✅ 减少连接建立开销
- ✅ 防止连接超时
- ✅ 提高并发性能

### 3.2 表结构反射

#### `reflect_tables(app)`

**流程图**:

```
Flask App
    ↓
创建MetaData对象
    ↓
反射数据库表结构
    ↓
将Table对象存入TableMap
    ↓
后续查询使用TableMap
```

**代码实现**:

```python
def reflect_tables(app):
    with app.app_context():
        meta = db.MetaData()
        meta.reflect(bind=db.engine)
        
        for tbl in TARGET_TABLES:
            if tbl in meta.tables:
                TableMap[tbl] = db.Table(tbl, meta, autoload_with=db.engine)
```

### 3.3 数值格式化

#### `format_numeric_value(value)`

**智能格式化逻辑**:

```python
输入: 12345.6789000
     ↓
检查类型: Decimal/float/int/str
     ↓
判断是否整数
     ↓
是 → 输出 "12346"
否 → 保留有效小数位 → "12345.6789"
```

**处理规则**:

| 输入类型 | 示例输入 | 输出结果 |
|---------|---------|---------|
| 整数 | 1000 | "1000" |
| 整数型浮点 | 1000.0 | "1000" |
| 小数 | 1234.5678 | "1234.5678" |
| 字符串数字 | "1234.56" | "1234.56" |
| Decimal | Decimal('123.45') | "123.45" |

**核心代码**:

```python
if isinstance(value, float):
    if value.is_integer():
        return str(int(value))
    else:
        # 保留有效小数位(最多4位)
        str_value = str(value)
        decimal_part = str_value.split('.')[1]
        significant_decimals = len(decimal_part.rstrip('0'))
        decimals_to_keep = min(significant_decimals, 4)
        return f"{value:.{decimals_to_keep}f}"
```

### 3.4 伪主键生成

#### `fake_pk(row, columns)`

**用途**: 为无主键表生成唯一标识符

**原理**: MD5哈希拼接行数据

```python
def fake_pk(row, columns):
    # 拼接所有列值
    raw = '|'.join(str(getattr(row, c)) for c in columns if c not in ['geometry'])
    
    # MD5哈希
    return hashlib.md5(raw.encode()).hexdigest()
    # 示例输出: "3f7c8a2b1e9d4f5a6b..."
```

### 3.5 路由函数

#### `list_data_route(table_name, request, db)`

**功能**: 分页查询+模糊搜索

**SQL生成逻辑**:

```python
# 1. 基础查询
stmt = tbl.select()

# 2. 添加搜索条件
if search:
    like_str = f'%{search}%'
    # 对所有VARCHAR列进行OR搜索
    stmt = stmt.where(
        or_(*[cast(c, String).like(like_str) for c in varchar_cols])
    )

# 3. 分页
stmt = stmt.offset((page - 1) * size).limit(size)
```

**性能优化**:
- ✅ 只对字符串类型列进行LIKE搜索
- ✅ 使用OFFSET/LIMIT分页
- ✅ 单独查询总数避免全表扫描

---

## 4. coupling_analysis.py - 耦合协调度分析

### 4.1 核心算法

#### 耦合度计算公式

**数学模型**:

$$C = \sqrt{\frac{U_p \times U_e}{[\frac{U_p + U_e}{2}]^2}}$$

其中:
- $U_p$: 人口发展指数(归一化)
- $U_e$: 经济发展指数(归一化)
- $C$: 耦合度 $[0, 1]$

#### 协调度计算公式

$$T = \alpha U_p + \beta U_e$$
$$D = \sqrt{C \times T}$$

其中:
- $\alpha = \beta = 0.5$: 权重系数
- $T$: 综合发展指数
- $D$: 协调度 $[0, 1]$

### 4.2 类定义

#### `CouplingCoordinationAnalysis`

**属性**:

```python
class CouplingCoordinationAnalysis:
    def __init__(self):
        self.engine = init_db_engine()    # 数据库引擎
        self.result_gdf = None             # 分析结果GeoDataFrame
```

**核心方法**:

```python
# 1. 数据加载与处理
load_and_process_data(target_year='2024') -> bool

# 2. 耦合协调度计算
calculate_coupling_coordination(data) -> DataFrame

# 3. 趋势数据获取
get_all_trend_data() -> List[dict]

# 4. 可用年份查询
get_available_years() -> List[str]
```

### 4.3 数据处理流程

```python
def load_and_process_data(self, target_year='2024'):
    # 1. 从数据库加载人口和GDP数据
    population_df = pd.read_sql("SELECT * FROM `人口数据`", connection)
    gdp_df = pd.read_sql("SELECT * FROM `年度数据`", connection)
    
    # 2. 提取目标年份列
    pop_cols = [col for col in population_df.columns if str(target_year) in str(col)]
    gdp_cols = [col for col in gdp_df.columns if str(target_year) in str(col)]
    
    # 3. 数据合并
    merged_data = pd.merge(pop_data, gdp_data, on='region', how='inner')
    
    # 4. 数据清洗
    merged_data = merged_data.dropna()
    merged_data['population'] = pd.to_numeric(merged_data['population'], errors='coerce')
    merged_data['gdp'] = pd.to_numeric(merged_data['gdp'], errors='coerce')
    
    # 5. 计算耦合协调度
    result_data = self.calculate_coupling_coordination(merged_data)
    
    # 6. 合并地理数据
    geo_data = gpd.read_file(shp_file)
    self.result_gdf = geo_data.merge(result_data, left_on='name', right_on='region')
```

### 4.4 协调等级划分

```python
def classify_coordination_level(D):
    if D >= 0.8:   return "优质协调"
    elif D >= 0.7: return "中级协调"
    elif D >= 0.6: return "初级协调"
    elif D >= 0.5: return "勉强协调"
    elif D >= 0.3: return "中度失调"
    else:          return "严重失调"
```

### 4.5 发展类型判断

```python
def classify_development_type(U_p, U_e):
    if U_p > U_e + 0.15:
        return "经济滞后型"  # 人口发展快于经济
    elif U_e > U_p + 0.15:
        return "人口滞后型"  # 经济发展快于人口
    else:
        return "同步发展型"  # 协调发展
```

### 4.6 结果数据结构

```python
{
    'region': '北京市',
    'population': 2188.6,
    'gdp': 43760.7,
    'U_p': 0.85,                      # 人口发展指数
    'U_e': 0.92,                      # 经济发展指数
    'coupling_degree': 0.88,          # 耦合度 C
    'comprehensive_index': 0.885,     # 综合发展指数 T
    'coordination_degree': 0.883,     # 协调度 D
    'coordination_level': '优质协调',
    'development_type': '同步发展型',
    'final_type': '优质协调-同步发展型'
}
```

---

## 5. spatial_analysis.py - 空间分析模块

### 5.1 空间统计指标

#### 全局Moran's I

**公式**:

$$I = \frac{n}{\sum_{i}\sum_{j}w_{ij}} \cdot \frac{\sum_{i}\sum_{j}w_{ij}(x_i - \bar{x})(x_j - \bar{x})}{\sum_{i}(x_i - \bar{x})^2}$$

**解释**:
- $I > 0$: 正空间自相关(高值聚集或低值聚集)
- $I < 0$: 负空间自相关(高低值交替分布)
- $I \approx 0$: 随机分布

#### 局部LISA指标

**四种聚类类型**:

| 类型编码 | 名称 | 解释 |
|---------|------|------|
| 1 | 高-高聚类 | 高GDP地区被高GDP地区环绕 |
| 2 | 低-低聚类 | 低GDP地区被低GDP地区环绕 |
| 3 | 高-低异常 | 高GDP地区被低GDP地区环绕 |
| 4 | 低-高异常 | 低GDP地区被高GDP地区环绕 |

#### Getis-Ord Gi*

**热点分析**:

```python
if gi_p < 0.05:  # 显著性检验
    if gi_z > 0:
        return "热点"  # 高值聚集区
    else:
        return "冷点"  # 低值聚集区
else:
    return "不显著"
```

### 5.2 核心函数

#### `perform_real_spatial_analysis()`

**完整分析流程**:

```python
1. 读取地理边界文件(GeoJSON)
   ↓
2. 从数据库获取年度数据
   ↓
3. 自动检测年份列
   ↓
4. 对每个年份执行空间分析:
   ├── 数据合并与清洗
   ├── 坐标系转换(WGS84 → Web Mercator)
   ├── 构建空间权重矩阵(KNN, K=4)
   ├── 计算全局Moran's I
   ├── 计算局部LISA
   ├── 计算Getis-Ord Gi*
   └── 结果分类与标注
   ↓
5. 保存分析结果(SHP + CSV)
   ↓
6. 生成可用年份列表JSON
```

#### 空间权重矩阵构建

```python
# K近邻权重矩阵(K=4)
k = min(4, len(gdf_projected) - 1)
w = KNN.from_dataframe(gdf_projected, k=k)
w.transform = "r"  # 行标准化
```

**权重矩阵示例**:

```
省份A的邻居: [省份B(0.25), 省份C(0.25), 省份D(0.25), 省份E(0.25)]
权重和为1
```

### 5.3 结果输出

#### SHP文件结构

```
字段列表:
- name: 省份名称
- gdp: GDP数值
- lisa_I: LISA统计量
- lisa_p: LISA显著性p值
- lisa_q: LISA类型编码(1-4)
- lisa_type: LISA聚类类型(中文)
- gi_z: Gi* Z值
- gi_p: Gi* 显著性p值
- gi_type: 热点类型(热点/冷点/不显著)
- analysis_year: 分析年份
- moran_I: 全局Moran's I
- moran_p: 全局Moran's I显著性
- geometry: 地理边界(多边形)
```

#### CSV文件示例

| 省份名称 | GDP数值 | LISA聚类类型 | Gi*热点类型 | 全局Moran_I |
|---------|---------|-------------|------------|------------|
| 北京市 | 43760.7 | 高-高聚类 | 热点 | 0.42 |
| 上海市 | 47689.4 | 高-高聚类 | 热点 | 0.42 |
| 西藏自治区 | 2392.7 | 低-低聚类 | 不显著 | 0.42 |

---

## 6. gdp_onnx_service.py - GDP预测服务

### 6.1 路径修正机制

#### 跨目录导入问题解决

```python
# 当前文件: Prediction/backend_api/gdp_onnx_service.py
current_file_path = os.path.abspath(__file__)

# 逐级获取父目录
backend_api_dir = os.path.dirname(current_file_path)
# → Prediction/backend_api

prediction_dir = os.path.dirname(backend_api_dir)
# → Prediction (data_setup.py在这里)

project_root = os.path.dirname(prediction_dir)
# → GDP_LSTM (data/在这里)

# 添加到系统路径
sys.path.insert(0, prediction_dir)
```

**目录结构示意**:

```
GDP_LSTM/                    (project_root)
├── data/                    (DATA_DIR)
│   ├── YearGDP.csv
│   └── ...
└── Prediction/              (prediction_dir)
    ├── data_setup.py        ← 需要导入的模块
    ├── models/              (MODEL_DIR)
    │   ├── 北京市_seq2seq_gdp_model.onnx
    │   └── ...
    └── backend_api/         (backend_api_dir)
        └── gdp_onnx_service.py  ← 当前文件
```

### 6.2 预测服务类

#### `GDPPredictorService`

**初始化流程**:

```python
class GDPPredictorService:
    def __init__(self, province: str):
        # 1. 验证省份名称
        if province not in PROVINCES:
            raise ValueError(f"无效的省份名称: {province}")
        
        # 2. 检查ONNX模型文件
        model_path = f"{MODEL_DIR}/{province}_seq2seq_gdp_model.onnx"
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型未找到: {model_path}")
        
        # 3. 初始化ONNX Runtime会话
        self.session = onnxruntime.InferenceSession(model_path)
        
        # 4. 加载历史数据并拟合Scaler
        self._load_data_and_scaler()
```

#### 数据加载方法

```python
def _load_data_and_scaler(self):
    # 1. 调用data_setup.create_dataset()
    # origin_data: 原始数据(时间逆序)
    # data_scaled: 归一化后的数据[0,1]
    self.origin_data, data_scaled = data_setup.create_dataset(DATA_DIR, self.province)
    
    # 2. 重新拟合MinMaxScaler
    self.scaler.fit(self.origin_data.values)
    
    # 3. 提取最后WINDOW_SIZE个时间步作为预测输入
    # 示例: 20年数据,窗口6 → 取第14-19条(2019-2024)
    last_start_index = len(data_scaled) - WINDOW_SIZE
    self.last_sequence = data_scaled[last_start_index: last_start_index + WINDOW_SIZE]
    # 形状: (6, 4)
```

#### 预测方法

```python
def predict_gdp(self) -> dict:
    # 1. 准备ONNX输入(需要批次维度)
    input_data = self.last_sequence.astype(np.float32)[np.newaxis, :, :]
    # 形状: (1, 6, 4)
    
    # 2. 执行ONNX推理
    input_name = self.session.get_inputs()[0].name
    output_name = self.session.get_outputs()[0].name
    predictions_np = self.session.run([output_name], {input_name: input_data})[0]
    # 输出形状: (1, 2, 1)
    
    # 3. 反归一化处理
    pre_2d = predictions_np.squeeze().reshape(-1, 1)  # (2, 1)
    
    # 创建4列数组用于反归一化
    temp_inverse_input = np.zeros((PREDICT_STEPS, INPUT_FEATURE_SIZE))
    temp_inverse_input[:, GDP_COL_INDEX] = pre_2d.flatten()
    # [[0, 0, pred1, 0],
    #  [0, 0, pred2, 0]]
    
    # 反归一化
    final_data_unscaled = self.scaler.inverse_transform(temp_inverse_input)
    final_gdp_values = final_data_unscaled[:, GDP_COL_INDEX]
    
    # 4. 构建结果
    start_year = self.origin_data.index[-1] + 6  # 24 + 6 = 30
    years = range(start_year, start_year + PREDICT_STEPS)  # [30, 31]
    
    return {
        "province": self.province,
        "predictions": [
            {"year": int(y) + 2000, "gdp": round(float(gdp), 2)}
            # year: 2030, 2031
            for y, gdp in zip(years, final_gdp_values)
        ]
    }
```

### 6.3 自定义数据预测

#### `load_custom_data()`

**用途**: 支持用户上传CSV文件进行自定义预测

**流程**:

```python
def load_custom_data(self, population_df, consumption_df, gdp_df, financial_df):
    # 1. 提取目标省份列
    province = self.province
    population = population_df[province]
    consumption = consumption_df[province]
    gdp = gdp_df[province]
    financial = financial_df[province]
    
    # 2. 拼接表格
    origin_data = pd.concat([population, consumption, gdp, financial], axis=1)
    origin_data.columns = ['population', 'consumption', 'GDP', 'financial']
    
    # 3. 时间逆序
    origin_data_reversed = origin_data.iloc[::-1].reset_index(drop=True)
    
    # 4. 归一化
    self.scaler = MinMaxScaler()
    data_scaled = self.scaler.fit_transform(origin_data_reversed.values)
    
    # 5. 更新实例变量
    self.origin_data = origin_data_reversed
    self.last_sequence = data_scaled[-WINDOW_SIZE:]
```

**API使用示例**:

```python
# 前端上传4个CSV文件
POST /api/gdp/predict_custom
Content-Type: multipart/form-data

Form Data:
- province: "北京市"
- population: (file) custom_population.csv
- consumption: (file) custom_consumption.csv
- gdp: (file) custom_gdp.csv
- financial: (file) custom_financial.csv
```

### 6.4 缓存机制

```python
_predictors_cache = {}

def get_predictor_service(province: str) -> GDPPredictorService:
    """获取预测器实例(带缓存)"""
    if province not in _predictors_cache:
        _predictors_cache[province] = GDPPredictorService(province)
    return _predictors_cache[province]
```

**优势**:
- ✅ 避免重复加载ONNX模型(耗时操作)
- ✅ 减少内存占用
- ✅ 提高响应速度

### 6.5 模型预加载

```python
def preload_all_models():
    """启动时预加载所有省份模型"""
    for p in PROVINCES:
        try:
            get_predictor_service(p)
            # 首次调用会触发模型加载和数据准备
        except Exception as e:
            pass  # 跳过加载失败的省份
```

**调用位置**:

```python
# app.py
if __name__ == '__main__':
    # ...
    print("开始预加载 GDP 预测模型...")
    preload_all_models()
    print("GDP 预测模型预加载完成。")
    app.run(debug=False)
```

---

## API接口文档

### 接口规范

#### 通用响应格式

**成功响应**:

```json
{
  "success": true,
  "message": "操作成功",
  "data": {...}
}
```

**错误响应**:

```json
{
  "success": false,
  "message": "错误描述",
  "error_code": "ERR_XXX"
}
```

### 接口列表

#### 1. 基础数据接口

##### GET `/api/tables`

获取所有表信息

**响应示例**:

```json
{
  "code": 0,
  "msg": "ok",
  "data": [
    {
      "name": "人口数据",
      "api_base_path": "/api/人口数据",
      "unit": "万"
    },
    {
      "name": "年度数据",
      "api_base_path": "/api/年度数据",
      "unit": "亿"
    }
  ]
}
```

##### GET `/api/<table_name>?page=1&size=20&search=北京`

分页查询表数据

**查询参数**:

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| page | int | 否 | 页码(默认1) |
| size | int | 否 | 每页条数(默认50) |
| search | string | 否 | 搜索关键词 |

#### 2. 耦合协调度接口

##### GET `/api/data?year=2024`

获取指定年份GeoJSON数据

**响应数据结构**:

```json
{
  "success": true,
  "year": "2024",
  "geojson": {
    "type": "FeatureCollection",
    "features": [
      {
        "type": "Feature",
        "properties": {
          "region": "北京市",
          "coordination_degree": 0.883,
          "coordination_level": "优质协调",
          "development_type": "同步发展型",
          "population": 2188.6,
          "gdp": 43760.7
        },
        "geometry": {...}
      }
    ]
  },
  "statistics": {
    "total_regions": 31,
    "coordination_range": {"min": 0.35, "max": 0.92},
    "average_coordination": 0.68
  }
}
```

#### 3. GDP预测接口

##### GET `/api/gdp/historical/北京市`

获取历史GDP数据

**响应示例**:

```json
{
  "success": true,
  "province": "北京市",
  "data": [
    {"year": 2005, "gdp": 6814.5},
    {"year": 2024, "gdp": 43760.7}
  ]
}
```

##### GET `/api/gdp/predict/北京市`

获取GDP预测结果

**响应示例**:

```json
{
  "success": true,
  "province": "北京市",
  "data": [
    {"year": 2025, "gdp": 46523.12},
    {"year": 2026, "gdp": 49384.56}
  ]
}
```

##### POST `/api/gdp/predict_custom`

自定义数据预测

**请求格式**:

```
Content-Type: multipart/form-data

Form Data:
- province: "北京市"
- population: (file)
- consumption: (file)
- gdp: (file)
- financial: (file)
```

---

## 数据库设计

### 核心表结构

#### 1. 年度数据表

```sql
CREATE TABLE `年度数据` (
  `地区` VARCHAR(50) PRIMARY KEY,
  `2005年` DECIMAL(10,2),
  `2006年` DECIMAL(10,2),
  ...
  `2024年` DECIMAL(10,2)
);
```

#### 2. GDP预测结果表

```sql
CREATE TABLE `gdp_predictions` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `province` VARCHAR(50) NOT NULL,
  `prediction_year` INT NOT NULL,
  `predicted_gdp` DECIMAL(12,2),
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY `unique_prediction` (`province`, `prediction_year`)
);
```

#### 3. 模型训练指标表

```sql
CREATE TABLE `model_training_metrics` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `province` VARCHAR(50) NOT NULL,
  `training_session_id` VARCHAR(64),
  `saved_at` DATETIME,
  `num_epochs` INT,
  `hyperparams_json` TEXT,
  `final_train_loss` DECIMAL(10,6),
  `final_test_loss` DECIMAL(10,6)
);
```

---

## 部署指南

### 环境要求

```bash
Python >= 3.8
MySQL >= 5.7
```

### 安装依赖

```bash
pip install flask flask-cors flask-sqlalchemy
pip install pandas numpy scikit-learn
pip install geopandas pymysql sqlalchemy
pip install onnxruntime esda libpysal
```

### 启动服务

```bash
# 1. 初始化数据库
mysql -u root -p < database_schema.sql

# 2. 配置config.py
# 修改数据库连接信息

# 3. 启动Flask应用
python app.py

# 服务地址: http://localhost:5000
```

### 生产部署

```bash
# 使用Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

---

## 常见问题

### Q1: ONNX模型加载失败?

**A**: 检查模型文件路径和版本兼容性

```python
# 确保模型在正确位置
Prediction/models/{province}_seq2seq_gdp_model.onnx

# 检查ONNX Runtime版本
pip install onnxruntime==1.12.0
```

### Q2: 跨域请求被阻止?

**A**: 确认CORS已正确配置

```python
from flask_cors import CORS
CORS(app)  # 允许所有域名

# 或指定域名
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})
```

### Q3: 数据库连接超时?

**A**: 调整连接池配置

```python
app.config['SQLALCHEMY_POOL_RECYCLE'] = 280  # 减少回收时间
app.config['SQLALCHEMY_POOL_PRE_PING'] = True  # 启用连接检测
```

---

**文档版本**: v2.0  
**最后更新**: 2025-12-20  
**维护者**: zzzauly