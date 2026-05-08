from typing import Final, Dict, List, Any, Literal
from enum import StrEnum, auto
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING


#---------------------------------------
#   終了コード
#---------------------------------------
class ExitCode(StrEnum):
    Succeeded = auto()
    Aborted = auto()




#---------------------------------------
# SAFE_FUNCTION用 カスタム関数
#---------------------------------------

# 関数の一覧はここでいいが、関数の実体は別モジュールにすべき。

def __num_to_num(value:Any, digit:int=None, rounding:Literal['round', 'floor', 'ceil']='round') -> int|float:
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

def __lookup(items:List[Dict], lookup_key:str, lookup_value:str, pickup_key:str=None, default:Any=None) -> Any:
    for item in items:
        if lookup_key in item.keys() and item[lookup_key] == lookup_value:
            if pickup_key:
                return item.get(pickup_key, default)
            else:
                return item
    else:
        return default


# format で使用できる関数
SAFE_FUNCITONS:Final[Dict[str, Any]] = {
    # ビルトイン関数
    "str" : None,
    "int" : None,
    "float" : None,
    "bool" : None,
    "len" : None,
    "max" : None,
    "min" : None,
    "sum" : None,
    "abs" : None,
    "hex" : None,
    "oct" : None,
    "bin" : None,

    # カスタム関数
    "round" : (lambda value, digit=0: __num_to_num(value, digit, 'round')),
    "floor" : (lambda value, digit=0: __num_to_num(value, digit, 'floor')),
    "ceil" : (lambda value, digit=0: __num_to_num(value, digit, 'ceil')),
    "type" : (lambda value: type(value).__name__),
    "lookup" : __lookup,
}






