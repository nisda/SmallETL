
from typing import Tuple, Any, List, Dict, Type, Callable, Literal
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
from uuid import UUID
import builtins


def str_to_str(value:str, spec:str = None):
    if spec:
        return f"{value:{spec}}"
    else:
        return value

def str_to_decimal(value:str, digit:int=None, rounding:Literal['round', 'floor', 'ceil']='round') -> Decimal:
    return decimal_to_decimal(value=Decimal(value), digit=digit, rounding=rounding)

def str_to_float(value:str, digit:int=None, rounding:Literal['round', 'floor', 'ceil']='round') -> float:
    return float(str_to_decimal(value=value, digit=digit, rounding=rounding))

def str_to_int(value:str, rounding:Literal['round', 'floor', 'ceil']='round') -> int:
    return int(str_to_decimal(value=value, digit=0, rounding=rounding))

def str_to_bytes(value:str, encoding:str='utf-8') -> bytes:
    return value.encode(encoding=encoding)

def str_to_datetime(value:str, format:str="iso") -> datetime:
    if format == 'iso':
        return datetime.fromisoformat(value)
    else:
        return datetime.strptime(value, format)

def str_to_date(value:str, format:str="iso") -> date:
    return str_to_datetime(value=value, format=format).date()

def str_to_time(value:str, format:str="%H:%M:%S") -> time:
    return str_to_datetime(value=value, format=format).time()

def str_to_bool(value:str) -> bool:
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    return bool(value)


def decimal_to_decimal(value:Decimal, digit:int=None, rounding:Literal['round', 'floor', 'ceil']='round') -> Decimal:
    
    if not isinstance(digit, int):
        # 丸めなし
        return value
    else:
        # 丸め処理
        rounding_expr:str = ROUND_HALF_UP
        if rounding == "floor":
            rounding_expr = ROUND_FLOOR
        elif rounding == "ceil":
            rounding_expr = ROUND_CEILING
        ret = value.quantize(exp=Decimal("0.1")**digit, rounding=rounding_expr)
        return ret

def decimal_to_float(value:Decimal, digit:int=None, rounding:Literal['round', 'floor', 'ceil']='round') -> float:
    return float(decimal_to_decimal(value=value, digit=digit, rounding=rounding))

def decimal_to_int(value:Decimal, rounding:Literal['round', 'floor', 'ceil']='round') -> int:
    return int(decimal_to_decimal(value=value, digit=0, rounding=rounding))

def decimal_to_str(value:Decimal, spec:str = None):
    if spec:
        return f"{value:{spec}}"
    else:
        return str(value)


def float_to_decimal(value:float, digit:int=None, rounding:Literal['round', 'floor', 'ceil']='round') -> Decimal:
    return decimal_to_decimal(value=Decimal(str(value)), digit=digit, rounding=rounding)

def float_to_float(value:float, digit:int=None, rounding:Literal['round', 'floor', 'ceil']='round') -> float:
    return decimal_to_float(value=Decimal(str(value)), digit=digit, rounding=rounding)

def float_to_int(value:float, rounding:Literal['round', 'floor', 'ceil']='round') -> int:
    return decimal_to_int(value=Decimal(str(value)), rounding=rounding)

def float_to_str(value:float, spec:str = None):
    if spec:
        return f"{value:{spec}}"
    else:
        return str(value)


def int_to_str(value:int, spec:str = None):
    if spec:
        return f"{value:{spec}}"
    else:
        return str(value)

def int_to_bytes(value:int, byteorder:Literal['small', 'big']="big", signed:bool=True) -> bytes:
    bit_len = value.bit_length()
    byte_len = (bit_len + 7) // 8
    return value.to_bytes(length=byte_len, byteorder=byteorder, signed=signed)


def bytes_to_int(value:bytes, byteorder:Literal['small', 'big']="big", signed:bool=True) -> int:
    return int.from_bytes(bytes=value, byteorder=byteorder, signed=signed)

def bytes_to_str(value:bytes, encoding:str="utf-8") -> str:
    return value.decode(encoding=encoding)



def datetime_to_str(value:datetime, format:str="iso") -> str:
    if format == 'iso':
        return value.isoformat()
    else:
        return value.strf(format)

def datetime_to_datetime(dt:datetime, tz:ZoneInfo|str=None, base_tz:ZoneInfo|str='local'):
    # デフォルト戻り値
    ret = dt

    # 現在のTZが未設定であれば、base_tzをセット
    if base_tz and base_tz.lower() != 'local':
        before_tz = base_tz if isinstance(base_tz, ZoneInfo) else ZoneInfo(base_tz)
        is_aware = dt.tzinfo is not None and dt.tzinfo.utcoffset(dt) is not None
        if not is_aware:
            ret = ret.replace(tzinfo=before_tz)

    # tzの指定があれば更新する
    if tz:
        after_tz = tz if isinstance(tz, ZoneInfo) else ZoneInfo(tz)
        ret = ret.astimezone(tz=after_tz)

    return ret



CUSTOM_CONVERTERS:Dict[Tuple[Type|Tuple[Type], Type], Callable] = {
    # str
    (str, str)          : str_to_str,
    (str, Decimal)      : str_to_decimal,
    (str, float)        : str_to_float,
    (str, int)          : str_to_int,
    (str, datetime)     : str_to_datetime,
    (str, date)         : str_to_date,
    (str, time)         : str_to_time,
    (str, bool)         : str_to_bool,

    # Decimal
    (Decimal, Decimal)  : decimal_to_decimal,
    (Decimal, float)    : decimal_to_float,
    (Decimal, int)      : decimal_to_int,
    (Decimal, str)      : decimal_to_str,

    # float
    (float, Decimal)    : float_to_decimal,
    (float, float)      : float_to_float,
    (float, int)        : float_to_int,
    (float, str)        : float_to_str,

    # int
    (int, str)          : int_to_str,

    # datetime/date/time
    (datetime, date)    : lambda x: x.date(),
    (datetime, time)    : lambda x: x.time(),
    (date, datetime)    : lambda x: datetime.combine(x, time()),
    (datetime, datetime) : datetime_to_datetime,
    (datetime, str)     : datetime_to_str,

    # datetime <-> timestamp 
    (datetime, int)     : lambda x: int(x.timestamp()),
    (datetime, Decimal) : lambda x: Decimal(x.timestamp()),
    (datetime, float)   : lambda x: float(x.timestamp()),
    (int, datetime)     : lambda x: datetime.fromtimestamp(x),
    (Decimal, datetime) : lambda x: datetime.fromtimestamp(float(x)),
    (float, datetime)   : lambda x: datetime.fromtimestamp(x),

    # date <-> timestamp 
    (date, int)       : lambda x: int(datetime.combine(x, time()).timestamp()),
    (date, Decimal)   : lambda x: Decimal(datetime.combine(x, time()).timestamp()),
    (date, float)     : lambda x: float(datetime.combine(x, time()).timestamp()),

    # bytes <-> int
    (bytes, str)        : bytes_to_str,
    (bytes, int)        : bytes_to_int,
    (str, bytes)        : str_to_bytes,
    (int, bytes)        : int_to_bytes,
}


class DataConverter:

    @classmethod
    def convert(cls, value:Any, dtype:Type|str, params:str|List|Dict=None):

        # 文字列の場合はデータ型を取得
        if isinstance(dtype, str):
            if dtype in dir(builtins):
                dtype = getattr(builtins, dtype)
            elif dtype.lower() == 'uuid':
                dtype = UUID
            elif dtype.lower() == 'datetime':
                dtype = datetime
            elif dtype.lower() == 'date':
                dtype = date
            elif dtype.lower() == 'time':
                dtype = time
            elif dtype.lower() == 'decimal':
                dtype = Decimal
            else:
                raise TypeError(f"Type `{dtype}` is not supported.")

        # コンバータパラメータ調整
        func_args:List = [] if params is None else []
        func_args:List = [params] if isinstance(params, str) else []
        func_args:List = params if isinstance(params, list) else []
        func_kwargs:Dict = params if isinstance(params, dict) else {}

        # 固定値返却
        if False:
            # 通らないダミーロジック
            pass
        elif dtype == type(None):
            # NoneType の場合は None 固定
            return None
        elif type(value) == dtype and not params:
            # 同タイプかつパラメータ無しの場合は無編集で返却
            return value

        # タイプに応じた変換ロジック
        for key_types, converter in CUSTOM_CONVERTERS.items():
            if key_types[0] == type(value) and key_types[1] == dtype:
                return converter(value, *func_args, **func_kwargs)
        else:
            # それ以外は Type で直接変換
            return dtype(value, *func_args, **func_kwargs)





