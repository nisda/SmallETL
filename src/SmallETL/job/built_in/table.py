from typing import List, Dict, Any, Literal, Type, Tuple

from .core.data_table import DataTable

"""内部関数：指定出力フォーマットに従って結果出力"""
def __output_format(dt:DataTable, output_format:str):

    # データ型チェック＆調整
    if output_format is None:
        specs = []
    if isinstance(output_format, (List, Tuple)):
        specs = output_format
    elif isinstance(output_format, str):
        specs = output_format.split(',')
    else:
        raise TypeError(f"The data type for `output_format <{type(output_format).__name__}>` is invalid. Only `str` or `list` is expected.")

    # 空データ除去
    specs = [ v.strip().lower() for v in specs if v.strip() ]

    # 指定フォーマットに合わせて DataTable から返却値を取得。
    # dict,rows がデフォルト
    dtype:str = 'list' if 'list' in specs else 'dict'
    ret = dt.cols(type=dtype) if 'cols' in specs \
            else dt.rows(type=dtype)

    return ret





def nop(data:Any, output_format:str="dict,rows"):
    """何もしない。出力形式の変更のみ可能。"""
    dt = DataTable(data=data)
    return __output_format(dt, output_format)



def filter(data:Any, condition:Dict[str, Any]|List[Dict[str, Any]], output_format:str="dict,rows"):
    """フィルタリング（条件抽出）"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.filter(condition=condition)
    return __output_format(dt_out, output_format)



def filter_multiple(data:Any, conditions:List[Dict[str, Any]|List[Dict[str, Any]]], output_format:str="dict,rows"):
    """フィルタリング（条件抽出）複数"""
    dt = DataTable(data=data)
    for condition in conditions:
        dt = dt.filter(condition=condition)
    return __output_format(dt, output_format)



def grouping(data:Any, group_by:List[str]=[], aggregation:Dict[str, str]={}, output_format:str="dict,rows"):
    """グルーピング"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.group_by(group_by=group_by, aggregation=aggregation)
    return __output_format(dt_out, output_format)



def join(
        data_left,
        data_right,
        how:Literal["inner", "left", "right", "full", "cross"],
        left_on:List[str]=None,
        right_on:List[str]=None,
        left_prefix:str='left_',
        right_prefix:str='right_',
        output_format:str="dict,rows",
    ):
    """join"""
    params:Dict[str, Any] = locals()
    
    dt_left = DataTable(data=params.pop("data_left"))
    dt_right = DataTable(data=params.pop("data_right"))
    dt_out = dt_left.join(table=dt_right, **params)
    return __output_format(dt_out, output_format)



def sort(data, sort_by:List[str], output_format:str="dict,rows"):
    """ソート"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.sort(sort_by=sort_by)
    return __output_format(dt_out, output_format)



def convert(
        data,
        column :str = None,
        dtype :str|Type = None,
        params :str|list|dict = None,
        is_null :Any = None,
        null_if :Any = None,
        errors :Literal['raise', 'coerce', 'ignore'] = 'raise',
        output_format:str="dict,rows",
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
        "output" : __output_format(dt_in, output_format),
        "errors" : error_data,  # error_dataのoutput_formatをどうするかは悩みどころ。
    }



def convert_multiple(data, params:List[Dict], output_format:str="dict,rows"):
    """データ変換（複数回一括）"""

    errors: List = []
    for param in params:
        # カラム名が必要であるため繰り返し中は output_format 固定
        ret = convert(data, output_format="dict,rows", **param)
        # 結果を保持
        data = ret["output"]
        errors.append(ret["errors"])

    # 返却
    dt = DataTable(data=data)
    return {
        "output" : __output_format(dt, output_format),
        "errors" : errors,
    }



def rename(data, columns:Dict|List, output_format:str="dict,rows"):
    """カラム名リネーム"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.rename(columns=columns)
    return __output_format(dt_out, output_format)



def explode(data, keys:List[str], sep:str='_', output_format:str="dict,rows"):
    if isinstance(keys, str):
        keys = [keys]

    dt = DataTable(data=data)
    for key in keys:
        dt = dt.explode(key=key, sep=sep)
    return __output_format(dt, output_format)


