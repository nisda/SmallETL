from __future__ import annotations
from typing import TYPE_CHECKING

from typing import final, List, Dict, Set, Any, Callable, Tuple
import logging
import importlib
import re
from .component_base import ComponentBase

if TYPE_CHECKING:
    from .workflow import DumpWriter


_NAME_SYMBOL = r'#$%@-_'
_NAME_REGEX = [
    {
        "pattern" : re.compile(f"[\w{re.escape(_NAME_SYMBOL)}]*"),
        "msg"     : f"`name` には半角英数字および一部記号({_NAME_SYMBOL})のみ使用できます。",
    }
]

logger = logging.getLogger(__name__)



class JobInfo(ComponentBase):
    """Job情報クラス"""


    @property
    def job(self) -> str:
        return self.__job_path


    @final
    def __init__(
        self,
        job:str,
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

        logger.info(f"{self.__class__.__name__}.init: job={job}")

        # 設定
        self.__job_path = job
        self.__job_func = self.__load_job(job_path=job)


    def __load_job(self, job_path:str) -> Callable:
        """job(module/func)をロード"""
    
        """対応形式
        とりあえず標準ジョブ(built_in)のみ対応する。      
        """

        '''jobを動的に読み込み'''
        logger.info(f"load_job: {job_path}")


        # 相対パスでのimportに package(基点) が必須であるため現在のパスを取得
        package_path = __package__

        # jobのパスを分解
        parts:List[str] = job_path.split(".")
        module_path:str = ".".join(parts[0:-1])
        module_name:str = parts[-1]

        if module_path.startswith("custom."):
            module_path_buildin:str = f"..job.{module_path}"
        else:
            module_path_buildin:str = f"..job.built_in.{module_path}"

        logger.debug(f"package : {package_path}")
        logger.debug(f"buildin : {module_path_buildin}")
        logger.debug(f"module  : {module_name}")


        # job-module を読み込み
        job_mod = importlib.import_module(module_path_buildin, package=package_path)
        job_func:Callable = getattr(job_mod, module_name)

        # function 返却
        logger.debug(f"load_job.succeed: {job_func.__name__}")
        return job_func


    def _run(
            self,
            task_name:str,
            args:List[Any],
            kwargs:Dict[str, Any],
        ) -> Any:

        return self.__job_func(
            *args,
            **kwargs,
        )

