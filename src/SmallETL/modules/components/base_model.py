from __future__ import annotations
from typing import TYPE_CHECKING

from typing import final, List, Dict, Set, Any, Callable, Tuple, Final, Self
from abc import ABC, abstractmethod
import inspect
import logging
import importlib
import re
from datetime import datetime
from enum import StrEnum, auto


from ..common.shared import evaluater
from .result_info import TaskResultInfo, TaskStatus, TaskAbort

if TYPE_CHECKING:
    from ..workflow import DumpWriter



# 定数
_NAME_SYMBOL:Final[str] = r'#$%@-_'
_NAME_REGEX:Final[List[str]] = [
    {
        "pattern" : re.compile(f"[\w{re.escape(_NAME_SYMBOL)}]*"),
        "msg"     : f"`name` には半角英数字および一部の記号({_NAME_SYMBOL})のみ使用できます。",
    }
]

_STOP_MSG_DEFAULT:Final[str] = "Task was aborted due to `abort.condition`."


# 共通
logger = logging.getLogger(__name__)




class ComponentBase():

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        #----------------------------
        # __init__ 調整処理
        #----------------------------

        # 子クラスで定義されたオリジナルの __init__ を取得
        child_init = cls.__init__

        # Child.__init__ 差し替え用 init 関数
        def wrapped_init(self, *args, **kwargs):

            # パラメータを取得
            sig = inspect.signature(self.__class__.__bases__[0].__init__)
            bound_args = sig.bind(self, *args, **kwargs)
            bound_args.apply_defaults()
            args_all = dict(bound_args.arguments)

            # パラメータの振り分け
            child_params    = args_all.get('kwargs', {})
            base_params     = args_all

            # 親クラスの init を実行
            ComponentBase.__init__(**base_params)

            # 子クラスの init を実行
            child_init(self, **child_params)

        # 子クラスの __init__ をラップしたものに差し替える
        cls.__init__ = wrapped_init


    def __param_to_list(self, value:Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, List):
            return value
        else:
            return [value]


    @final
    def __init__(
        self,
        name:str,
        description:str     = None,
        precondition:str    = None,
        parameters:Dict     = None,
        abort:List|Dict     = None,
        # **kwargs必須。wrapped_init で sig.bind するため。
        **kwargs
    ):

        logger.info(
            f"{self.__class__.__name__}.base.init: " +
            ", ".join([
                f"name={name}",
                f"description={description}",
                f"precondition={precondition}",
                f"parameters={parameters}",
                f"abort={abort}",
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
        self.__description      = description
        self.__precondition     = precondition
        self.__parameters       = parameters
        self.__abort            = self.__param_to_list(abort)

        # 終了
        return


    def __repr__(self) -> str:
        return f"<{self.name}: {self.__class__.__module__}.{self.__class__.__name__} object at {hex(id(self))}>"




    @property
    def name(self) -> str:
        return self.__name

    @property
    def description(self) -> str:
        return self.__description

    @property
    def precondition(self) -> str:
        return self.__precondition

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.__parameters

    @property
    def abort(self) -> List[Dict]:
        return self.__abort



    # タスク実行（子クラス用、実装必須）
    @abstractmethod
    def _run(self, *args, **kwargs):
        ...



    # タスク実行
    def run(
            self,
            dump_prefix:str,
            dump_writer:DumpWriter,
            variables:Dict[str, Any],
            payload:Dict[str, Any],
            outputs:Dict[str, Any]
        ) -> TaskResultInfo:
        """タスク実行"""

        # タスク名を生成
        task_name:str = f"{dump_prefix}_{self.name}"

        # 開始ログ
        logger.info(f"[{task_name}] {self.__class__.__name__}.start: payload.len:{len(payload)}")


        #------------------------
        # mapping_data 生成
        #------------------------
        mapping_data = {
            **variables,
            "output"   : payload,
        }

        #------------------------
        # 前提条件判定 precondition
        #------------------------

        # precondition が設定されていたら判定、未設定時はTrue
        precondition_result:bool = \
            evaluater.eval(self.precondition, mapping=mapping_data) \
            if self.precondition else True

        if not precondition_result:
            skip_msg:str = "skipped by `precondition`."

            # 出力結果はNull固定
            outputs[self.name] = None

            # dump出力
            dump_file:str = f"{task_name}.skip.json"
            dump_writer.put(filename=dump_file, content=skip_msg)

            # 終了
            logger.info(f"[{task_name}] {skip_msg}")
            return TaskResultInfo(status=TaskStatus.Skipped, output=None)


        #------------------------
        # Taskパラメータ生成
        #------------------------
        params = evaluater.format(
            self.__parameters,
            mapping=mapping_data,
        )


        #------------------------
        # 実行
        #------------------------

        # /// タスク実行 ///
        if "JobModel" in self.__class__.__name__:
            # ジョブの場合
            # 循環参照で JobInfo を参照できないため、クラス名で判定

            # パラメータ調整
            args:List = \
                [params] if not isinstance(params, (Dict, List, Tuple)) else \
                params if isinstance(params, (List, Tuple)) else []
            kwargs:Dict = \
                params if isinstance(params, (Dict)) else {}

            logger.info(f"[{task_name}] run: args.len={len(args)}, kwargs.len={len(kwargs)}")
            logger.debug(f"[{task_name}] params.args   = {args}")
            logger.debug(f"[{task_name}] params.kwargs = {kwargs}")

            task_result:TaskResultInfo = self._run(
                task_name=task_name,
                args=args,
                kwargs=kwargs,
            )

        else:

            # 制御コンポーネントの場合
            task_result:TaskResultInfo = self._run(
                task_name   = task_name,
                dump_prefix = dump_prefix,
                dump_writer = dump_writer,
                variables   = variables,
                payload     = payload,
                outputs     = outputs,
            )

        # 出力結果をセット
        outputs[self.name] = task_result.output


        #------------------------
        # dump出力
        #------------------------
        dump_file:str = f"{task_name}.json"
        dump_writer.put(filename=dump_file, content=task_result.output)


        #------------------------
        # 中止判定（abort）
        #------------------------
        if task_result.status != TaskStatus.Aborted:
            for i, abort_config in enumerate(self.abort):
                abort_condition:str = abort_config.get("condition", None)
                abort_message:str   = abort_config.get("message", _STOP_MSG_DEFAULT)

                # condition 未設定はエラー
                if abort_condition is None:
                    raise ValueError(f"`abort.condition` is not set in `{task_name}.abort[{i}]`")

                # 判定
                is_abort:bool = evaluater.eval(abort_condition, mapping=mapping_data)

                if is_abort:
                    # メッセージ調整
                    abort_message = evaluater.format(abort_message, mapping=mapping_data)

                    # メッセージ表示
                    logger.warning(f"[{task_name}] aborted: {abort_message}")
                    # ステータス上書き
                    task_result = TaskResultInfo(
                        status = TaskStatus.Aborted,
                        output = task_result.output,
                    )
                    # Workflow Abort
                    raise TaskAbort(f"{abort_message.rstrip(".")} at [{task_name}]")


        #------------------------
        # 終了
        #------------------------
        logger.info("[{}] {}: output.type = <{}>, output.len = {}".format(
            task_name,
            task_result.status,
            type(task_result.output).__name__,
            len(task_result.output) if hasattr(task_result.output, '__len__') else None,
        ))
        return task_result
