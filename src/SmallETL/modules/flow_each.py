from __future__ import annotations
from typing import TYPE_CHECKING

from typing import final, List, Dict, Set, Any
import logging
import re
from datetime import datetime
from ..libs import format_ex

if TYPE_CHECKING:
    from .workflow import DumpWriter
    from .graph import GraphInfo



_NAME_SYMBOL = r'#$%@-_'
_NAME_REGEX = [
    {
        "pattern" : re.compile(f"[\w{re.escape(_NAME_SYMBOL)}]*"),
        "msg"     : f"`name` には半角英数字および一部記号({_NAME_SYMBOL})のみ使用できます。",
    }
]



logger = logging.getLogger(__name__)


class FlowEach():
    """フロー制御Eachクラス"""

    @property
    def name(self) -> str:
        return self.__name

    @property
    def items(self) -> Any:
        return self.__items

    @property
    def graph(self) -> GraphInfo:
        return self.__graph

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.__parameters

    @property
    def depends_on(self) -> Set[str]:
        """依存Job"""
        ret:List[str] = []
        for prop in [self.__payload, self.__depends]:
            if prop is None:
                pass
            elif isinstance(prop, list):
                ret.extend(prop)
            elif isinstance(prop, Dict):
                ret.extend(list(prop.values()))
            elif isinstance(prop, str):
                ret.append(prop)
        return set(ret)

    @property
    def output(self) -> Any:
        return self.__output



    @final
    def __init__(self, name:str, items:Any, graph:List[Dict], parameters:Dict={}, depends:List=None):
        logger.info(f"Flow-each.init: name={name}, items={items}, graph(len)={len(graph)}, parameters={parameters}, depends={depends}")

        # name の命名チェック
        for _reg_def in _NAME_REGEX:
            _pattern = _reg_def["pattern"]
            _msg = _reg_def["msg"]
            if not re.fullmatch(_pattern, name):
                raise ValueError(f"{_msg}")

        # 循環参照を回避するためここでimport
        from .graph import GraphInfo

        # 設定
        self.__name = name
        self.__items = items
        self.__graph = GraphInfo(graph_def=graph)
        self.__depends = depends
        self.__parameters = parameters

        # 実行結果
        self.__start_time = None
        self.__output = None
        self.__end_time = None



    # def run(self, outputs:Dict[str, Any], vars:Dict[str, Dict[str, Any]]) -> Any:
    def run(
            self,
            dump_prefix:str,
            dump_writer:DumpWriter,
            variables:Dict[str, Any],
            payload:Dict[str, Any],
            outputs:Dict[str, Any]
        ) -> Any:
        logger.info(f"each.{self.name}.run: vars={variables}, payload.type:{type(payload).__name__}, payload.len:{len(payload)}")


        #------------------------
        # items生成
        #------------------------
        items:List|Dict = format_ex.data_mapping(
            template=self.items,
            data={
                **variables,
                "payload"   : payload,
            },
            errors='raise',
            assign_dtype='original',
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
        self.__start_time == datetime.now()

        # items(iter) のタイプに応じた実行
        if isinstance(items, dict):
            outputs[self.name] = {}

            for i, key in enumerate(items.keys()):
                current_variables = {
                    **variables,
                    "each" : {
                        "index" : i,
                        "key"   : key,
                        "value" : items[key],
                        **parent_var,
                    },
                }

                outputs[self.name][key] = {}
                self.__output = self.graph.run(
                    dump_prefix = f"{dump_prefix}[{key}]-",
                    dump_writer = dump_writer,
                    variables   = current_variables,
                    payload     = payload,
                    outputs     = outputs[self.name][key],
                )

        elif isinstance(items, (list, tuple)):
            outputs[self.name] = []

            for i, item in enumerate(items):
                current_variables = {
                    **variables,
                    "each" : {
                        "index"  : i,
                        "payload": item,
                        **parent_var,
                    },
                }
                outputs[self.name].append({})

                self.__output = self.graph.run(
                    dump_prefix = f"{dump_prefix}[{i}]-",
                    dump_writer = dump_writer,
                    variables   = current_variables,
                    payload     = payload,
                    outputs     = outputs[self.name][i],
                )

        self.__end_time == datetime.now()


        #------------------------
        # 終了
        #------------------------
        logger.info("Flow-each.{}.succeeded: output.type={}, output.length={}".format(
            self.name,
            type(self.__output).__name__,
            len(self.__output) if hasattr(self.__output, '__len__') else None,
        ))
        return outputs[self.name]


