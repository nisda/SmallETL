from typing import Final, Dict, List, Tuple, Any, Literal
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
from collections import defaultdict


from ...libs.syntax.evaluater import Evaluater

#-------------------------
# フォーマッタ
#-------------------------
# フォーマッタ（evaluater）用の SAFE_FUNCTION 群
class SafeFunctions():


    @staticmethod
    def _num_to_num(value:Any, digit:int=None, rounding:Literal['round', 'floor', 'ceil']='round') -> int|float:
        """数値の端数処理 & int|float への変換"""

        # 型を揃える
        value = Decimal(str(value))

        if not isinstance(digit, int):
            # 丸めなし
            return float(value) if "." in str(value) else int(value)
        else:
            # 丸め処理
            rounding_expr:str = ROUND_HALF_UP
            if rounding == "floor":
                rounding_expr = ROUND_FLOOR
            elif rounding == "ceil":
                rounding_expr = ROUND_CEILING
            ret = value.quantize(exp=Decimal("0.1")**digit, rounding=rounding_expr)

            if digit == 0:
                return int(ret)
            else:
                return float(ret)


    @staticmethod
    def _lookup(items:List[Dict], criteria:Dict[str,Any]=None, column:str|List[str]=None, remove_null:bool=True):

        columns:List[str] = column if isinstance(column, List) else ( None if column is None else [column])

        # criteria にマッチするデータを抽出
        ret:List[Dict] = []
        for item in items:
            if criteria is None or criteria.items() <= item.items():
                if columns is None:
                    ret.append(item)
                else:
                    ret.append({
                        k:v for k,v in item.items()
                        if k in columns
                    })

        if isinstance(column, List) or column is None:
            # 項目が複数指定されていたらそのまま返却（１項目のList型の場合を含む）
            return ret
        else:
            # 単項目を指定されていた場合は、value のみを List として返却する。
            ret = [ d[column] for d in ret if not (remove_null and d[column] is None) ]
            return ret


    @staticmethod
    def __eav_to_dict_core(attrs:List[Dict], name_key:str, value_key:str, return_as:str, remove_null:bool) -> Dict:

        # すべての要素を list で登録しておく
        ret:Dict[str, Any] = defaultdict(list)
        for attr in attrs:
            # name_key が存在しない場合はスキップ
            if name_key not in attr.keys():
                continue
            # value_key が存在しない場合は None で登録
            key = attr.get(name_key)
            ret[key].append(attr.get(value_key, None))

        # return_as = 'unwrap' のときは１要素のみの値の list 化を解除する。
        if return_as.lower() == 'unwrap':
            ret = {
                k: ( v[0] if len(v) == 1 else v)
                for k,v in ret.items()
            }

        # remove_null=True の場合は、リスト項目から None を除外
        # ※結果として要素が１つまたはゼロになってもリスト構造は維持する。
        if remove_null:
            ret = {
                key: (
                    values if not isinstance(values, List) else [ v for v in values if v is not None]
                )
                for key, values in ret.items()
            }

        # 返却
        return dict(ret)


    @staticmethod
    def _eav_to_dict(items:List[List[Dict]]|List[Dict], name_key:str, value_key:str, return_as:Literal["list", "unwrap"]="unwrap", remove_null:bool=True) -> List[Dict]|Dict:
        """EntittyAttributeValue のリストをdictに変換"""

        error_prefix:str = "eav_to_dict(): "

        # データ型チェック
        if not isinstance(items, (List, Tuple)):
            raise TypeError(f"{error_prefix}Type <{type(items).__name__}> is not supported. Expected <list>.")

        # データ存在チェック
        if len(items) == 0:
            return []

        if isinstance(items[0], Dict):
            # １つめの要素が Dictの場合は １件のEAVデータと見なす。
            return SafeFunctions.__eav_to_dict_core(
                attrs=items,
                name_key=name_key,
                value_key=value_key,
                return_as=return_as,
                remove_null=remove_null,
            )
        elif isinstance(items[0], (List, Tuple)):
            # １つめの要素が Dictの場合は EAVデータのリストと見なす。
            return [
                SafeFunctions.__eav_to_dict_core(
                    attrs=attrs,
                    name_key=name_key,
                    value_key=value_key,
                    return_as=return_as,
                    remove_null=remove_null,
                )
                for attrs in items
            ]
        else:
            raise TypeError(f"{error_prefix}Type <{type(items).__name__}.{type(items[0]).__name__}> is not supported. Expected <list.list.dict> or <list.dict>.")


        # ret:List[Dict] = []
        # for items in data:
        #     # ひとまずすべての要素を list で登録しておく
        #     temp:Dict[str, Any] = defaultdict(list)
        #     for eav_item in items:
        #         if name_key in eav_item.keys():
        #             key = eav_item.get(name_key)
        #             temp[key].append(eav_item.get(value_key, None))

        #     # 要素が1つだけの項目は list の１要素目のみをセットする（元に戻す）
        #     record = { k: ( v[0] if len(v) == 1 else v) for k,v in temp.items() }

        #     # remove_null=True の場合は、リスト項目から None を除外
        #     # ※結果として要素が１つまたはゼロになってもリスト構造は維持する。
        #     if remove_null:
        #         record = {
        #             k: (v) for k, v in temp.items()
        #         }

        #     ret.append(record)

        # return ret


    # format で使用できる関数
    SAFE_FUNCITONS:Final[Dict[str, Any]] = {
        # ビルトイン関数/キャスト
        "str" : None,
        "int" : None,
        "float" : None,
        "bool" : None,
        "hex" : None,
        "oct" : None,
        "bin" : None,
        "list" : None,
        "dict" : None,
        "tuple" : None,
        "set" : None,

        # ビルトイン関数/計算
        "max" : None,
        "min" : None,
        "sum" : None,
        "abs" : None,

        # ビルトイン関数/その他
        "all": None,
        "any": None,
        "len" : None,
        "range": None,
        "map" : None,
        "sorted" : None,
        "reversed" : None,

        # カスタム関数
        "round" : (lambda value, digit=0: SafeFunctions._num_to_num(value, digit, 'round')),
        "floor" : (lambda value, digit=0: SafeFunctions._num_to_num(value, digit, 'floor')),
        "ceil" : (lambda value, digit=0: SafeFunctions._num_to_num(value, digit, 'ceil')),
        "type" : (lambda value: type(value).__name__),
        "lookup" : _lookup,
        "eav_to_dict" : _eav_to_dict,
    }



# フォーマッタ本体
evaluater = Evaluater(
    funcs=SafeFunctions.SAFE_FUNCITONS,
    dot_access=True)

