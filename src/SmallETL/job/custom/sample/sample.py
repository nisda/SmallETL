from typing import Any


def echo(*args, **kwargs) -> Any:
    # 両方入ってくることは無い。
    if args:
        print(f"echo.args = {args}")
        return args
    if kwargs:
        print(f"echo.kwargs = {kwargs}")
        return kwargs
