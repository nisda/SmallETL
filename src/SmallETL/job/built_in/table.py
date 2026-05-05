from typing import List, Dict, Any, Literal, Type

from .core.data_table import DataTable



def filter(data:Any, condition:Dict[str, Any]|List[Dict[str, Any]]):
    """フィルタリング（条件抽出）"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.filter(condition=condition)
    return dt_out.rows(type='dict')


def filter_multiple(data:Any, conditions:List[Dict[str, Any]|List[Dict[str, Any]]]):
    """フィルタリング（条件抽出）複数"""
    dt = DataTable(data=data)
    for condition in conditions:
        dt = dt.filter(condition=condition)
    return dt.rows(type='dict')


def grouping(data:Any, group_by:List[str]=[], aggregation:Dict[str, str]={}):
    """グルーピング"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.group_by(group_by=group_by, aggregation=aggregation)
    return dt_out.rows(type='dict')



def join(
        data_left,
        data_right,
        how:Literal["inner", "left", "right", "full", "cross"],
        left_on:List[str]=None,
        right_on:List[str]=None,
        left_prefix:str='left_',
        right_prefix:str='right_',
    ):
    """join"""
    params:Dict[str, Any] = locals()
    
    dt_left = DataTable(data=params.pop("data_left"))
    dt_right = DataTable(data=params.pop("data_right"))
    dt_out = dt_left.join(table=dt_right, **params)
    return dt_out.rows(type='dict')



def sort(data, sort_by:List[str]):
    """ソート"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.sort(sort_by=sort_by)
    return dt_out.rows(type='dict')



def convert(
        data,
        column :str = None,
        dtype :str|Type = None,
        params :str|list|dict = None,
        is_null :Any = None,
        null_if :Any = None,
        errors :Literal['raise', 'coerce', 'ignore'] = 'raise',
    ):
    """データ変換"""

    params_:Dict[str, Any] = locals()
    data = params_.pop("data")


    # テーブル生成
    dt_in = DataTable(data=data)

    # 繰り返し処理
    error_data = []

    # 変換実行
    key = params_["column"]
    dt_in[key] = dt_in.convert(**params_, error_data=error_data)

    return {
        "output" : dt_in.rows(type='dict'),
        "errors" : error_data,
    }

def convert_multiple(data, params:List[Dict]):
    """データ変換（複数回一括）"""

    errors: List = []
    for param in params:
        ret = convert(data, **param)
        data = ret["output"]
        errors.append(ret["errors"])

    return {
        "output" : data,
        "errors" : errors,
    }

def rename(data, columns:Dict|List):
    """カラム名リネーム"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.rename(columns=columns)
    return dt_out.rows(type='dict')


def explode(data, keys:List[str], sep:str='_'):
    if isinstance(keys, str):
        keys = [keys]

    dt = DataTable(data=data)
    for key in keys:
        dt = dt.explode(key=key, sep=sep)
    return dt.rows(type='dict')


