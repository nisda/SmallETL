from typing import Any, List, Dict
from time import sleep

def Pass(*args, **kwargs) -> None:
    return [*args, kwargs]

def Sleep(seconds:float) -> None:
    sleep(seconds)
    return None

