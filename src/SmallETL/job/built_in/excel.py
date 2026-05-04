from typing import Union
from .core.excel import ExcelWorkbook, ExcelWorksheet, Direction, Oriented


def read(
        path:str,
        sheetname:str,
        header:bool=False,
        skip_blank:bool=True,
        min_col:int|str="A", min_row:int=1,
        max_col:int|str=None,max_row:int=None,
        direction:Union[Direction, str]="Vertical",
        return_type:Union[Oriented, str]="Row",
    ):
    params = locals()
    del params["path"]
    del params["sheetname"]

    book = ExcelWorkbook(file=path)
    sheet = book.worksheet(sheetname=sheetname)
    ret = sheet.get_values(**params)
    return ret


