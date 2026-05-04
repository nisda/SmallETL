from typing import List, Dict, Any, Tuple, Self, Union, Optional
from datetime import datetime
from collections import defaultdict

from boto3 import Session

from .tools import DynamoTools
from .table import DynamoTable
# from .libs.format_ex import format_recursive
from .libs.format_ex import data_mapping

class DynamoBatchUpdater():


    def __init__(self:Self, region_name:Optional[str] = None, session:Optional[Session] = None,):
        """コンストラクタ"""

        # メタデータ
        self.__meta_configs:Dict[str, DynamoTable] = {}

        # スタックデータ
        self.__stack_items:Dict[str, Dict[str, Any]] = defaultdict(dict)
        """ データ構造
            __stack_items = {
                "table_name" : {
                    "(pk, sk)" : {
                        "operation" : "Put|Delete",
                        "key"  : { key },
                        "item" : { item },
                        "meta" : { ttl, ... }
                    }
                }
            }
        """

        # session 取得
        self.__session = session if session else Session()
        self.__region_name = region_name

        # client/resource 取得
        self.__client = self.__session.client('dynamodb', region_name=region_name)
        self.__resource = self.__session.resource('dynamodb', region_name=region_name)


    def set_meta_config(
            self:Self,
            table_name:str,
            ttl_default:Union[int, datetime] = 0,
            updated_at_attr:Optional[str] = "updated_at",
            updated_at_format:Optional[str] = None,
            time_zone:str = "Asia/Tokyo",
        ):
        self.__meta_configs[table_name] = DynamoTable(
            table_name=table_name,
            region_name=self.__region_name,
            session=self.__session,
            ttl_default=ttl_default,
            updated_at_attr=updated_at_attr,
            updated_at_format=updated_at_format,
            time_zone=time_zone,
        )



    def get_stacks(self) -> Dict[str, Dict[Tuple, Dict[str, Any]]]:
        """スタックデータを取得"""
        return self.__stack_items


    def get_stack(self, table_name:str) -> Dict[Tuple, Dict[str, Any]]:
        """スタックデータを取得（テーブル指定）"""
        return self.__stack_items[table_name]


    def put_items(self, table_name:str, items:List[Dict[str, Any]], ttl:Union[int, datetime, None]=None, template:Dict=None) -> Dict[Tuple, Dict[str, Any]]:
        """データ追加"""

        # テンプレート変換
        if isinstance(template, dict):
            items = [
                data_mapping(template=template, data=v, assign_dtype='original')
                for v in items
            ]

        # データをスタックデータに保存
        for item in items:
            key:Dict = self.__get_primary_keys(table_name=table_name, item=item)
            key_hash:Tuple = self.__make_hashable(key)
            self.__stack_items[table_name][key_hash] = {
                "operation" : "Put",
                "key"  : key,
                "item" : item,
                "meta" : { "ttl": ttl },
            }

        # 終了：現在のスタックを返却
        return self.get_stack(table_name=table_name)


    def delete_items(self, table_name:str, items:List[Dict[str, Any]], template:Dict=None) -> Dict[Tuple, Dict[str, Any]]:
        """データ削除"""

        # テンプレート変換
        if isinstance(template, dict):
            items = [
                data_mapping(template=template, data=v, assign_dtype='original')
                for v in items
            ]

        # データをスタックデータに保存
        for item in items:
            key:Dict = self.__get_primary_keys(table_name=table_name, item=item)
            key_hash:Tuple = self.__make_hashable(key)
            self.__stack_items[table_name][key_hash] = {
                "operation" : "Delete",
                "key"  : key,
                "item" : None,
                "meta" : None,
            }

        # 終了：現在のスタックを返却
        return self.get_stack(table_name=table_name)



    def pre_delete(self, table_name:str, condition:Dict|List[Dict]) -> bool:
        """事前削除(登録のみ) / commit前であればいつでもOK"""

        # データ型を list に揃える
        conditions = [condition] if isinstance(condition, dict) else condition
        if not isinstance(conditions, list):
            raise TypeError(f"type `{type(conditions)}` is not supported.")

        # スタックに削除データを追加
        for cond in conditions:
            dynamo_table = self.__get_dynamo_table_obj(table_name=table_name)
            delete_items:List[Dict] = dynamo_table.query2(key_items=cond, primary_attr_only=True)
            for item in delete_items:
                key:Dict = self.__get_primary_keys(table_name=table_name, item=item)
                key_hash:Tuple = self.__make_hashable(key)
                # スタックに存在していないキーのみを登録
                if key_hash not in self.__stack_items[table_name].keys():
                    self.__stack_items[table_name][key_hash] = {
                        "operation" : "Delete",
                        "key"  : key,
                        "item" : None,
                        "meta" : None,
                    }

        # 終了
        return True



    def commit(self, transaction:bool=True) -> Dict[str, Dict[Tuple, Dict[str, Any]]]:

        # 実行前スタックデータ（返却用）を退避
        stack_items = self.__stack_items.copy()

        # 実行
        if transaction:
            self.__commit_transaction()
        else:
            self.__commit_batch_writer()

        # スタックデータ初期化
        self.__stack_items.clear()

        return stack_items



    def __set_meta_attr(self, table_name:str, item:Dict[str, Any], ttl:Union[int, datetime, None]) -> Dict[str, Any]:
        table:DynamoTable = self.__meta_configs.get(table_name, None)
        if table is None:
            # テーブル設定が未セット時は無加工で返却
            return item
        else:
            # 設定時は table のファンクションで加工
            return table.set_meta_attr(item=item, ttl=ttl)



    def __get_dynamo_table_obj(self, table_name:str) -> DynamoTable:
        """DynamoTable オブジェクトを取得"""
        
        if table_name in self.__meta_configs.keys():
            # meta_config で作成済みであればそれを取得
            return self.__meta_configs[table_name]
        else:
            # 未作成の場合は新規作成
            return DynamoTable(
                table_name=table_name,
                region_name=self.__region_name,
                session=self.__session,
            )


    def __commit_transaction(self) -> None:
        """Commit実行(トランザクションモード)"""

        # コマンドパラメータ生成
        transact_items: List[Dict] = []
        for table_name, commands in self.__stack_items.items():
            for idx in sorted(commands.keys()):
                command:Dict = commands[idx]
                operation:str = command["operation"].lower()

                if operation == "delete":
                    transact_items.append({
                        "Delete" : {
                            "TableName" : table_name,
                            "Key" : DynamoTools.type_serialize(item=command["key"]),
                        }
                    })
                elif operation == "put":
                    item:Dict = self.__set_meta_attr(
                        table_name=table_name,
                        item=command["item"],
                        **command["meta"]
                    )
                    transact_items.append({
                        "Put" : {
                            "TableName" : table_name,
                            "Item" : DynamoTools.type_serialize(item=item),
                        }
                    })

        # コマンド実行
        response = self.__client.transact_write_items(TransactItems=transact_items)

        return



    def __commit_batch_writer(self) -> None:
        """Commit 実行(BatchWriterモード)"""
 
        for table_name, commands in self.__stack_items.items():

            # データ振り分け
            delete_keys: List[Dict] = []
            put_items: List[Dict] = []
            for idx in sorted(commands.keys()):
                command:Dict = commands[idx]
                operation:str = command["operation"].lower()

                if operation == "delete":
                    delete_keys.append(command["key"])
                elif operation == "put":
                    item:Dict = self.__set_meta_attr(
                        table_name=table_name,
                        item=command["item"],
                        **command["meta"]
                    )
                    put_items.append(item)

            # 実行
            table = self.__resource.Table(table_name)
            with table.batch_writer() as batch:
                for item in put_items:
                    batch.put_item(Item=item)
                for key in delete_keys:
                    batch.delete_item(Key=key)

        # 終了
        return None


    def __get_primary_keys(self, table_name:str, item:Dict[str, Any]) -> Dict[str, Any]:
        """テーブルの PrimaryKey(PK+SK)のリストを取得"""

        table = self.__resource.Table(table_name)
        primary_keys:List[str] = [
            schema["AttributeName"]
            for schema in table.key_schema
        ]
        item_keys:Dict[str, Any] = { k: item[k] for k in primary_keys }
        return item_keys 


    def __make_hashable(self, obj) -> Tuple[Any]:
        """ lidt|dict のハッシュ化"""
        if isinstance(obj, dict):
            return tuple(sorted((k, self.__make_hashable(v)) for k, v in obj.items()))
        elif isinstance(obj, list):
            return tuple(self.__make_hashable(i) for i in obj)
        else:
            return obj


