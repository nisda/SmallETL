from typing import List, Dict, Any, Literal, Type

from ...libs.data_table import DataTable



def filter(data:Any, condition:Dict[str, Any]|List[Dict[str, Any]]):
    """フィルタリング（条件抽出）"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.filter(condition=condition)
    return dt_out.rows()



def grouping(data:Any, group_by:List[str]=[], aggregation:Dict[str, str]={}):
    """グルーピング"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.group_by(group_by=group_by, aggregation=aggregation)
    return dt_out.rows()



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
    return dt_out.rows()



def sort(data, sort_by:List[str]):
    """ソート"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.sort(sort_by=sort_by)
    return dt_out.rows()



def convert(
        data,
        column :str = None,
        dtype :str|Type = None,
        params :str|list|dict = None,
        is_null :Any = None,
        null_if :Any = None,
        errors :Literal['raise', 'coerce', 'ignore'] = 'raise',
        error_data: List[Any] = None,
        repeat: List[Dict] = None,  # 繰り返し処理用のパラメータ。
    ):
    """データ変換"""

    params_:Dict[str, Any] = locals()
    data = params_.pop("data")
    repeat = params_.pop("repeat")

    # パラメータをリスト形式に揃える。
    if not repeat:
        repeat = [params_]

    # テーブル生成
    dt_in = DataTable(data=data)

    # 繰り返し処理
    error_list = []
    for param in repeat:
        key = param["column"]
        error_data = []
        # 変換実行
        dt_in[key] = dt_in.convert(**param, error_data=error_data)
        error_list.append(error_data)

    dt_out = dt_in.convert(**params_)
    return dt_out.rows()


def rename(data, columns:Dict|List):
    """カラム名リネーム"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.rename(columns=columns)
    return dt_out.rows()


