from typing import List

import glob
from pathlib import Path
from datetime import datetime
import shutil

def find(path) -> List[List[str]]:
    """ファイル検索"""

    paths = [ Path(p) for p in glob.glob(path) ]
    ret = [
        {
            "path" : str(p),
            "dirname" : str(p.parent),
            "filename" : p.name,
            "basename" : p.stem,
            "extension" : p.suffix,
            "size" : p.stat().st_size,
            "created" : p.stat().st_ctime,
            "modified" : p.stat().st_mtime,
            "created_iso" : datetime.fromtimestamp(p.stat().st_ctime).isoformat(),
            "modified_iso" : datetime.fromtimestamp(p.stat().st_mtime).isoformat(),
        }
        for p in paths
    ]
    return ret


def copy(src:str, dst:str):
    """ファイルコピー"""
    return shutil.copy(src, dst)

