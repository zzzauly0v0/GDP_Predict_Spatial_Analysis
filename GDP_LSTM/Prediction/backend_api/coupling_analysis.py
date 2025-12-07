# coupling_analysis.py - 耦合协调度分析模块

import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os
from db_utils import init_db_engine
from config import CFG

class CouplingCoordinationAnalysis:
    def __init__(self):
        self.engine = init_db_engine()
        self.result_gdf = None

    def init_engine(self):
        """检查或重新初始化数据库引擎"""
        if self.engine is None:
            self.engine = init_db_engine()
        return self.engine is not None

    def get_available_years(self):
        """获取可用的年份列表"""
        return [str(year) for year in range(2005, 2025)]

    def load_and_process_data(self, target_year='2024'):
        """加载并处理指定年份的数据"""
        connection = None
        if not self.init_engine():
            return False

        try:
            connection = self.engine.connect()

            # 1. 加载数据
            population_df = pd.read_sql("SELECT * FROM `人口数据`", connection)
            gdp_df = pd.read_sql("SELECT * FROM `年度数据`", connection)

            # 2. 检查年份并提取数据
            pop_cols = [col for col in population_df.columns if str(target_year) in str(col)]
            gdp_cols = [col for col in gdp_df.columns if str(target_year) in str(col)]

            if not pop_cols or not gdp_cols:
                return False

            pop_data = population_df[['地区', pop_cols[0]]].copy()
            pop_data.columns = ['region', 'population']
            gdp_data = gdp_df[['地区', gdp_cols[0]]].copy()
            gdp_data.columns = ['region', 'gdp']

            merged_data = pd.merge(pop_data, gdp_data, on='region', how='inner')
            
            # 3. 数据清洗
            merged_data = merged_data.dropna()
            merged_data['population'] = pd.to_numeric(merged_data['population'], errors='coerce')
            merged_data['gdp'] = pd.to_numeric(merged_data['gdp'], errors='coerce')
            merged_data = merged_data.dropna()

            if merged_data.empty:
                return False

            # 4. 计算耦合协调度
            result_data = self.calculate_coupling_coordination(merged_data)

            # 5. 加载地理数据并合并
            shp_file = CFG['shp_file']
            if not os.path.exists(shp_file):
                print(f"错误: 找不到 {shp_file}")
                return False

            geo_data = gpd.read_file(shp_file)
            
            # 清理地理数据（仅保留大陆省份）
            if 'name' in geo_data.columns:
                mainland_provinces = [
                    '北京市', '天津市', '河北省', '山西省', '内蒙古自治区', '辽宁省', '吉林省', '黑龙江省',
                    '上海市', '江苏省', '浙江省', '安徽省', '福建省', '江西省', '山东省', '河南省', '湖北省',
                    '湖南省', '广东省', '广西壮族自治区', '海南省', '重庆市', '四川省', '贵州省', '云南省',
                    '西藏自治区', '陕西省', '甘肃省', '青海省', '宁夏回族自治区', '新疆维吾尔自治区'
                ]
                geo_data = geo_data[geo_data['name'].isin(mainland_provinces)]

            self.result_gdf = geo_data.merge(result_data, left_on='name', right_on='region', how='inner')
            return True

        except Exception as e:
            print(f"{target_year} 年数据处理错误: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if connection:
                connection.close()

    def calculate_coupling_coordination(self, data):
        """核心计算逻辑：计算耦合度 C、综合发展指数 T 和协调度 D"""
        
        # 数据标准化
        scaler = MinMaxScaler()
        data[['population_norm', 'gdp_norm']] = scaler.fit_transform(data[['population', 'gdp']])

        U_p = data['population_norm'].values
        U_e = data['gdp_norm'].values

        # 计算耦合度 (C)
        epsilon = 1e-8
        C_numerator = U_p * U_e
        C_denominator = ((U_p + U_e) / 2) ** 2 + epsilon
        C = np.sqrt(C_numerator / C_denominator)

        # 计算综合发展指数 (T) 和协调度 (D)
        alpha, beta = 0.5, 0.5
        T = alpha * U_p + beta * U_e
        D = np.sqrt(C * T)

        # 判断协调类型
        coordination_level = []
        development_type = []

        for i in range(len(D)):
            # 协调等级划分
            if D[i] >= 0.8: level = "优质协调"
            elif D[i] >= 0.7: level = "中级协调"
            elif D[i] >= 0.6: level = "初级协调"
            elif D[i] >= 0.5: level = "勉强协调"
            elif D[i] >= 0.3: level = "中度失调"
            else: level = "严重失调"

            # 发展类型判断
            if U_p[i] > U_e[i] + 0.15: dev_type = "经济滞后型"
            elif U_e[i] > U_p[i] + 0.15: dev_type = "人口滞后型"
            else: dev_type = "同步发展型"

            coordination_level.append(level)
            development_type.append(dev_type)

        # 保存结果
        data['U_p'] = U_p
        data['U_e'] = U_e
        data['coupling_degree'] = C
        data['comprehensive_index'] = T
        data['coordination_degree'] = D
        data['coordination_level'] = coordination_level
        data['development_type'] = development_type
        data['final_type'] = [f"{level}-{dtype}" for level, dtype in zip(coordination_level, development_type)]
        
        return data

    def get_all_trend_data(self):
        """获取2005-2024年所有年份的趋势数据"""
        trend_data = []
        years = self.get_available_years()

        for i, year in enumerate(years):
            if self.load_and_process_data(year):
                # 提取关键数据
                for idx, row in self.result_gdf.iterrows():
                    trend_data.append({
                        'year': int(year),
                        'region': row['region'],
                        'coordination_degree': float(row['coordination_degree']),
                        'coordination_level': row['coordination_level'],
                        'development_type': row['development_type'],
                        'population': int(row['population']),
                        'gdp': float(row['gdp'])
                    })
            else:
                print(f"跳过 {year} 年数据（处理失败）")

        return trend_data

# 创建耦合分析实例
analyzer = CouplingCoordinationAnalysis()