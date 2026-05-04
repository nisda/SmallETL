import pytest
from local_mem_cache import deco_local_mem_cache
import time
from datetime import datetime
import uuid



@deco_local_mem_cache(key_args=["a"])
def func_key_one(a:int=1, b:int=2, c:int=3):
    return (a + b) * c

@deco_local_mem_cache(key_args=["a", "b"])
def func_key_two(a:int=1, b:int=2, c:int=3):
    return (a + b) * c



def test_simply():
    """追加パラメータなし"""

    @deco_local_mem_cache()
    def func_uuid():
        return uuid.uuid4()

    ret_1 = func_uuid()
    ret_2 = func_uuid()
    ret_3 = func_uuid()
    assert ret_1 == ret_2
    assert ret_1 == ret_3



def test_param():
    """Functionのパラメータあり"""

    @deco_local_mem_cache()
    def func_uuid(p1=1, p2=2):
        return uuid.uuid4()

    # param が同じならキャッシュされる
    ret_1 = func_uuid()
    ret_2 = func_uuid()
    assert ret_1 == ret_2

    ret_1 = func_uuid(p1=2, p2=4)
    ret_2 = func_uuid(p1=2, p2=4)
    assert ret_1 == ret_2

    # デフォルト値を含めて同一であればキャッシュを利用
    ret_1 = func_uuid()
    ret_2 = func_uuid(p1=1, p2=2)
    assert ret_1 == ret_2

    # パラメータが違えば別キャッシュ
    ret_1 = func_uuid(p1=1, p2=2)
    ret_2 = func_uuid(p1=2, p2=2)
    assert ret_1 != ret_2

    # パラメータが違えば別キャッシュ　その２
    ret_1 = func_uuid()
    ret_2 = func_uuid(p1=1, p2=1)
    assert ret_1 != ret_2


def test_expire():
    """有効期限あり"""

    @deco_local_mem_cache(expire=0.5)
    def func_uuid(p1=1, p2=2):
        return uuid.uuid4()

    ret_1 = func_uuid()
    time.sleep(0.1)
    ret_2 = func_uuid()
    assert ret_1 == ret_2

    time.sleep(0.5)
    ret_3 = func_uuid()
    assert ret_1 != ret_3


def test_key_args():
    """
    キー指定あり
    ---
    パラメータのうち指定のキーだけをキャッシュキーとして使用する。
    """

    @deco_local_mem_cache(key_args=["p1", "p2"])
    def func_uuid(p1, p2, p3="c"):
        return uuid.uuid4()

    # 全部同一
    ret_1 = func_uuid(p1="a", p2="b")
    ret_2 = func_uuid(p1="a", p2="b", p3="c")
    assert ret_1 == ret_2

    # 指定キーは同一、他は異なる -> キー一致なのでキャッシュ利用
    ret_1 = func_uuid(p1="a", p2="b", p3="C")
    ret_2 = func_uuid(p1="a", p2="b", p3="c")
    assert ret_1 == ret_2

    # 指定キーが異なる
    ret_1 = func_uuid(p1="a", p2="b", p3="c")
    ret_2 = func_uuid(p1="a", p2="B", p3="c")
    assert ret_1 != ret_2


def test_force():

    # arg=fk が強制キー
    @deco_local_mem_cache(force_arg="force")
    def func_uuid(p1="a", p2="b", force=None):
        ret = uuid.uuid4()
        return ret

    # 同一キーのためキャッシュ
    ret_1 = func_uuid(p1="a")
    ret_2 = func_uuid(p1="a", p2="b")
    assert ret_1 == ret_2

    # 同一キーだが強制キーがセットされたので変更
    ret_3 = func_uuid(p1="a", p2="b", force=True)
    assert ret_2 != ret_3
    ret_4 = func_uuid(p1="a", p2="b", force=1)
    assert ret_3 != ret_4
    ret_5 = func_uuid(p1="a", p2="b", force="a")
    assert ret_4 != ret_5

    # 強制キー = False パターン
    ret_f1 = func_uuid(p1="a", p2="c", force=True)
    ret_f2 = func_uuid(p1="a", p2="c", force=False)
    assert ret_f1 == ret_f2
    ret_f3 = func_uuid(p1="a", p2="c", force=None)
    assert ret_f1 == ret_f3
    ret_f4 = func_uuid(p1="a", p2="c", force=[])
    assert ret_f1 == ret_f4

