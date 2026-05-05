from __future__ import annotations
from typing import TYPE_CHECKING

from typing import final, List, Dict, Set, Any, Callable, Tuple
import logging
import importlib
import re
from datetime import datetime
from ..libs import format_ex

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



class JobInfo():
    """Job情報クラス"""

    @property
    def name(self) -> str:
        return self.__name

    @property
    def job(self) -> str:
        return self.__job_path

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
    def __init__(self, name:str, job:str, parameters:Dict={}, depends:List=None):
        logger.info(f"Job.init: name={name}, job={job}, parameters={parameters}, depends={depends}")

        # name の命名チェック
        for _reg_def in _NAME_REGEX:
            _pattern = _reg_def["pattern"]
            _msg = _reg_def["msg"]
            if not re.fullmatch(_pattern, name):
                raise ValueError(f"{_msg}")

        # 設定
        self.__name = name
        self.__job_path = job
        self.__job_func = self.__load_job(job_path=job)
        self.__depends = depends
        self.__parameters = parameters

        # 実行結果
        self.__start_time = None
        self.__output = None
        self.__end_time = None



    def __repr__(self) -> str:
        return f"<{self.__name}: {self.__class__.__module__}.{self.__class__.__name__} object at {hex(id(self))}>"


    # def run(self, outputs:Dict[str, Any], vars:Dict[str, Dict[str, Any]]) -> Any:
    def run(
            self,
            variables:Dict[str, Any],
            payload:Dict[str, Any],
            outputs:Dict[str, Any]
        ) -> Any:
        """ジョブ実行"""
        logger.info(f"job.{self.name}.run: vars={variables}, payload.type:{type(payload).__name__}, payload.len:{len(payload)}")


        #------------------------
        # jobパラメータ生成
        #------------------------
        # 初期化: dict形式のpayload
        job_params = format_ex.data_mapping(
            template=self.__parameters,
            data={
                **variables,
                "payload"   : payload,
            },
            errors='raise',
            assign_dtype='original',
        )
        logger.debug(f"jos_params: {job_params}")


        #------------------------
        # 実行
        #------------------------
        self.__start_time == datetime.now()

        if isinstance(job_params, Dict):
            self.__output = self.__job_func(
                **job_params
            )
        elif isinstance(job_params, (List, Tuple)):
            self.__output = self.__job_func(
                *job_params
            )
        else:
            self.__output = self.__job_func(
                job_params
            )

        self.__end_time == datetime.now()
        outputs[self.name] = self.__output

        #------------------------
        # 終了
        #------------------------
        logger.info("job.{}.succeeded: output.type={}, output.len={}".format(
            self.name,
            type(self.__output).__name__,
            len(self.__output) if hasattr(self.__output, '__len__') else None,
        ))
        return self.__output


    def __load_job(self, job_path:str) -> Callable:
        """job(module/func)をロード"""
    
        """対応形式
        とりあえず標準ジョブ(built_in)のみ対応する。      
        """

        '''jobを動的に読み込み'''
        logger.info(f"load_job: {job_path}")


        # # 相対パスでのimportに package(基点) が必須であるため、SmallETL のディレクトリを取得
        # package = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."), os.getcwd())
        package_path = __package__
        # package = package_path

        # jobのパスを分解
        parts:List[str] = job_path.split(".")
        module_path:str = ".".join(parts[0:-1])
        module_name:str = parts[-1]
        module_path_buildin:str = f"..job.built_in.{module_path}"

        logger.critical(f"package : {package_path}")
        logger.critical(f"buildin : {module_path_buildin}")
        logger.critical(f"module  : {module_name}")


        # job-module を読み込み
        job_mod = importlib.import_module(module_path_buildin, package=package_path)
        job_func:Callable = getattr(job_mod, module_name)

        # function 返却
        logger.debug(f"load_job.succeed: {job_func.__name__}")
        return job_func

