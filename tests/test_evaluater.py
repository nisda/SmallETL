import pytest

from typing import Any, List, Dict, Tuple
from decimal import Decimal

from SmallETL.modules.common.shared import evaluater




"""SafeFunctions（いくつかピックアップ）"""
@pytest.mark.parametrize(
    ["expr",  "expected"],
    [
        # ビルトイン関数
        pytest.param("{str(123)}", "123"),
        pytest.param("{float('123')}", 123.0),
        pytest.param("{len([1, 1, 1, 1])}", 4),
        # pytest.param("{map(str, [1, 1, 1, 1])}", ["1", "1", "1", "1"]),   # eval再現が不完全であるため対応不可

        # カスタム関数
        pytest.param("{eav_to_dict(items=[{'nm':'id','val':1}], name_key='nm', value_key='val')}", {'id': 1}),
    ]
)
def test_safe_functions(expr:str, expected:Any):
    mapping_data = {}
    ret = evaluater.format(expr, mapping=mapping_data)
    assert ret == expected
    assert type(ret) == type(expected)

