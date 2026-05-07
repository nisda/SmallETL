from typing import Dict

from .const import SAFE_FUNCITONS
from ..libs.syntax.evaluater import Evaluater



#-------------------------
# フォーマッタ
#-------------------------
evaluater = Evaluater(
    funcs=SAFE_FUNCITONS,
    dot_access=True)

