# spatial_analysis.py - GDP空间分析模块

import geopandas as gpd
import pandas as pd
import os
import json
import pymysql
from esda import Moran, Moran_Local, G_Local
from libpysal.weights import KNN
from config import CFG

def get_database_data():
    """从数据库获取年度数据"""
    try:
        conn = pymysql.connect(**CFG["db_config"])
        query = f"SELECT * FROM {CFG['db_table']}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def detect_year_columns(df):
    """检测年份列"""
    year_columns = []
    for col in df.columns:
        # 排除非数据列
        if col in [CFG['join_key_db'], 'id', 'ID', '序号']:
            continue
        
        # 匹配包含'年'、纯数字年份或包含'year'/'y'的列
        if any(keyword in str(col) for keyword in ['年']) or \
           (str(col).isdigit() and len(str(col)) == 4 and 2000 <= int(col) <= 2030) or \
           any(keyword in str(col).lower() for keyword in ['year', 'y']):
            year_columns.append(col)
    return year_columns

def save_analysis_result(gdf, year):
    """保存分析结果为 SHP 和 CSV 文件"""
    try:
        output_columns = [
            CFG["join_key_shp"], 'gdp', 'lisa_I', 'lisa_p', 'lisa_q',
            'lisa_type', 'gi_z', 'gi_p', 'gi_type', 'analysis_year',
            'moran_I', 'moran_p', 'geometry'
        ]

        available_columns = [col for col in output_columns if col in gdf.columns]
        gdf_output = gdf[available_columns].copy()

        clean_year = year.replace(' ', '_').replace('/', '_')
        shp_path = f"{CFG['out_dir']}/{clean_year}_spatial_analysis.shp"

        # 1. 保存 SHP 文件
        gdf_output.to_file(shp_path, encoding='utf-8')

        # 2. 保存 CSV 文件
        csv_path = f"{CFG['out_dir']}/{clean_year}_analysis.csv"
        csv_data = gdf_output.drop(columns=['geometry']).copy()
        
        column_mapping = {
            CFG["join_key_shp"]: "省份名称",
            'gdp': "GDP数值",
            'lisa_I': "LISA统计量",
            'lisa_p': "LISA_p值",
            'lisa_q': "LISA类型编码",
            'lisa_type': "LISA聚类类型",
            'gi_z': "Gi*_Z值",
            'gi_p': "Gi*_p值",
            'gi_type': "Gi*热点类型",
            'analysis_year': "分析年份",
            'moran_I': "全局Moran_I",
            'moran_p': "全局Moran_p值"
        }
        csv_data.rename(columns=column_mapping, inplace=True)
        csv_data.to_csv(csv_path, index=False, encoding='utf-8-sig')

        return True

    except Exception as e:
        print(f"保存失败 {year}: {e}")
        return False


def perform_real_spatial_analysis():
    """核心分析函数：使用真实数据进行空间分析"""
    print("开始真实数据空间分析（优化版）...")

    try:
        # 1. 读取矢量数据
        shp_file = CFG["shp_file"]
        if not os.path.exists(shp_file):
            print(f"矢量文件不存在: {shp_file}")
            return False

        gdf_base = gpd.read_file(shp_file)

        # 2. 读取数据库真实数据
        df_db = get_database_data()
        if df_db is None or len(df_db) == 0:
            print("无法获取数据库数据")
            return False

        # 3. 检测年份列
        year_columns = detect_year_columns(df_db)
        if not year_columns:
            print("未找到有效的年份列")
            return False

        successful_years = []

        # 4. 处理每个年份
        for year_col in year_columns:
            try:
                # 合并数据
                gdf_merged = gdf_base.merge(
                    df_db[[CFG["join_key_db"], year_col]],
                    left_on=CFG["join_key_shp"],
                    right_on=CFG["join_key_db"],
                    how='inner'
                )

                # 清理GDP数据
                gdf_merged["gdp"] = pd.to_numeric(gdf_merged[year_col], errors="coerce")
                gdf_merged = gdf_merged[gdf_merged["gdp"].notna()].copy()

                if len(gdf_merged) < 5:
                    continue

                # 转换为投影坐标系进行计算
                gdf_projected = gdf_merged.to_crs(epsg=3857)

                # 空间权重矩阵 - 固定 K=4 近邻
                k = min(4, len(gdf_projected) - 1)
                w = KNN.from_dataframe(gdf_projected, k=k)
                w.transform = "r"

                y = gdf_projected["gdp"].values
                
                # 全局Moran's I
                moran = Moran(y, w, permutations=CFG["perm"])
                
                # LISA分析
                lisa = Moran_Local(y, w, permutations=CFG["perm"])
                gdf_projected["lisa_I"] = lisa.Is
                gdf_projected["lisa_p"] = lisa.p_sim
                gdf_projected["lisa_q"] = lisa.q

                # Gi*热点分析
                gi = G_Local(y, w, permutations=CFG["perm"])
                gdf_projected["gi_z"] = gi.Zs
                gdf_projected["gi_p"] = gi.p_sim

                # 转回地理坐标系
                gdf_result = gdf_projected.to_crs(epsg=4326)

                # 添加分类标签
                lisa_labels = {1: "高-高聚类", 2: "低-低聚类", 3: "高-低异常", 4: "低-高异常"}
                gdf_result["lisa_type"] = gdf_result["lisa_q"].map(lisa_labels)

                def classify_gi(row):
                    if pd.isna(row["gi_p"]) or row["gi_p"] >= 0.05:
                        return "不显著"
                    elif row["gi_z"] > 0:
                        return "热点"
                    else:
                        return "冷点"

                gdf_result["gi_type"] = gdf_result.apply(classify_gi, axis=1)
                gdf_result["analysis_year"] = year_col
                gdf_result["moran_I"] = moran.I
                gdf_result["moran_p"] = moran.p_sim

                if save_analysis_result(gdf_result, year_col):
                    successful_years.append(year_col)

            except Exception as e:
                print(f"{year_col} 处理失败: {e}")
                continue

        # 5. 保存年份列表
        years_data = {
            "available_years": successful_years,
            "total_count": len(successful_years),
            "status": "success",
            "message": f"成功处理 {len(successful_years)} 个年份"
        }

        with open(f"{CFG['out_dir']}/available_years.json", 'w', encoding='utf-8') as f:
            json.dump(years_data, f, ensure_ascii=False, indent=2)

        return True

    except Exception as e:
        print(f"空间分析整体失败: {e}")
        return False

# ----------------- 空间分析路由函数 -----------------

def get_spatial_available_years_route():
    """获取已生成的空间分析年份列表"""
    years_file = f"{CFG['out_dir']}/available_years.json"
    if os.path.exists(years_file):
        with open(years_file, 'r', encoding='utf-8') as f:
            years_data = json.load(f)

        # 检查每个年份的SHP文件是否存在
        all_exist = True
        for year in years_data.get('available_years', []):
            clean_year = year.replace(' ', '_').replace('/', '_')
            shp_path = f"{CFG['out_dir']}/{clean_year}_spatial_analysis.shp"
            if not os.path.exists(shp_path):
                all_exist = False
                break

        if all_exist:
            print(f"✓ 发现已有 {len(years_data['available_years'])} 个年份的分析结果")
            print(f"✓ 跳过分析，直接使用现有结果")
            return True  # 直接返回成功，不执行后面的分析代码

def get_spatial_data_api_route(year):
    """获取指定年份的 GeoJSON 空间分析结果"""
    try:
        clean_year = year.replace(' ', '_').replace('/', '_')
        shp_path = f"{CFG['out_dir']}/{clean_year}_spatial_analysis.shp"

        if os.path.exists(shp_path):
            gdf = gpd.read_file(shp_path)
            # 使用 to_json() 转换为 GeoJSON 字符串
            geojson = gdf.to_json() 
            return geojson, 200, {'Content-Type': 'application/json; charset=utf-8'}
        else:
            return {
                "type": "FeatureCollection",
                "features": [],
                "message": f"未找到 {year} 的预处理数据，请先访问 /api/spatial/refresh 生成数据",
                "action_required": True
            }, 404

    except Exception as e:
        return {"error": str(e)}, 500

def get_spatial_year_stats_api_route(year):
    """获取年份统计信息"""
    try:
        clean_year = year.replace(' ', '_').replace('/', '_')
        shp_path = f"{CFG['out_dir']}/{clean_year}_spatial_analysis.shp"

        if os.path.exists(shp_path):
            gdf = gpd.read_file(shp_path)

            stats = {
                "year": year,
                "province_count": len(gdf),
                "gdp_total": float(gdf['gdp'].sum()),
                "gdp_avg": float(gdf['gdp'].mean()),
                "gdp_max": float(gdf['gdp'].max()),
                "gdp_min": float(gdf['gdp'].min()),
                "moran_I": float(gdf['moran_I'].iloc[0]) if 'moran_I' in gdf.columns else None,
                "moran_p": float(gdf['moran_p'].iloc[0]) if 'moran_p' in gdf.columns else None,
                "lisa_distribution": gdf['lisa_type'].value_counts().to_dict(),
                "gi_distribution": gdf['gi_type'].value_counts().to_dict()
            }
            return stats, 200
        else:
            return {
                "error": f"未找到 {year} 的数据",
                "solution": "请先访问 /api/spatial/refresh 生成空间分析数据"
            }, 404

    except Exception as e:
        return {"error": str(e)}, 500