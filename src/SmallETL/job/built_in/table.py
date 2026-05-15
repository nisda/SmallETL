from typing import List, Dict, Any, Literal, Type, Tuple
from collections import defaultdict

from .core.data_table import DataTable

"""内部関数：指定出力フォーマットに従って結果出力"""
def __return_as(dt:DataTable, return_as:str):

    # データ型チェック＆調整
    if return_as is None:
        specs = []
    if isinstance(return_as, (List, Tuple)):
        specs = return_as
    elif isinstance(return_as, str):
        specs = return_as.split(',')
    else:
        raise TypeError(f"The data type for `return_as <{type(return_as).__name__}>` is invalid. Only `str` or `list` is expected.")

    # 空データ除去
    specs = [ v.strip().lower() for v in specs if v.strip() ]

    # 指定フォーマットに合わせて DataTable から返却値を取得。
    # dict,rows がデフォルト
    dtype:str = 'list' if 'list' in specs else 'dict'
    ret = dt.cols(type=dtype) if 'cols' in specs \
            else dt.rows(type=dtype)

    return ret





def nop(data:Any, return_as:str="dict,rows"):
    """何もしない。出力形式の変更のみ可能。"""
    dt = DataTable(data=data)
    return __return_as(dt, return_as)



def filter(
        data:Any,
        match_with:Dict[str, Any]|List[Dict[str, Any]] = {},
        mismatch_with:Dict[str, Any]|List[Dict[str, Any]] = {},
        return_as:str="dict,rows"):

    """フィルタリング（条件抽出）"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.filter(match_with=match_with, mismatch_with=mismatch_with)
    return __return_as(dt_out, return_as)




def grouping(data:Any, group_by:List[str]=[], aggregation:Dict[str, str]={}, return_as:str="dict,rows"):
    """グルーピング"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.group_by(group_by=group_by, aggregation=aggregation)
    return __return_as(dt_out, return_as)



def join(
        data_left,
        data_right,
        how:Literal["inner", "left", "right", "full", "cross"],
        left_on:List[str]=None,
        right_on:List[str]=None,
        left_prefix:str='left_',
        right_prefix:str='right_',
        return_as:str="dict,rows",
    ):
    """join"""
    
    left_on   = [left_on] if isinstance(left_on, str) else left_on
    right_on  = [right_on] if isinstance(right_on, str) else right_on

    dt_left = DataTable(data=data_left)
    dt_right = DataTable(data=data_right)

    dt_out = dt_left.join(
        table           = dt_right,
        how             = how,
        left_on         = left_on,
        right_on        = right_on,
        left_prefix     = left_prefix,
        right_prefix    = right_prefix,
    )

    return __return_as(dt_out, return_as)



def sort(data, sort_by:List[str], return_as:str="dict,rows"):
    """ソート"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.sort(sort_by=sort_by)
    return __return_as(dt_out, return_as)



def convert(
        data,
        column :str = None,
        dtype :str|Type = None,
        params :str|list|dict = None,
        is_null :Any = None,
        null_if :Any = None,
        errors :Literal['raise', 'coerce', 'ignore'] = 'raise',
        return_as:str="dict,rows",
    ):
    """データ変換"""

    # テーブル生成
    dt = DataTable(data=data)

    # 繰り返し処理
    error_data = []

    # 変換実行
    dt[column]   = dt.convert(
        column      = column,
        dtype       = dtype,
        params      = params,
        is_null     = is_null,
        null_if     = null_if,
        errors      = errors,
        error_data  = error_data,
    )

    return {
        "output" : __return_as(dt, return_as),
        "errors" : error_data,  # error_dataのreturn_asをどうするかは悩みどころ。
    }



def convert_multiple(data, params:List[Dict], return_as:str="dict,rows"):
    """データ変換（複数回一括）"""

    errors: List = []
    for param in params:
        # カラム名が必要であるため繰り返し中の return_as は固定
        ret = convert(data, **param, return_as="dict,rows")
        # 結果を置き換え
        data = ret["output"]
        errors.append(ret["errors"])

    # 返却
    dt = DataTable(data=data)
    return {
        "output" : __return_as(dt, return_as),
        "errors" : errors,
    }



def rename(data, columns:Dict|List, return_as:str="dict,rows"):
    """カラム名リネーム"""
    dt_in = DataTable(data=data)
    dt_out = dt_in.rename(columns=columns)
    return __return_as(dt_out, return_as)



def explode(data, keys:List[str], sep:str='_', return_as:str="dict,rows"):
    if isinstance(keys, str):
        keys = [keys]

    dt = DataTable(data=data)
    for key in keys:
        dt = dt.explode(key=key, sep=sep)
    return __return_as(dt, return_as)



def eav_to_dict(data:List[List[Dict]], name_key:str, value_key:str, remove_null:bool=True) -> List[Dict]:
    """EntittyAttributeValue のリストをdictに変換"""

    ret:List[Dict] = []
    for items in data:
        # ひとまずすべての要素を list で登録しておく
        temp:Dict[str, Any] = defaultdict(list)
        for eav_item in items:
            if name_key in eav_item.keys():
                key = eav_item.get(name_key)
                temp[key].append(eav_item.get(value_key, None))

        # 要素が1つだけの項目は list の１要素目のみをセットする（元に戻す）
        record = { k: ( v[0] if len(v) == 1 else v) for k,v in temp.items() }

        # remove_null=True の場合は、リスト項目から None を除外
        # ※結果として要素が１つになってもリスト構造は維持する。
        if remove_null:
            record = {
                k: (v) for k, v in temp.items()
            }

        ret.append(record)

    return ret