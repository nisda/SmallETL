import pytest
from local_mem_cache import CacheContainer, CacheContianerCore, Const
import time


def test_simplest():
    cc:CacheContainer = CacheContainer
    cc.clear()

    # 未登録
    ret = cc.get("a")
    assert ret == Const.CacheNotSet

    # 登録
    ret = cc.set("a", "AAA")
    assert ret == "AAA"

    # 取得
    ret = cc.get("a")
    assert ret == "AAA"

    # 再設定（無効）
    ret = cc.set("a", "BBB")
    assert ret == "AAA"

    # 取得
    ret = cc.get("a")
    assert ret == "AAA"


def test_expire():
    cc:CacheContainer = CacheContainer
    cc.clear()

    # マイナスは無期限（最後に再確認）
    ret = cc.set("x", "XXX", expire=-1)
    assert cc.get("x") == "XXX"


    # 有効期限内
    ret = cc.set("a", "AAA", expire=0.5)
    assert cc.get("a") == "AAA"

    # 有効期限藍は再設定されない
    ret = cc.set("a", "BBB", expire=999)
    assert cc.get("a") == "AAA"

    # 期限切れは再設定
    time.sleep(1)
    ret = cc.set("a", "CCC", expire=1)
    assert cc.get("a") == "CCC"

    # 有効期限内
    time.sleep(0.5)
    assert cc.get("a") == "CCC"

    # 期限切れ = None
    time.sleep(1.5)
    assert cc.get("a") == Const.CacheNotSet

    # ゼロは次から使えない（すぐに期限切れ）
    ret = cc.set("z", "ZZZ", expire=0)
    assert ret == "ZZZ"
    assert cc.get("z") == Const.CacheNotSet

    # マイナスは無期限（確認）
    assert cc.get("x") == "XXX"


def test_clear():
    cc:CacheContainer = CacheContainer
    cc.clear()

    cc.set("a", "AAA", expire=60)
    cc.set("b", "BBB", expire=60)
    cc.set("c", "CCC", expire=60)

    # 全クリア
    cc.clear()

    # すべてクリアされている
    assert cc.get("a") == Const.CacheNotSet
    assert cc.get("b") == Const.CacheNotSet
    assert cc.get("c") == Const.CacheNotSet

    # 再設定も可能
    cc.set("a", "AAA", expire=60)
    cc.set("b", "BBB", expire=60)
    cc.set("c", "CCC", expire=60)
    assert cc.get("a") == "AAA"
    assert cc.get("b") == "BBB"
    assert cc.get("c") == "CCC"


def test_delete():
    cc:CacheContainer = CacheContainer
    cc.clear()

    cc.set("a", "AAA")
    cc.set("b", "BBB")

    # 指定キーを削除
    cc.delete("a")

    # 削除されたものは CacheNotSet になる。
    assert cc.get("a") == Const.CacheNotSet
    assert cc.get("b") == "BBB"

    # 存在しないキーでもエラーにはならない。返却値は CacheNotSet
    ret_c = cc.delete("c")
    assert ret_c == Const.CacheNotSet


def test_default():
    cc:CacheContainer = CacheContainer
    cc.clear()
    pass


    # 期限切れ
    cc.set("a", "AAA", expire=0)
    assert "DEFAULT" == cc.get("a", default="DEFAULT")

    # 削除済み
    cc.set("b", "BBB", expire=999)
    cc.delete("b")
    assert "DEFAULT" == cc.get("b", default="DEFAULT")

    # 未登録
    assert "DEFAULT" == cc.get("x", default="DEFAULT")


def test_none():
    cc:CacheContainer = CacheContainer
    cc.clear()

    # None もキャッシュ値として保持されて取得可能（勝手にdefault適用されない）
    cc.set(key="a", value=None, expire=120)
    ret = cc.get(key="a", default="DEFAULT")
    assert ret is None


def test_force_set():
    cc:CacheContainer = CacheContainer
    cc.clear()

    ret = cc.set("a", "AAA", expire=120)
    assert ret == "AAA"

    # 有効期限内でも強制的に更新
    ret = cc.set("a", "BBB", expire=120, force=True)
    assert ret == "BBB"
    assert cc.get("a") == "BBB"


@pytest.mark.parametrize(
    ["input"],
    [
        pytest.param("aaaa"),
        pytest.param(1),
        pytest.param(2.0),
        pytest.param(True),
        pytest.param(None),
        pytest.param(["a", 1, 2.0, True]),
        pytest.param({"a": "AA", "b": 123}),
    ]
)
def test_value_type(input):
    cc:CacheContainer = CacheContainer
    cc.clear()

    cc.set(key="a", value=input)
    ret = cc.get(key="a")
    assert ret == input
    assert type(ret) == type(input)


@pytest.mark.parametrize(
    ["input"],
    [
        pytest.param("aaaa"),
        pytest.param(1),
        pytest.param(2.0),
        pytest.param(True),
        pytest.param(None),
        pytest.param(["a", 1, 2.0, True]),
        pytest.param({"a": "AA", "b": 123}),
        pytest.param({"a", 1, 2.0, True}),
    ]
)
def test_key_type(input):
    cc:CacheContainer = CacheContainer
    cc.clear()

    # キーがstr型以外でも機能する。
    cc.set(key=input, value=input)
    ret = cc.get(key=input)
    assert ret == input
    assert type(ret) == type(input)


def test_func():
    cc:CacheContainer = CacheContainer
    cc.clear()

    # ファンクションも可。実行結果が保存される。
    cc.set(key="func", value=lambda: 2**2 ,expire=0.1)
    ret = cc.get(key="func")
    assert ret == 4

    # 有効期限内=実行されない
    cc.set(key="func", value=lambda: 3**2)
    ret = cc.get(key="func")
    assert ret == 4

    # 期限切れ -> 再実行
    time.sleep(0.2)
    cc.set(key="func", value=lambda: 4**2)
    ret = cc.get(key="func")
    assert ret == 16


def test_core():
    # Core はインスタンス化して使用。
    # 別領域に管理したい場合に使用。
    cc1:CacheContianerCore = CacheContianerCore()
    cc2:CacheContianerCore = CacheContianerCore()
    cc1.clear()
    cc2.clear()

    cc1.set(key="a", value="aaaaa")
    cc2.set(key="a", value="AAAAA")

    # インスタンスが別なら同キー名でも別管理
    assert cc1.get(key="a") == "aaaaa"
    assert cc2.get(key="a") == "AAAAA"

    cc1.delete(key="a")
    assert cc1.get(key="a") == Const.CacheNotSet
    assert cc2.get(key="a") == "AAAAA"



