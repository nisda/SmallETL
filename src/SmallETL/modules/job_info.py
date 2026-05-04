from typing import final, List, Dict, Set, Any, Callable
from types import LambdaType
import logging
import importlib
import re
import os
from datetime import datetime
# from types import SimpleNamespace
from ..libs import format_ex

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
    def payload(self) -> List|Dict|str:
        return self.__payload

    @property
    def parameters(self) -> Dict[str, Any]:
        return self.__parameters

    @property
    def depends_on(self) -> Set[str]:
        """依存Job"""
        result:List[str] = []
        for prop in [self.__payload, self.__depends]:
            if prop is None:
                pass
            elif isinstance(prop, list):
                result.extend(prop)
            elif isinstance(prop, Dict):
                result.extend(list(prop.values()))
            elif isinstance(prop, str):
                result.append(prop)
        return set(result)

    @property
    def result(self) -> Any:
        return self.__result

    @final
    def __init__(self, package_path:str, name:str, job:str, payload:List|Dict|str=None, parameters:Dict={}, depends:List=None):
        logger.info(f"Job.init: name={name}, job={job}, payload={payload}, parameters={parameters}, depends={depends}")

        # name の命名チェック
        for _reg_def in _NAME_REGEX:
            _pattern = _reg_def["pattern"]
            _msg = _reg_def["msg"]
            if not re.fullmatch(_pattern, name):
                raise ValueError(f"{_msg}")

        self.__name = name
        self.__job_path = job
        self.__job_func = self.__load_job(job_path=job, package_path=package_path)
        self.__depends = depends
        self.__parameters = parameters
        self.__payload = payload

        self.__start_time = None
        self.__result = None
        self.__end_time = None

    def __repr__(self) -> str:
        return f"<{self.__name}: {self.__class__.__module__}.{self.__class__.__name__} object at {hex(id(self))}>"


    # def run(self, outputs:Dict[str, Any], vars:Dict[str, Dict[str, Any]]) -> Any:
    def run(self, inputs:Dict[str, Any], user_vars:Dict, wf_vars:Dict) -> Any:
        """ジョブ実行"""
        logger.info(f"job.{self.name}.run: vars={user_vars}, wf_vars={wf_vars}")


        # #------------------------
        # # Payload 調整
        # #   -> Payload の必要性から再検討
        # #      たぶん loop とか実装するまで要らない。
        # #------------------------


        #------------------------
        # jobパラメータ生成
        #------------------------
        # 初期化: dict形式のpayload
        job_params = format_ex.data_mapping(
            template=self.__parameters,
            data={
                "var"       : user_vars,
                "wf"        : wf_vars,
                "payload"   : inputs,
            },
            errors='raise',
            assign_dtype='original',
        )
        logger.debug(f"jos_params: {job_params}")


        #------------------------
        # 実行
        #------------------------
        self.__start_time == datetime.now()
        self.__result = self.__job_func(
            **job_params
        )
        self.__end_time == datetime.now()

        #------------------------
        # 終了
        #------------------------
        logger.info("job.{}.succeeded: output.type={}, output.length={}".format(
            self.name,
            type(self.__result).__name__,
            len(self.__result) if hasattr(self.__result, '__len__') else None,
        ))
        return self.__result


    def __load_job(self, job_path:str, package_path:str) -> Callable:
        """job(module/func)をロード"""
    
        """対応形式
        とりあえず標準ジョブ(built_in)のみ対応する。      
        """

        '''jobを動的に読み込み'''
        logger.info(f"load_job: {job_path}")


        # # 相対パスでのimportに package(基点) が必須であるため、SmallETL のディレクトリを取得
        # package = os.path.relpath(os.path.join(os.path.dirname(__file__), ".."), os.getcwd())
        # package = __package__
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

