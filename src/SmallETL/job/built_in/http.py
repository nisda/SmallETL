from typing import List, Dict, Final
from datetime import datetime, date
from .core.http_requests.http_requests_plus import RequestsPlus

def get_text(url:str):

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
