from __future__ import annotations
from typing import TYPE_CHECKING
from typing import Dict, List, Any, Self
import logging

from .job_info import JobInfo
from .flow_each import FlowEach
from .component_base import ComponentBase, ComponentStatus

if TYPE_CHECKING:
    from .workflow import DumpWriter



logger = logging.getLogger(__name__)



class GraphInfo():

    @property
    def steps(self) -> List[ComponentBase]:
        return self.__steps

    @property
    def status(self) -> ComponentStatus:
        return self.__status

    @property
    def output(self) -> Any:
        return self.__output


    def __init__(self, graph_def:List[Dict],):
        """コンストラクタ"""

        self.__steps:List[ComponentBase] = []
        for step_def in graph_def:
            flow:str = step_def.pop("flow", None)

            if flow is None:
                self.__steps.append(JobInfo(**step_def,))
            elif flow.lower() == 'each':
                self.__steps.append(FlowEach(**step_def,))


    def run(
            self:Self,
            dump_prefix:str,
            dump_writer:DumpWriter,
            variables:Dict[str, Any],
            payload:Dict[str, Any],
            outputs:Dict[str, Any],
        ) -> Dict:
        """ワークフロー実行（主処理）"""

        # 実行番号の最大桁数（最低２桁に調整）
        run_num_digit:int = max(len(str(len(self.steps))), 2)

        # job実行（直列）
        for i, step_info in enumerate(self.steps):
            # dump_prefix 生成
            dump_prefix_current = dump_prefix + str(i+1).zfill(run_num_digit)

            # Component実行
            self.__status = step_info.run(
                dump_prefix = dump_prefix_current,
                dump_writer = dump_writer,
                variables   = variables,
                payload     = payload,
                outputs     = outputs,
            )

            print("------------------")
            print(self.__status)
            print(self.status)
            print("------------------")

            # Stopped のときはその時点で終了
            if self.status == ComponentStatus.Stopped:
                break

        else:
            # 最後まで通った場合
            self.__status = ComponentStatus.Succeeded


        # 結果を保存
        self.__output = outputs
        return self.status

