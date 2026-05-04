# coding: utf-8
import os
import json
import logging
import importlib
from typing import List, Dict, Any, Set
from datetime import datetime
import uuid
from collections import Counter
from pathlib import Path
from collections import OrderedDict
import glob, shutil

# from ...job.job_base import JobBase

# ### 定数定義
# BASE_DIR: str           = os.path.dirname(__file__)
# WORKSPACE_DIR: str      = os.path.join(BASE_DIR, "__workspace")
# JOB_NUMBER_DIGIT: int   = 3

### Logger 
logger = logging.getLogger(__name__)


class SmallEtlUtils():


    # @staticmethod
    # def optimize_graph(jobs:List[Dict[str, Any]], package_path:str) -> List[List[Any]]:
    #     """ Graph を最適化"""

    #     # 全job名を取得
    #     job_names_all:List[str] = [ x["name"] for x in jobs ]

    #     # nameの重複があればエラー
    #     duplicate_names:List[str] = [
    #         name for name, cnt in Counter(job_names_all).items()
    #         if cnt > 1
    #     ]
    #     if len(duplicate_names) > 0:
    #         raise Exception(f"The job name `{duplicate_names[0]}` is duplicated.")

    #     # 全jobオブジェクトを生成
    #     job_pool:Dict[str, JobBase] = {}
    #     try:
    #         for _job_def in jobs:
    #             _job_name:str = _job_def.get("name")
    #             _job_path:str = _job_def.get("job")
    #             job_pool[_job_name] = SmallEtlUtils.job_loader(
    #                 package_path=package_path,
    #                 job_path=_job_path,
    #             )(**_job_def)
    #     except Exception as e:
    #         error_type = type(e)
    #         raise error_type(f"job={_job_name}#{_job_path}: {e}") from e

    #     # 前提条件を満たした job から順番に graph に追加する。
    #     job_stack:List[List[Dict]] = []
    #     name_stack:Set[str] = set()
    #     while True:
    #         # 前提条件を満たしている job を buffer に保存
    #         _names_buf:List[str] = []
    #         for _name, _job_obj in job_pool.items():
    #             if _job_obj.depends_on <= name_stack:
    #                 _names_buf.append(_name)

    #         # １つも存在しない => job が繋がっていない。
    #         if len(_names_buf) == 0:
    #             raise Exception(f"Dependent jobs not found at {list(job_pool.keys())}")
    #         else:
    #             name_stack.update(_names_buf)
    #             job_stack.append([
    #                 job_pool.pop(_name) for _name in _names_buf
    #             ])

    #         # 全て処理しきったらループを抜ける。
    #         if len(job_pool) == 0:
    #             break

    #     return job_stack



    @staticmethod
    def make_dump_dir(path:str) -> Path:
        cwd:Path = Path.cwd()
        dump_dir:Path = cwd.joinpath(path)

        if os.path.isdir(dump_dir):
            # 既にフォルダが存在する場合は全削除
            files = glob.glob(f"{dump_dir}/*")
            for f in files:
                if os.path.isfile(f):
                    os.remove(f)
                elif os.path.isdir(f):
                    shutil.rmtree(f)

        dump_dir.mkdir(exist_ok=True, parents=True)
        return dump_dir


    @staticmethod
    def dump_job_output(dump_dir:Path, job_id:str, data:Any) -> Path:
        if dump_dir is None: return None

        # dump出力
        dump_path: Path = dump_dir.joinpath(f"{job_id}.json")
        with open(dump_path, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return dump_path


