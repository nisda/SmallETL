from __future__ import annotations
from typing import TYPE_CHECKING

from typing import final, List, Dict, Set, Any
import logging
import re
from datetime import datetime
from collections import defaultdict
from ..common.shared import evaluater

from .base_model import ComponentBase
from .result_info import TaskResultInfo, TaskStatus

if TYPE_CHECKING:
    from ..workflow import DumpWriter
    from .graph_model import GraphModel





logger = logging.getLogger(__name__)


class EachModel(ComponentBase):
    """フロー制御Eachクラス"""


    @property
    def items(self) -> Any:
        return self.__items

    @property
    def graph(self) -> GraphModel:
        return self.__graph



    def __init__(
        self,
        items:Any,
        graph:List[Dict],
    ):
        logger.info(f"{self.__class__.__name__}.init: items={items}, graph.len={len(graph)}")


        # 循環参照を回避するためここでimport
        from .graph_model import GraphModel

        # 設定
        self.__items = items
        self.__graph = GraphModel(graph_def=graph)



    def _run(
            self,
            task_name:str,
            dump_prefix:str,
            dump_writer:DumpWriter,
            variables:Dict[str, Any],
            payload:Dict[str, Any],
            outputs:Dict[str, Any]
        ) -> Any:
        logger.info(f"[{task_name}] each.run: payload.type:{type(payload).__name__}, payload.len:{len(payload)}")


        #------------------------
        # items を生成（変数割り当て）
        #------------------------
        items:List|Dict = evaluater.format(
            self.items,
            mapping={
                **variables,
                "payload"   : payload,
            },
        )
        logger.info(f"items: type=<{type(items).__name__}>, len={len(items)}")


        #------------------------
        # 変数調整
        #------------------------

        # 現在の each は次の each.parent にセット
        parent_var:Dict[str, Any] = variables.pop("each", {})
        if parent_var:
            parent_var = {
                "parent": parent_var,
            }


        #------------------------
        # 実行
        #------------------------

        # ループ実行
        outputs[self.name] = defaultdict(dict)
        status:TaskStatus = TaskStatus.Succeeded
        for i, item in enumerate(items):

            # キー情報を整理
            key = item if isinstance(items, dict) else i
            current_variables = {
                **variables,
                "each" : {
                    "index" : i,
                    "key"   : key,
                    "value" : items[key],
                    **parent_var,
                },
            }

            # 実行
            task_result = self.graph.run(
                dump_prefix = f"{dump_prefix}[{key}]-",
                dump_writer = dump_writer,
                variables   = current_variables,
                payload     = payload,
                outputs     = outputs[self.name][key],
            )

            if task_result.status == TaskStatus.Stopped:
                status = task_result.status
                break

        ret = TaskResultInfo(
            status=status,
            output=outputs[self.name],
        )

        #------------------------
        # 終了
        #------------------------
        return ret

