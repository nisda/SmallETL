from typing import Callable, List, Dict, Any, overload, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, Future
from abc import ABC, abstractmethod
import types


class Task():
    def __init__(self, func:Callable, /, *args, **kwargs):
        self.__func = func
        self.__args = args
        self.__kwargs = kwargs

    def __call__(self):
        return self.__func(*self.__args, **self.__kwargs)



class _MultiWorkerBase(ABC):

    @staticmethod
    @abstractmethod
    def _executer():
        pass

    @overload
    @classmethod
    def execute(cls, tasks:Dict[str, Union[Task, types.LambdaType]], max_workers:int=None):
        pass

    @overload
    @classmethod
    def execute(cls, tasks:List[Union[Task, types.LambdaType]], max_workers:int=None):
        pass
    
    @classmethod
    def execute(cls, tasks, max_workers:int=None):
        # ** tasks に lambda関数は不可。PicklingError が発生する。

        if isinstance(tasks, dict):
            tasks_by_id:Dict = tasks
        if isinstance(tasks, list):
            tasks_by_id:Dict = {
                i: tasks[i]
                for i in range(0, len(tasks))
            }


        # 処理実行
        id_map:Dict[Any, int] = {}
        workers:list = []

        executer = cls._executer()
        with executer(max_workers=max_workers) as executer:
            for key, task in tasks_by_id.items():
                # 処理開始
                worker:Future = executer.submit(task)
                workers.append(worker)
                id_map[key] = id(worker)


        # 完了した worker から順次結果を取得
        results_by_worker_id:Dict[int, Any] = {}
        for worker in as_completed(workers):
            worker_id:int = id(worker)
            try:
                result = worker.result()  # 結果を取得
                results_by_worker_id[worker_id] = result
            except Exception as e:
                results_by_worker_id[worker_id] = e

        # 結果を input_param に合わせて返却
        if isinstance(tasks, dict):
            return {
                key: results_by_worker_id[worker_id]
                for key, worker_id in id_map.items()
            }
        if isinstance(tasks, list):
            return [
                results_by_worker_id[worker_id]
                for key, worker_id in id_map.items()
            ]



class MultiThreadWorker(_MultiWorkerBase):
    pass

    @classmethod
    def _executer(cls):
        return ThreadPoolExecutor



class MultiProcessWorker(_MultiWorkerBase):
    pass

    @classmethod
    def _executer(cls):
        return ProcessPoolExecutor
