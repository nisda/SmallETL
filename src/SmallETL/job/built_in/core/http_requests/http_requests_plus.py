from .http_requests import _RequestsCore, Response
from typing import Union, Dict, Any, List, Tuple, override
import inspect
import time
import random
import logging


DEFAULTS_STATUS_CODES :List[int] = [
    408,    # 408 Request Timeout
    423,    # 423 Locked
    429,    # 429 Too Many Requests
    500,    # 500 Internal Server Error
    502,    # 502 Bad Gateway
    503,    # 503 Service Unavailable
    504,    # 504 Gateway Timeout
]


logger: logging.Logger = logging.getLogger(__name__)


class RequestsPlus(_RequestsCore):
    _base_url:str
    _base_params: Dict[str, Any]
    _base_headers: Dict[str, str]
    _retry_count:int
    _retry_interval:int
    _retry_jitter:int
    _retry_backoff:int
    _retry_status_codes: List[int]


    def __init__(
            self,
            base_url: str,
            base_params: Dict[str, Any] = None,
            base_headers: Dict[str, str] = None,
            retry_count: int = 0,
            retry_interval: int = 0,
            retry_jitter: int = 0,
            retry_backoff: int = 0,
            retry_stasus_codes: List[int] = [
                408,    # 408 Request Timeout
                423,    # 423 Locked
                429,    # 429 Too Many Requests
                500,    # 500 Internal Server Error
                502,    # 502 Bad Gateway
                503,    # 503 Service Unavailable
                504,    # 504 Gateway Timeout
            ]
        ):

        self._base_url      = base_url
        self._base_params   = base_params
        self._base_headers  = base_headers
        self._retry_count   = retry_count
        self._retry_interval = retry_interval
        self._retry_jitter  = retry_jitter
        self._retry_backoff = retry_backoff
        self._retry_status_codes = retry_stasus_codes

    @override
    def _request(
        self,
        method: str,
        path: str,
        params: Dict[str, Any] = None,
        data: Union[Dict, List[Tuple], str, bytes] = None,
        json: Dict = None,
        headers: Dict[str, str] = None,
        files: dict = None,
    ):

        # path を結合
        combined_url: str = f"{self._base_url.rstrip("/")}/{path}"

        # querystring をマージ
        combined_params: Dict[str, Any] = {
            **(self._base_params or {}),
            **(params or {}),
        }
        # querystring の None を除去
        combined_params = { # None を除去
            k:v for k,v in combined_params.items()
            if v is not None
        }

        # headers をマージ
        combined_headers: Dict[str, Any] = {
            **(self._base_headers or {}),
            **(headers or {}),
        }
        # headers の None を除去
        combined_headers = { # None を除去
            k:v for k,v in combined_headers.items()
            if v is not None
        }


        # リクエスト実行（リトライあり）
        for i in range(0, self._retry_count+1):
            logger.info(f"http-request[{i}] {method} {combined_url}")

            # リクエスト実行
            ret = super()._request(
                method=method,
                url=combined_url,
                params=combined_params,
                data=data,
                json=json,
                headers=combined_headers,
                files=files,
            )
            logger.info(f"http-request[{i}] {method} {combined_url} -> {ret.status_code}")

            # 指定ステータスコードかつ最大リトライ回数未満の場合は wait 後に再試行
            if (ret.status_code in self._retry_status_codes) and (i < self._retry_count):
                time.sleep(self._retry_interval)
                time.sleep(self._retry_jitter * random.random())
                time.sleep(self._retry_backoff * 2 ** i)
                continue

            # 実行結果を返却
            return ret



    @override
    def get(
        self,
        path: str,
        params: Dict[str, Any] = None,
        data: Union[Dict, List[Tuple], str, bytes] = None,
        json: Dict = None,
        headers: Dict[str, str] = None,
    ) -> Response:
        return self._request(
            method="GET",
            path=path,
            params=params,
            data=data,
            json=json,
            headers=headers,
        )

    @override
    def head(
        self,
        path: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> Response:
        return self._request(
            method="HEAD",
            path=path,
            params=params,
            headers=headers,
        )

    @override
    def post(
        self,
        path: str,
        params: Dict[str, Any] = None,
        data: Union[Dict, List[Tuple], str, bytes] = None,
        json: Dict = None,
        headers: Dict[str, str] = None,
        files: dict = None,
    ) -> Response:
        return self._request(
            method="POST",
            path=path,
            params=params,
            data=data,
            json=json,
            headers=headers,
            files=files,
        )

    @override
    def put(
        self,
        path: str,
        params: Dict[str, Any] = None,
        data: Union[Dict, List[Tuple], str, bytes] = None,
        json: Dict = None,
        headers: Dict[str, str] = None,
        files: dict = None,
    ) -> Response:
        return self._request(
            method="PUT",
            path=path,
            params=params,
            data=data,
            json=json,
            headers=headers,
            files=files,
        )

    @override
    def patch(
        self,
        path: str,
        params: Dict[str, Any] = None,
        data: Union[Dict, List[Tuple], str, bytes] = None,
        json: Dict = None,
        headers: Dict[str, str] = None,
        files: dict = None,
    ) -> Response:
        return self._request(
            method="PATCH",
            path=path,
            params=params,
            data=data,
            json=json,
            headers=headers,
            files=files,
        )

    @override
    def delete(
        self,
        path: str,
        params: Dict[str, Any] = None,
        data: Union[Dict, List[Tuple], str, bytes] = None,
        json: Dict = None,
        headers: Dict[str, str] = None,
    ) -> Response:
        return self._request(
            method="DELETE",
            path=path,
            params=params,
            data=data,
            json=json,
            headers=headers,
        )

    @override
    def options(
        self,
        path: str,
        params: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
    ) -> Response:
        return self._request(
            method="OPTIONS",
            path=path,
            params=params,
            headers=headers,
        )

