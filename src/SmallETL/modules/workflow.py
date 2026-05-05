# coding: utf-8

from typing import Dict, Any, overload
import logging
from pathlib import Path
from datetime import datetime
import uuid
from pathlib import Path
import os
import glob
import shutil

from .const import ExitCode
from .graph import GraphInfo
from ..libs import format_ex
from ..libs.json_ex import JsonEx

# 設定

logger = logging.getLogger(__name__)


class DumpWriter():

    @property
    def dir(self) -> str:
        return self.__dump_dir

    def __init__(self, dir:str):
        self.__dump_dir:Path = self.__make_dump_dir(path=dir)


    def __make_dump_dir(self, path:str) -> Path:
        """dumpディレクトリ作成"""

        if path is None:
            return None

        cwd:Path = Path.cwd()
        dump_dir:Path = cwd.joinpath(path)

        if os.path.isdir(dump_dir):
            # 既にフォルダが存在する場合は中身を全削除
            files = glob.glob(f"{dump_dir}/*")
            for f in files:
                if os.path.isfile(f):
                    os.remove(f)
                elif os.path.isdir(f):
                    shutil.rmtree(f)

        dump_dir.mkdir(exist_ok=True, parents=True)
        return dump_dir

    
    def put(self, filename:str, content:Any) -> Path:
        """書き込み"""

        if self.__dump_dir is None:
            return None

        # dump出力
        dump_path: Path = self.__dump_dir.joinpath(filename)
        JsonEx.dump(content, dump_path)
        return dump_path




class WorkFlow():

    @property
    def name(self) -> str:
        return self.__name

    @property
    def description(self) -> str:
        return self.__description

    @property
    def const(self) -> Dict[str, Any]:
        return self.__const

    @property
    def dump_dir(self) -> str:
        return self.__dump_dir

    @property
    def graph(self) -> GraphInfo:
        return self.__graph


    @overload
    def __init__(self, *, workflow:Dict):
        pass

    @overload
    def __init__(self, *, filepath:str, encoding:str="utf-8"):
        pass

    def __init__(self, *, workflow:Dict={}, filepath:str = "", encoding:str="utf-8"):
        logger.info(f"workflow.type: <{type(workflow).__name__}>, filepath: {filepath}, encoding: {encoding}")

        # workflow, filepath の入力はどちらか一方のみ許可
        if all([workflow, filepath]) or not any([workflow, filepath]):
            raise ValueError("You must specify either `workflow` or `filepath`.")

        # 文字列の場合はファイルパスと見なし、jsonc として読み込み。
        if filepath:
            workflow = JsonEx.load(path=filepath, encoding=encoding)

        # Workflow定義をロード
        self.__load_workflow(workflow_def=workflow)


    def __load_workflow(self, workflow_def:Dict) -> None:
        '''Workflow定義を読み込み'''
        logger.debug(f"workflow-def: {workflow_def}")

        # 情報読み込み
        self.__name:str             = workflow_def["name"]
        self.__description:str      = workflow_def.get("description", None)
        self.__const:Dict[str, Any] = workflow_def.get("const", None) or {}
        self.__dump_dir:str         = workflow_def.get("dump_dir", None)
        self.__graph:GraphInfo      = GraphInfo(workflow_def["graph"])

        # 終了
        return


    def run(self, var:Dict[str, Any]={}) -> str:
        '''実行ワークフロー実行'''

        # run_id 生成
        run_id = str(uuid.uuid4())[0:8]
        logger.info(f"[{run_id}] Run Workflow `{self.name}`")
        start_time:datetime = datetime.now()

        # 変数の生成
        variables:Dict[str, Any] = {
            "var" : var,
            "wf"    : {
                "name" : self.name,
                "run_id" : run_id,
                "start_time" : start_time,
            },
        }
        variables = {
            **variables,
            "const": format_ex.data_mapping(self.const, data=variables),
        }


        # dump ディレクトリ作成
        dump_dir_str = format_ex.format(self.dump_dir, data=variables) if self.dump_dir else None
        dump_writer = DumpWriter(dir=dump_dir_str)
        logger.debug(f"dump_dir: {dump_writer.dir}")


        try:
            # payload/outputs 初期化
            outputs:Dict[str, Any] = {}

            # graph 実行
            self.graph.run(
                dump_prefix = "",
                dump_writer = dump_writer,
                variables   = variables,
                payload     = outputs,
                outputs     = outputs,
            )

            # 終了処理
            end_time:datetime = datetime.now()
            logger.info(f"[{run_id}] End Workflow `{self.name}`")
            dump_writer.put(filename="_outputs.json", content=outputs)
            return {
                "run_id" : run_id,
                "start_time" : start_time,
                "end_time" : end_time,
                "status"  : ExitCode.Succeeded,
                "outputs" : outputs,
            }

        except KeyboardInterrupt:
            # 改行を入れる（暫定対応）
            print()
            print()

            # 終了処理
            end_time:datetime = datetime.now()
            logger.warning(f"Catch KeyboardInterrupt")
            logger.warning(f"[{run_id}] Aborted Workflow `{self.name}`")
            dump_writer.put(filename="_outputs.json", content=outputs)
            return {
                "run_id" : run_id,
                "start_time" : start_time,
                "end_time" : end_time,
                "status"  : ExitCode.Aborted,
                "outputs" : None,
            }

