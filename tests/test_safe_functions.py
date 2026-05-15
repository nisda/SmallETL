import pytest

from typing import Any, List, Dict, Tuple
from decimal import Decimal

from SmallETL.modules.common.shared import SafeFunctions


@pytest.mark.parametrize(
    ["value", "digit", "rounding", "expected"],
    [
        # int 型／小数桁の指定なし = 丸めなし
        pytest.param(123, None, "ceil", 123),
        pytest.param(123, None, "floor", 123),

        # int 型で小数桁数指定 = float型になる
        pytest.param(123, 1, "ceil", float(123.0)),

        # float 型／小数桁の指定なし = 丸めなし
        pytest.param(float(234), None, "floor", float(234)),
        pytest.param(234.567, None, "floor", 234.567),

        # float 型／小数桁の指定あり = 指定の方法で丸め
        pytest.param(234.567, 2, "floor", 234.56),
        pytest.param(234.567, 2, "round", 234.57),

        # Decimal 型／小数桁の指定なし = 丸めなし
        pytest.param(Decimal(345)       , None, "ceil", 345),
        pytest.param(Decimal(345.0)     , None, "ceil", 345),
        pytest.param(Decimal(345.678)   , None, "ceil", 345.678),

        # Decimal 型／小数桁の指定あり = 指定の方法で丸め
        pytest.param(Decimal(345.678), 0, "round", 346),
        pytest.param(Decimal(345.678), 1, "ceil" , 345.7),
        pytest.param(Decimal(345.678), 2, "floor", 345.67),

        # str も可
        pytest.param("123"      , None  , "ceil"    , 123),
        pytest.param("123"      , None  , "floor"   , 123),
        pytest.param("123"      , 1     , "ceil"    , float(123.0)),
        pytest.param("234.567"  , None  , "floor"   , 234.567),
        pytest.param("234.567"  , 2     , "floor"   , 234.56),
        pytest.param("234.567"  , 2     , "round"   , 234.57),
    ]
)
def test_num_to_num(value:str|int|float|Decimal, digit:int, rounding:str, expected:int|float):
    ret = SafeFunctions._num_to_num(value=value, digit=digit, rounding=rounding)
    assert ret == expected
    assert type(ret) == type(expected)




@pytest.mark.parametrize(
    ["criteria", "column", "remove_null", "expected"],
    [
        # 条件指定あり
        pytest.param({"name": "berry"}, None, False,
                     [{"id": 4, "name": "berry"   , "color": "black"  , "lot": None}, {"id": 5, "name": "berry"   , "color": "red"    , "lot": 40},]),

        # 複数条件
        pytest.param({"name": "apple", "lot": 16}, None, False,
                     [{"id": 2, "name": "apple"   , "color": "red"    , "lot": 16}, {"id": 3, "name": "apple"   , "color": "green"  , "lot": 16},]),

        # 項目指定（リスト型、複数項目）
        pytest.param({"name": "berry"}, ["name", "color"], False,
                     [{"name": "berry" , "color": "black"}, {"name": "berry", "color": "red"},]),

        # 項目指定（リスト型、１項目）
        pytest.param({"name": "berry"}, ["color"], False,
                     [{"color": "black"}, {"color": "red"},]),

        # 項目指定（str型の単項目）
        pytest.param({"name": "apple"}, "color", False,
                     ["red", "green", None]),

        # 項目指定（str型の単項目）、None除去
        pytest.param({"name": "apple"}, "color", True,
                     ["red", "green"]),

        # 条件なし(None)
        pytest.param(None, "color", False,
                     ["yellow", "red", "green", "black", "red", None, None]),

        # 条件なし(空dict)
        pytest.param({}, "color", False,
                     ["yellow", "red", "green", "black", "red", None, None]),

        # 条件なし(空dict) + None除去
        pytest.param({}, "color", True,
                     ["yellow", "red", "green", "black", "red"]),
    ]
)
def test_lookups(criteria, column, remove_null, expected:Any):
    items = [
        {"id": 1, "name": "banana"  , "color": "yellow" , "lot": 10},
        {"id": 2, "name": "apple"   , "color": "red"    , "lot": 16},
        {"id": 3, "name": "apple"   , "color": "green"  , "lot": 16},
        {"id": 4, "name": "berry"   , "color": "black"  , "lot": None},
        {"id": 5, "name": "berry"   , "color": "red"    , "lot": 40},
        {"id": 6, "name": "melon"   , "color": None     , "lot": 1},
        {"id": 3, "name": "apple"   , "color": None     , "lot": 20},
    ]

    ret = SafeFunctions._lookup(
        items=items,
        criteria=criteria,
        column=column,
        remove_null=remove_null)
    assert ret == expected




@pytest.mark.parametrize(
    ["name_key", "value_key", "return_as", "remove_null", "expected"],
    [

        # デフォルト
        pytest.param("name", "value", "unwrap", True, 
                     {"id": 1, "name": "Alice", "age": None, "category": ["A", "B", "C"]}),

        # None 除去なし
        pytest.param("name", "value", "unwrap", False, 
                     {"id": 1, "name": "Alice", "age": None, "category": ["A", "B", None, "C"]}),

        # return as list
        pytest.param("name", "value", "list", False, 
                     {"id": [1], "name": ["Alice"], "age": [None], "category": ["A", "B", None, "C"]}),

        # return as list で None 除去
        pytest.param("name", "value", "list", True, 
                     {"id": [1], "name": ["Alice"], "age": [], "category": ["A", "B", "C"]}),

    ]
)
def test_eav_to_dict_one(name_key, value_key, return_as, remove_null, expected:Any):
    items = [
        {"name": "id"       , "value": 1        , "type": "int", "required": True},
        {"name": "name"     , "value": "Alice"  , "type": "str", "required": True},
        {"name": "age"      , "value": None     , "type": "int", "required": False},
        {"NAME": "sex"      , "value": "Female" , "type": "str", "required": False},    # name_key 不一致
        {"name": "category" , "value": "A"      , "type": "str", "required": False},
        {"name": "category" , "value": "B"      , "type": "str", "required": False},
        {"name": "category" , "value": None     , "type": "str", "required": False},
        {"name": "category" , "value": "C"      , "type": "str", "required": False},
    ]

    ret = SafeFunctions._eav_to_dict(
        items=items,
        name_key=name_key,
        value_key=value_key,
        return_as=return_as,
        remove_null=remove_null,
    )
    assert ret == expected




@pytest.mark.parametrize(
    ["name_key", "value_key", "return_as", "remove_null", "expected"],
    [

        # デフォルト
        pytest.param("name", "value", "unwrap", True, 
                     [
                         {"id": 1, "name": "Alice", "category": ["A"]},
                         {"id": 2, "name": "Bob"  , "category": ["B"]},
                     ]),

        # 設定変更
        pytest.param("name", "value", "list", False, 
                     [
                         {"id": [1], "name": ["Alice"], "category": ["A", None]},
                         {"id": [2], "name": ["Bob"]  , "category": [None, "B"]},
                     ]),

    ]
)
def test_eav_to_dict_list(name_key, value_key, return_as, remove_null, expected:Any):
    items = [
        [
            {"name": "id"       , "value": 1        , "type": "int", "required": True},
            {"name": "name"     , "value": "Alice"  , "type": "str", "required": True},
            {"name": "category" , "value": "A"      , "type": "str", "required": False},
            {"name": "category" , "value": None     , "type": "str", "required": False},
        ],
        [
            {"name": "id"       , "value": 2        , "type": "int", "required": True},
            {"name": "name"     , "value": "Bob"    , "type": "str", "required": True},
            {"name": "category" , "value": None     , "type": "str", "required": False},
            {"name": "category" , "value": "B"      , "type": "str", "required": False},
        ],
    ]

    ret = SafeFunctions._eav_to_dict(
        items=items,
        name_key=name_key,
        value_key=value_key,
        return_as=return_as,
        remove_null=remove_null,
    )
    assert ret == expected

