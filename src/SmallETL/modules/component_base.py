from __future__ import annotations
from typing import TYPE_CHECKING

from typing import final, List, Dict, Set, Any, Callable, Tuple
from abc import ABC, abstractmethod
import logging
import importlib
import re
from datetime import datetime
from enum import StrEnum, auto

from .shared import evaluater

if TYPE_CHECKING:
    from .workflow import DumpWriter


_NAME_SYMBOL = r'#$%@-_'
_NAME_REGEX = [
    {
        "pattern" : re.compile(f"[\w{re.escape(_NAME_SYMBOL)}]*"),
        "msg"     : f"`name` には半角英数字および一部の記号({_NAME_SYMBOL})のみ使用できます。",
    }
]

_STOP_MSG_DEFAULT = "*** Task was stopped due to `stop_condition`."


logger = logging.getLogger(__name__)


class ComponentStatus(StrEnum):
    Initialized = auto()
    Running = auto()
    Succeeded = auto()
    Stopped = auto()
    Skipped = auto()



class ComponentBase(ABC):
    """コンポーネント基底クラス"""

    @property
    def name(self) -> str:
        return self.__name

    @property
    def description(self) -> str:
        return self.__description

    @property
    def condition(self) -> str:
        return self.__condition

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
    def stop_condition(self) -> str:
        return self.__stop_condition

    @property
    def stop_message(self) -> str:
        return self.__stop_message

    @property
    def status(self) -> ComponentStatus:
        return self.__status

    @property
    def output(self) -> Any:
        return self.__output

    @property
    def start_time(self) -> datetime:
        return self.__start_time

    @property
    def end_time(self) -> datetime:
        return self.__end_time

    @final
    def __init__(
        self,
        name:str,
        description:str,
        depends:List,
        condition:str,
        parameters:Dict,
        stop_condition:str,
        stop_message:str,
    ):

        logger.info(
            f"{self.__class__.__name__}.init: " +
            ", ".join([
                f"name={name}",
                f"description={description}",
                f"condition={condition}",
                f"parameters={parameters}",
                f"depends={depends}",
                f"stop_condition={stop_condition}",
                f"stop_message={stop_message}",
            ])
        )

        # name の命名チェック
        for _reg_def in _NAME_REGEX:
            _pattern = _reg_def["pattern"]
            _msg = _reg_def["msg"]
            if not re.fullmatch(_pattern, name):
                raise ValueError(f"{_msg}")

        # 設定
        self.__name = name
        self.__description = description
        self.__condition = condition
        self.__depends = depends
        self.__parameters = parameters
        self.__stop_condition = stop_condition
        self.__stop_message = stop_message

        # 実行情報
        self.__start_time = None
        self.__output = None
        self.__end_time = None
        self.__status   = ComponentStatus.Initialized



    def __repr__(self) -> str:
        return f"<{self.__name}: {self.__class__.__module__}.{self.__class__.__name__} object at {hex(id(self))}>"


    def run(
            self,
            dump_prefix:str,
            dump_writer:DumpWriter,
            variables:Dict[str, Any],
            payload:Dict[str, Any],
            outputs:Dict[str, Any]
        ) -> ComponentStatus:
        """タスク実行"""

        # タスク名を生成
        task_name:str = f"{dump_prefix}_{self.name}"

        logger.info(f"[{task_name}] {self.__class__.__name__}.start: vars={variables}, payload.type:{type(payload).__name__}, payload.len:{len(payload)}")
        self.__status   = ComponentStatus.Running


        #------------------------
        # mapping_data 生成
        #------------------------
        mapping = {
            **variables,
            "payload"   : payload,
        }

        #------------------------
        # 実行条件判定（condition）
        #------------------------

        # condition が設定されていたら判定、未設定時はTrue
        condition_result:bool = evaluater.eval(self.condition, mapping=mapping) if self.condition else True
        if not condition_result:
            self.__status   = ComponentStatus.Skipped
            self.__output   = ComponentStatus.Skipped

            # dump出力
            dump_file:str = f"{task_name}.skip.json"
            dump_writer.put(filename=dump_file, content=self.__output)

            # 終了
            logger.info("[{}] skipped: output.type = <{}>, output.len = {}".format(
                task_name,
                type(self.__output).__name__,
                len(self.__output) if hasattr(self.__output, '__len__') else None,
            ))
            return ComponentStatus.Skipped


        #------------------------
        # Taskパラメータ生成
        #------------------------
        params = evaluater.format(
            self.__parameters,
            mapping=mapping,
        )


        #------------------------
        # 実行
        #------------------------

        # 開始時間を取得保持
        self.__start_time == datetime.now()


        # /// タスク実行 ///
        if "JobInfo" in self.__class__.__name__:
            # ジョブの場合
            # 循環参照で JobInfo を参照できないため、クラス名で判定

            # パラメータ調整
            args:List = \
                [params] if not isinstance(params, (Dict, List, Tuple)) else \
                params if isinstance(params, (List, Tuple)) else []
            kwargs:Dict = \
                params if isinstance(params, (Dict)) else {}

            logger.info(f"[{task_name}] run")
            logger.debug(f"[{task_name}] params.args   = {args}")
            logger.debug(f"[{task_name}] params.kwargs = {kwargs}")

            self.__output = self._run(
                task_name,
                args=args,
                kwargs=kwargs,
            )

        else:

            # 制御コンポーネントの場合
            flow_output:Dict = self._run(
                task_name   = task_name,
                dump_prefix = dump_prefix,
                dump_writer = dump_writer,
                variables   = variables,
                payload     = payload,
                outputs     = outputs,
            )
            self.__status = flow_output["status"]
            self.__output = flow_output["output"]

        # 終了時間を取得保持
        self.__end_time == datetime.now()

        # 出力結果をセット
        outputs[self.name] = self.__output


        #------------------------
        # dump出力
        #------------------------
        dump_file:str = f"{task_name}.json"
        dump_writer.put(filename=dump_file, content=self.__output)


        #------------------------
        # 中止判定（子タスク実行結果）
        #------------------------

        if self.status == ComponentStatus.Stopped:
            # メッセージ表示
            logger.info("[{}] stopped: output.type = <{}>, output.len = {}".format(
                task_name,
                type(self.__output).__name__,
                len(self.__output) if hasattr(self.__output, '__len__') else None,
            ))
            return self.status


        #------------------------
        # 中止判定（stop_condition）
        #------------------------
        mapping = {
            **mapping,
            "output" : self.__output,
        }

        # condition が設定されていたら判定、未設定時は False
        is_stop:bool = evaluater.eval(self.stop_condition, mapping=mapping) if self.stop_condition else False
        if is_stop:

            # メッセージ表示
            stop_msg = self.stop_message or _STOP_MSG_DEFAULT
            logger.info(f"[{task_name}] stopped: {stop_msg}")
            logger.info("[{}] stopped: output.type = <{}>, output.len = {}".format(
                task_name,
                type(self.__output).__name__,
                len(self.__output) if hasattr(self.__output, '__len__') else None,
            ))

            self.__status   = ComponentStatus.Stopped
            return ComponentStatus.Stopped


        #------------------------
        # 終了
        #------------------------
        logger.info("[{}] succeeded: output.type = <{}>, output.len = {}".format(
            task_name,
            type(self.__output).__name__,
            len(self.__output) if hasattr(self.__output, '__len__') else None,
        ))

        self.__status   = ComponentStatus.Succeeded
        return ComponentStatus.Succeeded


    @abstractmethod
    def _run(self, *args, **kwargs):
        ...
