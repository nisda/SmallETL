from typing import Final, Dict, List, Any
from enum import StrEnum, auto


#終了コード
class ExitCode(StrEnum):
    Succeeded = auto()
    Aborted = auto()


# format で使用できる Function
SAFE_FUNCITONS:Final[Dict[str, Any]] = {
    "str" : None,
    "int" : None,
    "float" : None,
    "bool" : None,
    "len" : None,
}






