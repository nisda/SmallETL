from typing import Any, List, Dict
from time import sleep

def Pass(*args, **kwargs) -> Dict[str, Any]:
    # 両方入ってくることは無い。
    if args:
        return args
    if kwargs:
        return kwargs


def Sleep(seconds:float) -> float:
    sleep(seconds)
    return seconds

