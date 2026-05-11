from typing import Final, List, Dict, Any
import json as origin_json
import re
import os
import glob
from pprint import pprint
from pathlib import Path


class CustomJSONEncoder(origin_json.JSONEncoder):

    __ENCODE_DEFS:Final = {
        ### 全部 __repl__ に任せていいのでは。
        # (datetime.datetime, datetime.date): lambda x: x.isoformat(),
        # datetime.time: lambda x: x.isoformat(),
        # decimal.Decimal: lambda x: float(x) if '.' in str(x) else int(x),
        # uuid.UUID: lambda x: str(x),
        # bytes: lambda x: x.decode(),  # 変換できないものがあるため利用NG
    }

    def default(self, o):
        # 変換定義のあるデータ型はそれに従う。
        for typ, func in self.__ENCODE_DEFS.items():
            if isinstance(o, typ):
                return func(o)
        
        # 既存の方法で処理
        try:
            return super().default(o) 
        except Exception as e:
            pass

        # 変換不能なものは repr, str を返却
        if hasattr(o, "__repr__"):
            return repr(o)
        if hasattr(o, "__str__"):
            return f"{type(o)}:{o}"

        # それもダメなら Exception
        raise TypeError("Type %s not serializable" % type(o))



class JsonEx():


    @staticmethod
    def __convert_jsonc_to_json(jsonc_text:str):
        # 正規表現でコメントを削除
        return re.sub(r'/\*[\s\S]*?\*/|//.*', '', jsonc_text)


    @staticmethod
    def __remove_comments(jsonc_text:str):
        pattern = r'("(?:\\.|[^"\\])*")|/\*[\s\S]*?\*/|//.*'
       
        def replace(match):
            if match.group(1) is not None:
                # 文字列ならそのまま返す（保護）
                return match.group(1)
            else:
                # コメントなら空文字に置換
                return ""

        # re.DOTALL は不要（//.* が改行を超えないようにするため）
        return re.sub(pattern, replace, jsonc_text)



    @staticmethod
    def loads(expr:str) -> str|Dict|List:
        # json_expr:str = JsonEx.__convert_jsonc_to_json(expr)
        json_expr:str = JsonEx.__remove_comments(expr)
        json_obj = origin_json.loads(json_expr)
        return json_obj



    @staticmethod
    def load(path: str, encoding: str = 'utf-8') -> str|Dict|List:
        with open(path, 'r', encoding=encoding) as f:
            src_expr = f.read()
        json_obj = JsonEx.loads(expr=src_expr)
        return json_obj


    @staticmethod
    def dumps(obj:Any, cls=CustomJSONEncoder, indent:int=2, ensure_ascii:bool=False, sort_keys:bool=False, **kwargs) -> str:
        return origin_json.dumps(
            obj,
            cls=cls,
            indent=indent,
            ensure_ascii=ensure_ascii,
            sort_keys=sort_keys,
            **kwargs
        )



    @staticmethod
    def dump(obj:Any, path:str, encoding:str="utf-8", cls=CustomJSONEncoder, indent:int=2, ensure_ascii:bool=False, sort_keys:bool=False, **kwargs):
        with open(path, 'w', encoding=encoding) as f:
            origin_json.dump(
                obj,
                f,
                cls=cls,
                indent=indent,
                ensure_ascii=ensure_ascii,
                sort_keys=sort_keys,
                **kwargs
            )
        return



    @classmethod
    def batch_dump(cls, dir:str, data:Dict[str, Any], dir_exist_ok:bool=True, indent:int=2):
        '''
        一括ファイル出力
        指定フォルダ内に key ごとに json ファイル出力する。
        フォルダ内の既存ファイルはすべて削除する。
        '''

        # フォルダ作成
        os.makedirs(name=dir, exist_ok=dir_exist_ok)

        # フォルダ内をクリーンアップ
        path_pattern: str = os.path.join(dir, "*")
        for file_path in glob.glob(path_pattern):
            os.remove(file_path)

        # キーごとに出力
        for k, v in data.items():
            file_path: str = os.path.join(dir, f"{k}.json")
            with open(file_path, 'w') as f:
                origin_json.dump(v, f, indent=indent, default=cls.default_json_encoder)


    @classmethod
    def batch_load(cls, dir:str, filepattern:str|List[str]=["*.json", "*.jsonc"], encoding:str="utf-8") -> Dict[str, Any]:
        '''
        一括ファイル読込
        指定フォルダ内にある *.json|*.jsonc をすべて読み込む。
        ファイル名を key とした dict を返却する。
        '''

        # filepattern を list 型に揃える
        filepatterns:List[str] = [filepattern] if isinstance(filepattern, str) else filepattern

        # パスを取得
        file_paths:List[Path] = sorted(list(set([
            Path(p)
            for pat in filepatterns
            for p in glob.glob(os.path.join(dir, pat))
        ])))

        # 読み込み
        ret: Dict[str, Any] = {}
        for file_path in file_paths:
            ret[Path.stem] = cls.load_jsonc(file_path, encoding=encoding)

        # 返却
        return ret



#--- ヒント/インテリセンスが対応できないため不採用
# dumps = functools.partial(origin_json.dumps, cls=CustomJSONEncoder)
# dump = functools.partial(origin_json.dump, cls=CustomJSONEncoder)


