
from typing import List, Dict, Any, Literal, Type, Tuple
from string import Formatter
from pprint import pprint
from types import SimpleNamespace
from decimal import Decimal
from .path_util import get_nested_data
import re
import ast



def extract_placeholders(expr:str|Dict|List|Tuple, /) -> List[str]:
    """exprに含まれるすべてのプレースホルダ―をリスト化（再帰実行）"""

    def __extract_from_str(expr:str) -> List[str]:
        ret = []
        for (literal_text, field_name, format_spec, conversion) in Formatter().parse(expr):
            print(f"*** {literal_text} | {field_name} | {format_spec} | {conversion}")
            if field_name:
                ret.append(field_name)
            if format_spec:
                ret.extend(__extract_from_str(format_spec))
        return ret

    # 再帰実行
    if expr is None:
        ret = []
    elif isinstance(expr, dict):
        ret =  [ p for v in expr.values() for p in extract_placeholders(v) ]
    elif isinstance(expr, (list, tuple)):
        ret =  [ p for v in expr for p in extract_placeholders(v) ]
    elif isinstance(expr, str):
        ret =  __extract_from_str(expr)
    else:
        ret = []

    # ユニーク化して返却
    return list(dict.fromkeys(ret))


def convert_placeholders(expr:str, /) -> List[str]:
    def __convert(expr:str) -> str:
        s = expr
        # s = re.sub(r'\.([a-zA-Z0-9_]+)', r'[\1]', expr)
        s = re.sub(r'\.([^\[\]\.]+)', r'[\1]', expr)
        return s

    if expr is None:
        return None

    buf = []
    for (literal_text, field_name, format_spec, conversion) in Formatter().parse(expr):
        # print(f"  [debug] {literal_text}, {field_name}, {format_spec}, {conversion}")
        literal_text = literal_text or ""
        if field_name:
            field_name = __convert(field_name) or ""
            format_spec = convert_placeholders(format_spec)
            format_spec = ":" + format_spec if format_spec else ""
            conversion = "!" + conversion if conversion else ""
            buf.append(f"{literal_text}{{{field_name}{format_spec}{conversion}}}")
        else:
            # print("[debug] field_name is none")
            # エスケープが外れているため復元する。
            if literal_text.endswith("{"):
                buf.append(literal_text + "{")
            elif literal_text.endswith("}"):
                buf.append(literal_text + "}")
            else:
                buf.append(literal_text)

    return "".join(buf)


def is_fieldname_only(expr:str, /) -> bool:
    try:
        # format(expr) を分解
        elements = [
            dict(zip(['literal_text', 'field_name', 'format_spec', 'conversion'], p))
            for p in Formatter().parse(expr)
        ]
        # １要素のみ且つ field_name のみである
        ret = bool(
            len(elements) == 1
            and not elements[0]['literal_text']
            and not elements[0]['format_spec']
            and not elements[0]['conversion']
            and elements[0]['field_name']
        )
        return ret
    except Exception as e:
        return False


def format(expr:str, /, data:Dict[str, Any]) -> str:
    """フォーマット"""
    corrected = convert_placeholders(expr)
    return corrected.format_map(data)


def data_mapping(
        template:str,
        data:Dict[str, Any],
        errors:Literal['raise', 'coerce', 'ignore']='raise',
        assign_dtype:Literal['original', 'str'] = 'original',
    ) -> Any:
    """テンプレートへのデータマッピング"""
    """このライブラリの中にあるべきなのかは別途検討"""

    def __assign_data(expr:str, data):
        try:
            # format 実行
            if assign_dtype == "original" and is_fieldname_only(expr):
                # 変換可能
                return get_nested_data(data=data, path=expr[1:-1])
            else:
                # 変換なし
                try:
                    return format(expr, data)
                except Exception as e:
                    e_type:Type = type(e)
                    e_msg:str   = f"{str(e).rstrip('.')}. occurred at expression='{expr}'"
                    raise e_type(e_msg) from e
        except Exception as e:
            if errors == 'coerce':
                return None
            elif errors == 'ignore':
                return expr
            else:
                raise


    if isinstance(template, dict):
        return {
            k: data_mapping(template=v, data=data, errors=errors, assign_dtype=assign_dtype)
            for k,v in template.items()
        }
    elif isinstance(template, list):
        return [
            data_mapping(template=v, data=data, errors=errors, assign_dtype=assign_dtype)
            for v in template
        ]
    elif isinstance(template, tuple):
        return tuple([
            data_mapping(template=v, data=data, errors=errors, assign_dtype=assign_dtype)
            for v in template
        ])
    elif isinstance(template, str):
        return __assign_data(template, data=data)
    else:
        return template

