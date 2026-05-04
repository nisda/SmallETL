from typing import List, Dict, Final
from datetime import datetime, date
from .core.http_requests.http_requests_plus import RequestsPlus

__WEEKDAYS_JP:Final[str] = ['月', '火', '水', '木', '金', '土', '日']
__WEEKDAYS_EN:Final[str] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

def get_public_holidays_jp(start_date:date=None, end_date:date=None):

    #-----------------------------------------
    # パラメータ調整
    #-----------------------------------------
    if not start_date:
        start_date = date.min
    if isinstance(start_date, datetime):
        start_date = start_date.date()

    if not end_date:
        end_date = date.max
    if isinstance(end_date, datetime):
        end_date = end_date.date()



    #-----------------------------------------
    #   内閣府の公開するリストから取得
    #-----------------------------------------
    params = {
        "base_url"       : "https://www8.cao.go.jp/",
        "retry_count"    : 4,
        "retry_interval" : 0.5,
        "retry_jitter"   : 0,
        "retry_backoff"  : 0,
    }
    req = RequestsPlus(**params)
    res = req.get(path="/chosei/shukujitsu/syukujitsu.csv")
    body:bytes = res._content
    csv_text:str = body.decode('sjis')

    #-----------------------------------------
    # List[Dict] に形式変換
    #-----------------------------------------
    ret = [
        {
            "date" : line.split(",")[0].strip(),
            "name" : line.split(",")[1].strip(),
        }
        for line in csv_text.splitlines()
        if line.strip()
    ]
    # １行目は見出しのため除去
    ret = ret[1:]




    #-----------------------------------------
    # データを追加編集
    #-----------------------------------------
    temp = []
    for line in ret:
        dt:date = datetime.strptime(line["date"], '%Y/%m/%d').date()

        # 日付が範囲外のときスキップ
        if not (start_date <= dt and dt <= end_date):
            continue

        temp.append({
            # "date" : dt.date(),
            "date" : dt.strftime('%Y-%m-%d'),
            "name" : line["name"],
            "week" : {
                "code": dt.weekday(),
                "en": __WEEKDAYS_EN[dt.weekday()],
                "jp": __WEEKDAYS_JP[dt.weekday()],
            }
        })
    ret = temp


    # 返却
    return ret
