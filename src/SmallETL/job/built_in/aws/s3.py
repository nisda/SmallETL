from typing import Literal
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


def put_object(
    bucket:str,
    key:str,
    body:bytes|str,
    encoding:str = 'utf-8',
    region_name:str=None,
    **kwargs,
) -> None:
    client = boto3.client("s3", region_name=region_name)

    # byte に変換
    if isinstance(body, str):
        body = body.encode(encoding=encoding)

    # 実行
    response = client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        **kwargs
    )
    return None

