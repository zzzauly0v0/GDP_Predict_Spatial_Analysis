# config.py - 配置参数

import pathlib

# ==================== 全局配置参数 ====================
CFG = {
    # 空间分析配置
    "shp_file": "china_province.geojson",
    "db_config": {
        'host': 'localhost',
        'user': 'root',
        'database': '工程实践', # 修改成你的数据库名称
        'port': 3306,
        'password': '123456', # 修改成你的数据库密码
        'charset': 'utf8mb4'
    },
    "db_table": "年度数据", # 用于空间分析的数据库表
    "join_key_shp": "name",
    "join_key_db": "地区",
    "out_dir": "output",
    "perm": 99,  # 空间分析优化参数：排列检验次数
}

# 数据库连接配置
MYSQL_USER = 'root'
MYSQL_PASSWORD = '123456' # 修改成你的数据库密码
MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_DB_NAME = '工程实践' # 修改成你的数据库名称

MYSQL_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB_NAME}'

# 目标表列表 (按需修改)
TARGET_TABLES = [
    '人口数据', '地方财政支出数据', '季度指数数据',
    '季度数据', '年度数据', '消费品数据',
    'gdp_predictions', 'model_training_metrics', 'training_epoch_details'
]

# 单位映射表
UNIT_MAP = {
    '人口数据': '万',
    '地方财政支出数据': '亿',
    '季度指数数据': '', # 指数通常没有单位
    '季度数据': '亿',
    '年度数据': '亿',
    '消费品数据': '亿',
    'gdp_predictions': '亿',
    'model_training_metrics': '',
    'training_epoch_details': '',
}

# 文本列（无需单位）
TEXT_COLS = ['地区', '省份', '城市', '名称', '描述', '指标名称', 'province', 'model_version', 'hyperparams_json', 'training_session_id']

# 创建输出目录
pathlib.Path(CFG["out_dir"]).mkdir(exist_ok=True)