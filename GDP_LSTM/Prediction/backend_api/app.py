# app.py - Flask 应用主文件和路由定义

import warnings
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import numpy as np
import pandas as pd
import os
import sys

# 导入配置和工具
from config import MYSQL_URI
from db_utils import db, reflect_tables, list_tables_route, list_data_route, one_data_route
from coupling_analysis import analyzer
import spatial_analysis
# from gdp_db_utils import gdp_db_manager

# --- 路径修正，以便导入 data_setup ---
current_file_path = os.path.abspath(__file__)
backend_api_dir = os.path.dirname(current_file_path)
prediction_dir = os.path.dirname(backend_api_dir)
if prediction_dir not in sys.path:
    sys.path.insert(0, prediction_dir)

try:
    from data_setup import create_dataset
except ImportError as e:
    print(f"无法导入模块: {e}。请确保 backend_api 的父目录中有 data_setup.py。")
    # 在app.py中，我们不希望因此而退出，所以只打印警告
    create_dataset = None
# -----------------------------------------

warnings.filterwarnings('ignore')

# ==================== Flask 应用初始化 ====================
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_RECYCLE'] = 280
app.config['JSON_AS_ASCII'] = False
CORS(app)
db.init_app(app) # 绑定 db 实例到 app

# ==================== 基础数据路由 ====================

@app.route('/api/tables')
def list_tables():
    """返回所有目标表的名称和对应的API路径"""
    result = list_tables_route()
    return jsonify(code=0, msg='ok', data=result)

@app.route('/api/<table_name>')
def list_data(table_name):
    """获取指定表的数据列表（支持分页和搜索）"""
    data, status_code = list_data_route(table_name, request, db)
    return jsonify(data), status_code

@app.route('/api/<table_name>/<pk>')
def one_data(table_name, pk):
    """获取指定表的单条数据"""
    data, status_code = one_data_route(table_name, pk, db)
    return jsonify(data), status_code

# ==================== 耦合协调度分析路由 ====================

@app.route('/api/data', methods=['GET'])
def get_analysis_data():
    """获取指定年份的分析数据 (GeoJSON 格式)"""
    year = request.args.get('year', '2024')

    if analyzer.load_and_process_data(year) and analyzer.result_gdf is not None:
        gdf_fixed = analyzer.result_gdf.copy()
        for col in gdf_fixed.select_dtypes(include=[np.number]).columns:
            gdf_fixed[col] = gdf_fixed[col].apply(lambda x: float(x) if not pd.isna(x) else None)

        geojson_data = json.loads(gdf_fixed.to_json())

        stats = {
            "total_regions": len(gdf_fixed),
            "coordination_range": {
                "min": float(gdf_fixed['coordination_degree'].min()),
                "max": float(gdf_fixed['coordination_degree'].max())
            },
            "level_distribution": gdf_fixed['coordination_level'].value_counts().to_dict(),
            "type_distribution": gdf_fixed['development_type'].value_counts().to_dict(),
            "average_coordination": float(gdf_fixed['coordination_degree'].mean())
        }

        return jsonify({
            "success": True,
            "year": year,
            "geojson": geojson_data,
            "statistics": stats
        })
    else:
        return jsonify({
            "success": False,
            "message": f"{year}年数据处理失败",
            "year": year
        })

@app.route('/api/regions', methods=['GET'])
def get_regions_list():
    """获取指定年份的地区列表和排名"""
    year = request.args.get('year', '2024')

    if analyzer.load_and_process_data(year) and analyzer.result_gdf is not None:
        regions = []
        for idx, row in analyzer.result_gdf.iterrows():
            regions.append({
                "name": row['region'],
                "coordination_degree": float(row['coordination_degree']),
                "final_type": row['final_type'],
                "coordination_level": row['coordination_level'],
                "development_type": row['development_type'],
                "population": int(row['population']),
                "gdp": float(row['gdp']),
                "U_p": float(row['U_p']),
                "U_e": float(row['U_e']),
                "coupling_degree": float(row['coupling_degree'])
            })

        regions.sort(key=lambda x: x['coordination_degree'], reverse=True)

        return jsonify({"success": True, "year": year, "regions": regions})
    else:
        return jsonify({"success": False, "message": f"{year}年数据加载失败", "year": year})
    
@app.route('/api/all_trend', methods=['GET'])
def get_all_trend_data():
    """获取所有年份的趋势数据"""
    trend_data = analyzer.get_all_trend_data()

    if trend_data:
        return jsonify({
            "success": True,
            "total_records": len(trend_data),
            "years_covered": len(set(item['year'] for item in trend_data)),
            "trend_data": trend_data
        })
    else:
        return jsonify({"success": False, "message": "趋势数据加载失败"})


@app.route('/api/years', methods=['GET'])
def get_available_years():
    """获取耦合协调度分析可用的年份列表"""
    years = analyzer.get_available_years()
    return jsonify({"success": True, "years": years, "total_years": len(years)})


# ==================== GDP空间分析路由 ====================

@app.route('/api/spatial/available-years', methods=['GET'])
def get_spatial_available_years():
    """获取已生成的空间分析年份列表"""
    data, status_code = spatial_analysis.get_spatial_available_years_route()
    return jsonify(data), status_code

@app.route('/api/spatial/data/<year>', methods=['GET'])
def get_spatial_data_api(year):
    """获取指定年份的 GeoJSON 空间分析结果"""
    geojson, status_code, headers = spatial_analysis.get_spatial_data_api_route(year)
    if isinstance(geojson, dict):
        return jsonify(geojson), status_code
    return geojson, status_code, headers

@app.route('/api/spatial/stats/<year>', methods=['GET'])
def get_spatial_year_stats_api(year):
    """获取年份统计信息"""
    stats, status_code = spatial_analysis.get_spatial_year_stats_api_route(year)
    return jsonify(stats), status_code

@app.route('/api/spatial/refresh', methods=['POST'])
def refresh_spatial_data():
    """手动刷新空间分析数据"""
    try:
        success = spatial_analysis.perform_real_spatial_analysis()
        return jsonify({
            "status": "success" if success else "error",
            "message": "空间分析数据刷新完成" if success else "数据刷新失败",
            "timestamp": pd.Timestamp.now().isoformat()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ==================== 静态文件路由 ====================

@app.route('/')
def admin():
    """首页路由"""
    return send_from_directory('.', 'admin.html')

@app.route('/api-test')
def api_test():
    """API测试页面路由"""
    return send_from_directory('.', 'api_test.html')

@app.route('/<path:path>')
def static_files(path):
    """静态文件服务"""
    return send_from_directory('.', path)

# ==================== GDP预测相关路由 ====================

@app.route('/api/gdp/historical/<province>', methods=['GET'])
def get_gdp_historical_data(province):
    """获取指定省份用于预测的原始历史GDP数据"""
    if 'PROVINCES' not in globals() or province not in PROVINCES:
        return jsonify({"success": False, "message": f"省份名称 '{province}' 无效或PROVINCES列表未加载"}), 400

    if not create_dataset:
        return jsonify({"success": False, "message": "服务器数据加载模块 'data_setup' 未成功导入"}), 500
        
    try:
        project_root = os.path.dirname(prediction_dir)
        data_dir = os.path.join(project_root, "data")
        
        origin_data, _ = create_dataset(data_dir, province)

        # 在后端打印实际的列名，用于验证
        print(f"DEBUG: Columns for {province} are: {origin_data.columns.tolist()}")

        # origin_data 索引是0-19，需要映射到实际年份2005-2024（正序）
        # 将索引转换为实际年份
        data_length = len(origin_data)
        
        # 创建年份列表（从2005正序到2024）
        years = list(range(2005, 2005 + data_length))  # [2005, 2006, ..., 2024]
        
        # 使用 reset_index() 并添加年份列
        historical_data = origin_data.reset_index(drop=True)
        historical_data['year'] = years
        
        # 提取年份和GDP列
        historical_data = historical_data[['year', 'GDP']]
        
        # 重命名列以匹配前端期望
        historical_data.rename(columns={'GDP': 'gdp'}, inplace=True)
        
        # 按年份正序排序（2005->2024）
        historical_data = historical_data.sort_values('year').reset_index(drop=True)
        
        return jsonify({
            "success": True,
            "province": province,
            "data": historical_data.to_dict('records')
        })

    except FileNotFoundError:
        return jsonify({"success": False, "message": f"未能找到 {province} 的历史数据文件"}), 404
    except Exception as e:
        import traceback
        print("--- ERROR IN get_gdp_historical_data ---")
        traceback.print_exc()
        print("--------------------------------------")
        return jsonify({
            "success": False, 
            "message": f"处理历史数据时发生严重错误: {str(e)}",
            "traceback": traceback.format_exc()
            }), 500


try:
    from .gdp_onnx_service import get_predictor_service, PROVINCES, preload_all_models
except ImportError:
    # 如果作为主脚本运行，可能需要调整导入方式
    from gdp_onnx_service import get_predictor_service, PROVINCES, preload_all_models
    print("警告: 使用本地导入 gdp_onnx_service。在大型项目中推荐使用包管理。")


@app.route('/api/gdp/metrics/<province>', methods=['GET'])
def get_gdp_metrics(province):
    """返回指定省份的训练指标 JSON（由训练脚本保存至 Prediction/models）"""
    # 确保 province 合法
    if 'PROVINCES' in globals() and province not in PROVINCES:
        return jsonify({"success": False, "message": f"省份名称 '{province}' 无效"}), 400

    models_dir = os.path.join(prediction_dir, 'models')
    metrics_file = os.path.join(models_dir, f"{province}_training_metrics.json")

    if not os.path.exists(metrics_file):
        return jsonify({"success": False, "message": f"未找到 {province} 的训练指标文件"}), 404

    try:
        with open(metrics_file, 'r', encoding='utf-8') as mf:
            metrics = json.load(mf)
        return jsonify({"success": True, "province": province, "metrics": metrics})
    except Exception as e:
        return jsonify({"success": False, "message": f"读取训练指标失败: {str(e)}"}), 500


@app.route('/api/gdp/predict/<province>', methods=['GET'])
def get_gdp_prediction(province):
    """获取指定省份未来几年的GDP预测值"""

    if province not in PROVINCES:
        return jsonify({"success": False, "message": f"省份名称 '{province}' 无效"}), 400

    try:
        # 通过缓存机制获取预测器实例
        predictor = get_predictor_service(province)

        # 执行预测
        prediction_result = predictor.predict_gdp()

        if prediction_result:
            # 保存预测结果到数据库
            
            return jsonify({
                "success": True,
                "province": province,
                "data": prediction_result['predictions']
            })
        else:
            return jsonify({"success": False, "message": f"未能获取 {province} 的预测结果"}), 500

    except FileNotFoundError as e:
        return jsonify({"success": False, "message": str(e)}), 404
    except Exception as e:
        print(f"预测失败: {e}")
        return jsonify({"success": False, "message": f"预测过程中发生错误: {str(e)}"}), 500

@app.route('/api/gdp/predict_custom', methods=['POST'])
def predict_gdp_custom_data():
    if request.method != 'POST':
        return jsonify({"success": False, "message": "仅支持POST方法"}), 405
        
    # 1. 检查四个CSV文件是否都存在
    required_files = ['population', 'consumption', 'gdp', 'financial']
    if any(file not in request.files for file in required_files):
        return jsonify({"success": False, "message": "必须提供四个CSV文件：population, consumption, gdp, financial"}), 400
    
    province = request.form.get('province')
    if province is None:
        return jsonify({"success": False, "message": "缺少省份参数"}), 400
    
    try:
        # 2. 读取每个上传的CSV文件
        dfs = []
        for file_key in required_files:
            csv_file = request.files[file_key]
            df = pd.read_csv(csv_file.stream)
            
            # 检查是否有目标省份列
            if province not in df.columns:
                return jsonify({"success": False, "message": f"CSV文件 {file_key} 缺少省份列: {province}"}), 400
            dfs.append(df)
        
        # 3. 获取预测器并加载自定义数据
        predictor = get_predictor_service(province)
        predictor.load_custom_data(*dfs)
        
        # 4. 执行预测
        prediction_result = predictor.predict_gdp()
        
        return jsonify({
            "success": True,
            "province": province,
            "data": prediction_result['predictions']
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"预测失败: {str(e)}"}), 500
    
# ==================== 主程序入口 ====================

if __name__ == '__main__':
    # 1. 启动时反射数据库表结构
    with app.app_context():
        reflect_tables(app)

    # 2. 检查耦合分析引擎
    if analyzer.init_engine():
        print("数据库连接初始化成功")
    else:
        print("数据库连接初始化失败")

    # 3. 预加载所有 GDP 预测 ONNX 模型 (可选)
    print("开始预加载 GDP 预测模型...")
    preload_all_models()
    print("GDP 预测模型预加载完成。")

    print("=" * 60)
    # ... (其余打印信息)

    app.run(debug=False)
