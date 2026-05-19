from typing import Literal, Dict
import boto3




def get_object(
    bucket:str,
    key:str,
    type:Literal['str', 'bytes'] = 'str',
    encoding:str = 'utf-8',
    region_name:str=None,
    **kwargs,
) -> str | bytes:
    client = boto3.client("s3", region_name=region_name)
    response = client.get_object(
        Bucket=bucket,
        Key=key,
        **kwargs
    )
    ret:bytes = response['Body'].read()
    if type == 'str':
        return ret.decode(encoding=encoding)
    else:
        return ret


def get_file(
    bucket:str,
    key:str,
    filepath:str,
    type:Literal['str', 'bytes'] = 'str',
    encoding:str = 'utf-8',
    region_name:str=None,
    **kwargs,
) -> str | bytes:

    body = get_object(
        bucket=bucket,
        key=key,
        type=type,
        encoding=encoding,
        region_name=region_name,
        **kwargs,
    )

    mode = "w" if type.lower() == 'str' else 'wb'
    with open(filepath, mode) as f:
        f.write(body)

    return body


def put_object(
    bucket:str,
    key:str,
    body:bytes|str,
    encoding:str = 'utf-8',
    region_name:str=None,
    **kwargs,
) -> Dict:
    client = boto3.client("s3", region_name=region_name)

    # byte に変換
    if isinstance(body, str):
        body = body.encode(encoding=encoding)

    # 実行
    res = client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        **kwargs
    )
    return res


def put_file(
    bucket:str,
    key:str,
    filepath:str,
    encoding:str = 'utf-8',
    region_name:str=None,
    **kwargs,
) -> Dict:

    with open(filepath, "rb") as f:
        buffer = f.read()

    res = put_object(
        bucket=bucket,
        key=key,
        body=buffer,
        encoding=encoding,
        region_name=region_name,
        **kwargs,
    )

    return res

