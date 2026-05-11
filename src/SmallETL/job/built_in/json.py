from typing import Any, Dict, List
from .core.json_ex import JsonEx


def dump(obj:Any, path:str, encoding:str="utf-8"):
    return JsonEx.dump(obj, path, encoding)

def load(path: str, encoding: str = 'utf-8') -> str|Dict|List:
    return JsonEx.load(path, encoding)

