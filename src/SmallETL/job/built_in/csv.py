import logging
import csv
from typing import Any, List, Dict, Union
from collections import OrderedDict


logger = logging.getLogger(__name__)
 

QUOTING:Dict = {
    "QUOTE_ALL" : csv.QUOTE_ALL,
    "QUOTE_MINIMAL" : csv.QUOTE_MINIMAL,
    "QUOTE_NONNUMERIC" : csv.QUOTE_NONNUMERIC,
    "QUOTE_NONE" : csv.QUOTE_NONE,
    # "QUOTE_NOTNULL": csv.QUOTE_NOTNULL,   # Added in version 3.12.
    # "QUOTE_STRINGS": csv.QUOTE_STRINGS,   # Added in version 3.12.
}

def __get_quoting(quoting_expression:Union[str,int]) -> int:
    if isinstance(quoting_expression, str):
        return QUOTING[quoting_expression]
    else:
        return quoting_expression

def load(input:None, path:str, encoding:str = 'utf-8', has_header:int = 1, quotechar='"', delimiter=',', lineterminator='\n', fieldnames:List[str]=None) -> List[Dict[str, str]]:
    '''CSV読み込み'''

    # option を整形
    csv_options:Dict = {
        "delimiter"         : delimiter,
        "lineterminator"    : lineterminator,
        "quotechar"         : quotechar
    }

    lines:List[List[str]] = []
    headers: List[str] = None
    with open(path, "r", encoding=encoding) as f:
        reader = csv.reader(f, **csv_options)
        if has_header == 1:
            headers = next(reader)
        lines = list(reader)

    ret: Dict[str, str] = None
    if fieldnames is not None:
        # column_names の指定がある場合はそれを key に設定。
        logger.debug(f"column_name: {fieldnames}")
        ret = [ dict(zip(fieldnames, x)) for x in lines ]
    elif headers is not None:
        # ヘッダ行ありの場合はそれを key に設定。
        logger.debug(f"headers: {headers}")
        ret = [ dict(zip(headers, x)) for x in lines ]
    else:
        # いずれも指定無しの場合は番号（0から開始）を key に設定。
        logger.debug(f"headers: <None>")
        ret = [ dict(zip(range(0, len(x)), x)) for x in lines ]

    return ret


def save(input:List[Dict[Any, Any]], path:str, encoding:str = 'utf-8', quotechar='"', delimiter=',', lineterminator='\n', quoting = csv.QUOTE_NONNUMERIC, fieldnames:List[str]=None):
    '''CSV書き込み'''

    # option を整形
    csv_options:Dict = {
        "delimiter"         : delimiter,
        "lineterminator"    : lineterminator,
        "quotechar"         : quotechar,
        "quoting"           : __get_quoting(quoting),
    }

    # fieldnames 未指定時は抽出
    if fieldnames is None:
        fieldnames = OrderedDict({ k:None for x in input for k in x.keys() }).keys()

    # CSVファイルを書き込みモードで開く
    with open(path, 'w', encoding=encoding, newline="") as f:

        # DictWriterオブジェクトを作成
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore', **csv_options)

        # ヘッダ行を書き込む
        writer.writeheader()

        # 各行のデータを書き込む
        for row in input:
            writer.writerow(row)

    # 正常終了
    return None
