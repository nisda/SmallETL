from typing import Any
from enum import StrEnum, auto


class TaskStatus(StrEnum):
    Succeeded = auto()
    Aborted = auto()
    Skipped = auto()



class TaskResultInfo():

    def __init__(self, status:TaskStatus, output:Any):
        self.__status = status
        self.__output = output


    @property
    def status(self) -> TaskStatus:
        return self.__status

    @property
    def output(self) -> Any:
        return self.__output



