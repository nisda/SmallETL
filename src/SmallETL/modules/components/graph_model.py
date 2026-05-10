from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Dict, List, Any, Self
import logging

from .result_info import TaskResultInfo, TaskStatus
from .base_model import ComponentBase
from .job_model import JobModel
from .each_model import EachModel

if TYPE_CHECKING:
    from ..workflow import DumpWriter



logger = logging.getLogger(__name__)



class GraphModel():

    @property
    def tasks(self) -> List[ComponentBase]:
        return self.__tasks


    def __init__(self, graph_def:List[Dict]|Dict):
        """コンストラクタ"""

        # Dictの場合は１タスクのみのgraphと見なす。
        # 内部でlist化して処理する。
        if isinstance(graph_def, Dict):
            graph_def = [graph_def]


        # 定義読み込み＆モデル生成
        self.__tasks:List[ComponentBase] = []
        for step_def in graph_def:
            flow:str = step_def.pop("flow", None)

            if flow is None:
                self.__tasks.append(JobModel(**step_def))
            elif flow.lower() == 'each':
                self.__tasks.append(EachModel(**step_def))


    def run(
            self:Self,
            dump_prefix:str,
            dump_writer:DumpWriter,
            variables:Dict[str, Any],
            payload:Dict[str, Any],
            outputs:Dict[str, Any],
        ) -> TaskResultInfo:
        """ワークフロー実行（主処理）"""

        # 実行番号の最大桁数（最低２桁に調整）
        run_num_digit:int = max(len(str(len(self.tasks))), 2)

        # job実行（直列）
        status:TaskStatus = TaskStatus.Succeeded
        for i, tasks_info in enumerate(self.tasks):
            # dump_prefix 生成
            dump_prefix_current = dump_prefix + str(i+1).zfill(run_num_digit)

            # Component実行
            task_result = tasks_info.run(
                dump_prefix = dump_prefix_current,
                dump_writer = dump_writer,
                variables   = variables,
                payload     = payload,
                outputs     = outputs,
            )

            # Stopped のときはその時点で終了
            if task_result.status == TaskStatus.Aborted:
                status = task_result.status
                break


        # 結果を返却
        return TaskResultInfo(
            status=status,
            output=outputs,
        )

