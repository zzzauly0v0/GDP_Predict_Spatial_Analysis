# db_utils.py - 数据库工具和通用数据处理

import flask_sqlalchemy
from sqlalchemy import create_engine, text, cast, String, or_
import decimal
import hashlib
from config import MYSQL_URI, TARGET_TABLES, TEXT_COLS

db = flask_sqlalchemy.SQLAlchemy()
TableMap = {}


def reflect_tables(app):
    """反射目标数据库表结构"""
    with app.app_context():
        meta = db.MetaData()
        meta.reflect(bind=db.engine)
        for tbl in TARGET_TABLES:
            # 确保表名在数据库中存在，避免出错
            if tbl in meta.tables:
                 TableMap[tbl] = db.Table(tbl, meta, autoload_with=db.engine)


def init_db_engine():
    """初始化 SQLAlchemy 引擎"""
    try:
        engine = create_engine(
            MYSQL_URI.replace('mysql+pymysql://', 'mysql+pymysql://', 1), 
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        return engine
    except Exception as e:
        print(f"数据库引擎初始化失败: {e}")
        return None


def format_numeric_value(value):
    """智能格式化数值，根据实际小数位数处理"""
    if value is None:
        return None

    if isinstance(value, decimal.Decimal):
        value = float(value)

    if isinstance(value, int):
        return str(value)

    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        else:
            str_value = str(value)
            if '.' in str_value:
                decimal_part = str_value.split('.')[1]
                significant_decimals = len(decimal_part.rstrip('0'))
                decimals_to_keep = min(significant_decimals, 4)
                return f"{value:.{decimals_to_keep}f}"
            else:
                return str(int(value))

    if isinstance(value, str):
        str_value = value.strip()
        if not str_value: return value
        try:
            if '.' not in str_value:
                return str(int(float(str_value)))
            float_value = float(str_value)
            if float_value.is_integer():
                return str(int(float_value))
            else:
                if '.' in str_value:
                    original_decimals = len(str_value.split('.')[1].rstrip('0'))
                    decimals_to_keep = min(original_decimals, 4)
                    return f"{float_value:.{decimals_to_keep}f}"
                else:
                    return str(int(float_value))
        except (ValueError, TypeError):
            return value

    return str(value)


def row2dict(row, columns):
    """将行数据转换为字典，并格式化数值"""
    result = {}
    for col in columns:
        value = getattr(row, col)
        if col not in TEXT_COLS:
            result[col] = format_numeric_value(value)
        else:
            result[col] = value
    return result


def fake_pk(row, columns):
    """生成一个简单的MD5哈希作为伪主键"""
    # 排除geometry列 (针对GIS数据，虽然这里的数据表里没有)
    raw = '|'.join(str(getattr(row, c)) for c in columns if c not in ['geometry'])
    return hashlib.md5(raw.encode()).hexdigest()

# ----------------- 基础路由函数 -----------------

def list_tables_route():
    """返回所有目标表的名称和对应的API路径"""
    from config import UNIT_MAP # 运行时导入，避免循环依赖
    tables_info = []
    for tbl_name in TARGET_TABLES:
        api_path = f'/api/{tbl_name}'
        unit = UNIT_MAP.get(tbl_name, '')
        tables_info.append({
            'name': tbl_name,
            'api_base_path': api_path,
            'unit': unit
        })
    return tables_info

def list_data_route(table_name, request, db):
    """查询并返回列表数据"""
    if table_name not in TableMap:
        return {'code': 404, 'msg': '表不存在'}, 404
    tbl = TableMap[table_name]
    cols = [c.name for c in tbl.columns]
    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 50))
    search = request.args.get('search', '').strip()

    stmt = tbl.select()
    if search:
        like_str = f'%{search}%'
        # 只对字符串类型列进行模糊搜索
        str_cols = [c for c in tbl.columns if str(c.type) == 'VARCHAR']
        if str_cols:
            stmt = stmt.where(
                or_(*[cast(c, String).like(like_str) for c in str_cols]))

    total = db.session.execute(
        stmt.with_only_columns(db.func.count()).order_by(None)).scalar()
    rows = db.session.execute(
        stmt.offset((page - 1) * size).limit(size)).all()

    data = []
    for r in rows:
        d = row2dict(r, cols)
        d['_pk'] = fake_pk(r, cols)
        data.append(d)

    return {'code': 0, 'msg': 'ok', 'data': data, 'total': total}, 200

def one_data_route(table_name, pk, db):
    """查询并返回单条数据"""
    if table_name not in TableMap:
        return {'code': 404, 'msg': '表不存在'}, 404
    tbl = TableMap[table_name]
    cols = [c.name for c in tbl.columns]
    for row in db.session.execute(tbl.select()).all():
        if fake_pk(row, cols) == pk:
            return {'code': 0, 'msg': 'ok', 'data': row2dict(row, cols)}, 200
    return {'code': 404, 'msg': '记录不存在'}, 404