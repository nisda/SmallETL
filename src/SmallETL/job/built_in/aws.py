from typing import List, Dict, Any, Tuple, Union, Optional, Iterator, Literal
from datetime import datetime
import boto3

from .core.aws.dynamodb import DynamoTable
from .core.aws.dynamodb import DynamoBatchUpdater


class s3():
    
    def get_object(
        cls,
        bucket:str,
        key:str,
        type:Literal['str', 'bytes'] = 'str',
        encoding:str = 'utf-8',
        region_name:str=None,
        **kwargs,
    ):
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
        cls,
        bucket:str,
        key:str,
        body:bytes|str,
        encoding:str = 'utf-8',
        region_name:str=None,
        **kwargs,
    ):
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
        return response



class dynamodb():
    """dynamodb"""


    @classmethod
    def truncate(
        cls,
        table_name:str,
        region_name:str = None,
    ) -> bool:
        table = DynamoTable(table_name=table_name, region_name=region_name)
        table.truncate()
        return True



    @classmethod
    def scan(
        cls,
        table_name:str,
        region_name:str = None,
    ) -> Iterator[List[Dict[str, Any]]]:
        """検索"""

        table = DynamoTable(table_name=table_name, region_name=region_name)
        res = table.scan()
        return list(res)



    @classmethod
    def query(
        cls,
        table_name:str,
        key_items:List[Dict[str, Any]],
        primary_attr_only:bool = False,
        region_name:str = None,
    ) -> Iterator[List[Dict[str, Any]]]:
        """検索"""

        table = DynamoTable(table_name=table_name, region_name=region_name)
        res = table.query2(key_items=key_items, primary_attr_only=primary_attr_only)
        return list(res)


    @classmethod
    def upsert_items(
        cls,
        table_name:str,
        items:List[Dict],
        template:Dict,
        pre_delete:Dict|List[Dict] = None,
        region_name:str = None,
        ttl:Union[int, datetime] = 0,
        updated_at_attr:Optional[str] = "updated_at",
        updated_at_format:Optional[str] = None,
        time_zone:str = "Asia/Tokyo",
        transaction:bool = True,
    ) -> bool:
        """UPSERT"""

        # 一括登録モジュールを生成
        dynamo_updater: DynamoBatchUpdater = DynamoBatchUpdater(region_name=region_name)
        dynamo_updater.set_meta_config(
            table_name=table_name,
            ttl_default = ttl,
            updated_at_attr = updated_at_attr,
            updated_at_format = updated_at_format,
            time_zone = time_zone,
        )

        # 事前削除
        if pre_delete:
            dynamo_updater.pre_delete(table_name=table_name, condition=pre_delete)

        # 追加/更新
        dynamo_updater.put_items(table_name=table_name, items=items, template=template)

        # コミット
        dynamo_updater.commit(transaction=transaction)

        # 正常終了
        return True


    @classmethod
    def delete_items(
        cls,
        table_name:str,
        items:List[Dict],
        template:Dict,
        region_name:str = None,
        transaction:bool = True,
    ) -> bool:
        """DELETE"""

        # 一括登録モジュールを生成
        dynamo_updater: DynamoBatchUpdater = DynamoBatchUpdater(region_name=region_name)

        # 追加/削除
        dynamo_updater.delete_items(table_name=table_name, items=items, template=template)

        # コミット
        dynamo_updater.commit(transaction=transaction)

        # 正常終了
        return True
