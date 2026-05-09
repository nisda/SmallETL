from typing import Dict

from .const import SafeFunctions
from ...libs.syntax.evaluater import Evaluater



#-------------------------
# フォーマッタ
#-------------------------
evaluater = Evaluater(
    funcs=SafeFunctions.SAFE_FUNCITONS,
    dot_access=True)

