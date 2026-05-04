from typing import Any


class _DotDictBase(dict):
    def __init__(self, data:dict={}):
        """コンストラクタ"""

        def __convert(data:Any, type_:type) -> Any:
            """再帰的に全dictを変換"""
            if isinstance(data, dict):
                return type_({k: __convert(v, type_) for k, v in data.items()})
            elif isinstance(data, list):
                return [__convert(v, type_) for v in data]
            elif isinstance(data, tuple):
                return tuple([__convert(v, type_) for v in data])
            else:
                return data

        # トップレベルの変換
        converted_data = {
            k: __convert(data=v, type_=type(self))
            for k,v in data.items()
        }

        # 初期化
        super().__init__(converted_data)


def restore_dotdict(data:_DotDictBase|Any):
    """DotDictからのデータ型復元"""

    def __restore(data:Any) -> Any:
        """再帰的に全dictを変換"""
        if isinstance(data, _DotDictBase):
            return {k: __restore(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [__restore(v) for v in data]
        elif isinstance(data, tuple):
            return tuple([__restore(v) for v in data])
        else:
            return data

    return __restore(data=data)


class DotDict1(_DotDictBase):
    def __getattr__(self, item):
        return self[item]
    def __setattr__(self, key, value):
        self[key] = value
    def __delattr__(self, item):
        del self[item]


class DotDict2(_DotDictBase):
  def __getattr__(self, key):
    return self.__getitem__(key)
  def __setattr__(self, key, value):
    self.__setitem__(key, value)
  def __delattr__(self, key):
    self.__delitem__(key)


class DotDict3(_DotDictBase):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class DotDict4(_DotDictBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

