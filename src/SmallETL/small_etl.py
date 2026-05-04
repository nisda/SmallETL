# coding: utf-8

from typing import Dict, List, Union, Optional, Any, Self, Type, overload, Set, Tuple
import sys
import logging
import json
from copy import deepcopy
from pprint import pprint
from pathlib import Path
from datetime import datetime
import uuid
# from types import SimpleNamespace
from pathlib import Path

from .utils.small_etl import SmallEtlUtils
from .modules import JobInfo
# from .modules import json as json_ex
from .libs import format_ex
from .libs.json_ex import JsonEx

# 設定

logger = logging.getLogger(__name__)


class _Utils:
    pass

    # @classmethod
    # def dict_to_chain(cls, d:dict):
    #     if isinstance(d, dict):
    #         return SimpleNamespace(**{ k:cls.dict_to_chain(v) for k,v in d.items()})
    #     elif isinstance(d, (list, tuple)):
    #         return tuple([cls.dict_to_chain(v) for v in d])
    #     else:
    #         return d


class WorkFlow:


    @property
    def name(self) -> str:
        return self.__name

    @property
    def dump_dir(self) -> str:
        return self.__dump_dir

    @property
    def max_workers(self) -> int:
        return self.__max_workers

    @property
    def graph(self) -> List[JobInfo]:
        return self.__graph


    @overload
    def __init__(self, *, workflow:Dict):
        pass

    @overload
    def __init__(self, *, filepath:str, encoding:str="utf-8"):
        pass

    def __init__(self, *, workflow:Dict={}, filepath:str = "", encoding:str="utf-8"):
        logger.info(f"workflow: {type(workflow)}, filepath: {filepath}, encoding: {encoding}")
        if all([workflow, filepath]) or not any([workflow, filepath]):
            raise ValueError("You must specify either `workflow` or `filepath`.")

        if filepath:
            # 文字列の場合はファイルパスと見なし、jsonc として読み込み。
            workflow = JsonEx.load(path=filepath, encoding=encoding)

        # Workflow定義をロード
        self.__load_workflow(workflow_def=workflow)


    def __load_workflow(self, workflow_def:Dict) -> None:
        '''Workflow定義を読み込み'''
        logger.debug(f"workflow-def: {workflow_def}")

        # 情報読み込み
        self.__name: str            = workflow_def["name"]
        self.__dump_dir: str        = workflow_def.get("dump_dir", None)
        self.__max_workers: int     = workflow_def.get("max_workers", None)
        self.__graph: List[JobInfo]  = [
            JobInfo(**job_def, package_path=__package__)
            for job_def in workflow_def["graph"]
        ]

        # 終了
        return


    def run(self, var:Dict[str, Any]={}) -> str:
        '''実行ワークフロー実行'''

        # run_id 生成
        run_id = str(uuid.uuid4())[0:8]
        logger.info(f"[{run_id}] Run Workflow `{self.name}`")
        start_time:datetime = datetime.now()

        # 実行変数
        user_vars:Dict = var
        wf_vars:Dict = {
            "name" : self.name,
            "run_id" : run_id,
            "start_time" : start_time,
        }

        # dump ディレクトリ作成
        dump_dir = None
        if self.dump_dir:
            dump_dir_str = format_ex.format(self.dump_dir, data={
                "var" : user_vars, "wf": wf_vars
            })
            dump_dir:Path = SmallEtlUtils.make_dump_dir(path=dump_dir_str)
        logger.debug(f"dump_dir: {dump_dir}")

        # graph 実行
        results:List = self.__exec_graph(
            dump_dir = dump_dir,
            graph = self.graph,
            user_vars = user_vars,
            wf_vars = wf_vars,
        )

        # 終了処理
        end_time:datetime = datetime.now()
        logger.info(f"[{run_id}] End Workflow `{self.name}`")
        return {
            "run_id" : run_id,
            "start_time" : start_time,
            "end_time" : end_time,
            "results" : results,
        }


    def __exec_graph(
            self:Self,
            dump_dir:Path,
            graph:List[JobInfo],
            user_vars:Dict[str, Any],
            wf_vars:Dict[str, Any],
        ) -> Dict:
        """ワークフロー実行（主処理）"""

        # 実行番号の最大桁数（最低２桁に調整）
        run_num_digit:int = max(len(str(len(graph))), 2)

        # job実行（直列）
        job_outputs:Dict = {}
        for i, job_info in enumerate(graph):
            # job実行
            output = job_info.run(inputs=job_outputs, user_vars=user_vars, wf_vars=wf_vars)

            # dump出力
            if dump_dir:
                num_str:str = str(i+1).zfill(run_num_digit)
                dump_path:str = dump_dir / f"{num_str}_{job_info.name}.json"
                JsonEx.dump(output, dump_path, encoding="utf-8")

            # 実行結果を保存
            job_outputs[job_info.name] = output

        logger.debug(f"outputs: {job_outputs}")
        return job_outputs

