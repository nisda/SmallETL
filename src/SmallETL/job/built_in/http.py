from typing import List, Dict, Final
from datetime import datetime, date
from .core.http_requests.http_requests_plus import RequestsPlus

__WEEKDAYS_JP:Final[str] = ['月', '火', '水', '木', '金', '土', '日']
__WEEKDAYS_EN:Final[str] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

def get_text(url:str):

    #-----------------------------------------
    #   内閣府の公開するリストから取得
    #-----------------------------------------
    params = {
        "base_url"       : url,
        "retry_count"    : 4,
        "retry_interval" : 0.5,
        "retry_jitter"   : 0,
        "retry_backoff"  : 0,
    }
    req = RequestsPlus(**params)
    res = req.get(path="")
    res.raise_for_status()

    # 返却
    return res.text
