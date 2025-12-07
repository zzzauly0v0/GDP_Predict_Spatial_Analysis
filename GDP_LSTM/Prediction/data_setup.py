import os
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

NUM_WORKERS = os.cpu_count()


def create_dataset(
        data_path:str,
        province:str,
):
    # 定义数据集的来源
    year_population_path = os.path.join(data_path, "YearPeople.csv")
    year_consumption_path = os.path.join(data_path,"YearXiaofei.csv")
    year_gdp_path = os.path.join(data_path,"YearGDP.csv")
    year_financial = os.path.join(data_path,"YearFinancial.csv")

    # 定义输入特征将他们重新拼接成一个新的csv表格
    population = pd.read_csv(year_population_path)[province]  # 单位是万
    comsumption = pd.read_csv(year_consumption_path)[province]  # 单位是亿
    GDP = pd.read_csv(year_gdp_path)[province]  # 单位是亿
    financial = pd.read_csv(year_financial)[province]  # 单位是亿

    # 生成目标省份的人口、消费、GDP、财政支出的新表格
    origin_data = pd.concat(
        [population, comsumption, GDP, financial],
        axis=1,
    )

    # 定义列表列名
    origin_data.columns = ['polulation', 'consumption', 'GDP', 'financial']

    # 翻转列表,将时间顺序转换成较远时间变成较近时间，并更新索引
    origin_data_reversed = origin_data.iloc[::-1].reset_index(drop=True)

    # 转换为numpy数组
    data_for_scaling = origin_data_reversed.values
    scaler = MinMaxScaler()
    # 进行归一化后的数组
    data_scaled = scaler.fit_transform(data_for_scaling)

    return origin_data_reversed,data_scaled