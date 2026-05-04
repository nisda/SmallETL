from typing import List, Dict, Tuple, Any, Callable
from enum import Enum
import inspect
import functools
from  datetime import datetime, timedelta



#-------------------
# 定数
#-------------------

# 定数クラス
class _Const(object):
    __keyword:Any
    def __init__(self, keyword:Any):
        self.__keyword = keyword
    def __bool__(self) -> bool:
        return bool(self.__keyword)

# 定数
class Const(Enum):
    CacheNotSet:_Const = _Const(keyword=None)


#--------------------------------------
# Core
#--------------------------------------
class CacheContianerCore:
    __Container: Dict[Any, Tuple[Any, datetime]] = {}

    def clear(self):
        """キャッシュデータ全削除"""
        self.__Container = {}


    def delete(self, key:Any):
        """キャッシュデータ削除"""
        key_hash = self.__to_hashable(obj=key)
        value, expire_dt = self.__Container.pop(key_hash, tuple([None, None]))
        if (expire_dt is None) or (expire_dt <= datetime.now()):
            return Const.CacheNotSet
        else:
            return value


    def get(self, key:Any, default:Any=Const.CacheNotSet) -> Any:
        """キャッシュデータ取得"""

        # キーをhash化
        key_hash = self.__to_hashable(obj=key)

        # データ取得
        value, expire_dt =self.__Container.get(key_hash, tuple([None, None]))
        if (expire_dt is None) or (expire_dt <= datetime.now()):
            # 非存在 or 期限切れ
            self.delete(key_hash)
            return default
        else:
            # 存在-> 返却
            return value


    def set(self, key:Any, value:Any, expire:int=-1, force:bool=False) -> Any:
        """キャッシュデータ更新"""

        # キーをhash化
        key_hash = self.__to_hashable(obj=key)

        if force:
            # 強制更新の時は既存を削除
            self.delete(key=key)
        else:
            cache_value = self.get(key)
            if cache_value != Const.CacheNotSet:
                return cache_value

        # 有効なキャッシュがなければ更新
        ret:Any = value() if isinstance(value, Callable) else value
        expire_dt:datetime = datetime.max if expire < 0 else datetime.now() + timedelta(seconds=expire)
        self.__Container[key_hash] = tuple([ret, expire_dt])

        # 結果を返却
        return ret



    def __to_hashable(self, obj) -> Any:
        """汎用ハッシュ化関数"""

        if isinstance(obj, dict):
            return tuple(sorted((k, self.__to_hashable(v)) for k, v in obj.items()))     
        elif isinstance(obj, list):
            return tuple(self.__to_hashable(i) for i in obj)
        else:
            return f"{type(obj)}:{obj}"


#--------------------------------------
# Static（singleton）
#--------------------------------------
class CacheContainer:
    __core:CacheContianerCore = CacheContianerCore()

    @classmethod
    def clear(cls):
        return cls.__core.clear()

    @classmethod
    def delete(cls, key:Any) -> None:
        return cls.__core.delete(key=key)
    
    @classmethod
    def get(cls, key:Any, default:Any=Const.CacheNotSet) -> Any:
        return cls.__core.get(key=key, default=default)

    @classmethod
    def set(cls, key:Any, value:Any, expire:int=-1, force:bool=False) -> Any:
        return cls.__core.set(key=key, value=value, expire=expire, force=force)





#--------------------------------------
#   デコレータ
#--------------------------------------
def deco_local_mem_cache(expire:int=-1, key_args:List[str]=None, force_arg:str=None):
    """
    functionキャッシュデコレータ
    ---
    このデコレータを付与したfunctionは結果をキャッシュし、再実行をスキップする。
    
    :param expire: 有効期限（秒）
    :type expire: int
    :param key_args: 
        キャッシュ判定args名。
        指定argsがすべて一致していたらキャッシュを利用する。
        未指定時は全args。
    :type key_args: List[str]
    :param force_arg:
        ここで指定されたキーが True (not-empty) である場合は、キャッシュを利用せず強制的に再実行する。
        key_argsからは自動的に除外される。
    :type force_arg: str
    """

    class __CacheContainer():
        core: CacheContianerCore = CacheContianerCore()

    def __wrapper(func:Callable):

        @functools.wraps(func)
        def __inner(*args, **kwargs):
            # args 情報を取得
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            func_args_all = bound_args.arguments

            # cacheキーを構築
            cache_key_args:Dict = {
                k:v for k,v in func_args_all.items()
                if ( (key_args is None) or (k in key_args) ) \
                and ( (force_arg is None) or ( k != force_arg) )
            }
            cache_key:Dict = {"id": id(func), "func": func.__name__, "args": cache_key_args}

            # force フラグ判定
            force_flg:bool = bool(func_args_all.get(force_arg, False))

            # function 呼び出し（キャッシュ有効）
            ret = __CacheContainer.core.set(
                key=cache_key,
                value=lambda: func(*args, **kwargs),
                expire=expire,
                force=force_flg,
            )

            # 返却
            return ret

        return __inner
    return __wrapper


