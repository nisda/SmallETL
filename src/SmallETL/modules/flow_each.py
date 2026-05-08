from __future__ import annotations
from typing import TYPE_CHECKING

from typing import final, List, Dict, Set, Any
import logging
import re
from datetime import datetime
from collections import defaultdict
from .shared import evaluater

from .component_base import ComponentBase, ComponentStatus

if TYPE_CHECKING:
    from .workflow import DumpWriter
    from .graph import GraphInfo





logger = logging.getLogger(__name__)


class FlowEach(ComponentBase):
    """フロー制御Eachクラス"""


    @property
    def items(self) -> Any:
        return self.__items

    @property
    def graph(self) -> GraphInfo:
        return self.__graph




    @final
    def __init__(
        self,
        items:Any,
        graph:List[Dict],
        # 以下、共通パラメータ
        name:str,
        description:str=None,
        depends:List=None,
        condition:str=None,
        parameters:Dict={},
        stop_condition:str=None,
        stop_message:str=None,
    ):
        super().__init__(
            name            = name,
            description     = description,
            depends         = depends,
            condition       = condition,
            parameters      = parameters,
            stop_condition = stop_condition,
            stop_message   = stop_message,
        )
        # -- ここまで共通処理
        # -- 以下、クラス独自処理

        logger.info(f"{self.__class__.__name__}.init: items={items}, graph(len)={len(graph)}")

        # 循環参照を回避するためここでimport
        from .graph import GraphInfo

        # 設定
        self.__items = items
        self.__graph = GraphInfo(graph_def=graph)



    def _run(
            self,
            task_name:str,
            dump_prefix:str,
            dump_writer:DumpWriter,
            variables:Dict[str, Any],
            payload:Dict[str, Any],
            outputs:Dict[str, Any]
        ) -> Any:
        logger.info(f"each.{self.name}.run: payload.type:{type(payload).__name__}, payload.len:{len(payload)}")


        #------------------------
        # items生成
        #------------------------
        items:List|Dict = evaluater.format(
            self.items,
            mapping={
                **variables,
                "payload"   : payload,
            },
        )
        logger.debug(f"items: type={type(items).__name__}, count={len(items)}")


        #------------------------
        # 変数調整
        #------------------------

        # 現在の each は次の each.parent にセット
        parent_var:Dict[str, Any] = variables.get("each", {})
        if parent_var:
            parent_var = {
                "parent": parent_var,
            }


        #------------------------
        # 実行
        #------------------------

        # ループ実行
        status:ComponentStatus = ComponentStatus.Running
        outputs[self.name] = defaultdict(dict)
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
            self.__output = self.graph.run(
                dump_prefix = f"{dump_prefix}[{key}]-",
                dump_writer = dump_writer,
                variables   = current_variables,
                payload     = payload,
                outputs     = outputs[self.name][key],
            )

            if self.graph.status == ComponentStatus.Stopped:
                status = self.graph.status
                break
        else:
            status = ComponentStatus.Succeeded


        #------------------------
        # 終了
        #------------------------
        logger.info("Flow-each.{}.{}: output.type={}, output.length={}".format(
            self.name,
            status,
            type(self.__output).__name__,
            len(self.__output) if hasattr(self.__output, '__len__') else None,
        ))
        return {
            "output" : outputs[self.name],
            "status" : status,
        }


