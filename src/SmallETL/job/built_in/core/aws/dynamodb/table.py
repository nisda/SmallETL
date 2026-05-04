from typing import List, Dict, Any, Union, Optional, Tuple, Self, overload
from collections.abc import Iterator
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from boto3 import Session
from boto3.dynamodb.conditions import AttributeBase, Key, Attr, Or, And, Not
from botocore.exceptions import ClientError

from .index import DynamoIndex, DynamoIndexTypes
from .tools import DynamoTools


class DynamoTable:

    @property
    def table_name(self:Self) -> str:
        return self._table.table_name

    @property
    def pk(self:Self) -> DynamoIndex:
        return self._pk

    @property
    def gsi(self:Self) -> Dict[str, DynamoIndex]:
        return self._gsi

    @property
    def lsi(self:Self) -> Dict[str, DynamoIndex]:
        return self._lsi

    @property
    def ttl_name(self:Self) -> Optional[str]:
        return self._ttl_name

    @property
    def ttl_default(self:Self) -> Union[int, datetime]:
        return self._ttl_default

    @property
    def updated_at_attr(self:Self) -> Optional[str]:
        return self._updated_at_attr

    @property
    def updated_at_format(self:Self) -> Optional[str]:
        return self._updated_at_format

    @property
    def time_zone(self:Self) -> ZoneInfo:
        return self._time_zone


    def __init__(
            self:Self,
            table_name:str,
            region_name:str = None,
            session:Session = None,
            ttl_default:Union[int, datetime] = 0,
            updated_at_attr:Optional[str] = "updated_at",
            updated_at_format:Optional[str] = None,
            time_zone:str = "Asia/Tokyo"
        ):
        """コンストラクタ"""

        # session 取得
        session = session if session else Session()

        # client/resource 取得
        dynamodb_cli = session.client('dynamodb', region_name=region_name)
        dynamodb_rsc = session.resource('dynamodb', region_name=region_name)

        # Tableリソース取得
        self._table = dynamodb_rsc.Table(table_name)

        # PrimaryKey
        self._pk = DynamoIndex(
            table = self._table,
            name = None,
            type = DynamoIndexTypes.Primary,
            key_schemas = self._table.key_schema
        )

        # LocalSecondaryIndex
        lsi_list:List = self._table.local_secondary_indexes or []
        self._lsi = {}
        for idx_info in sorted(lsi_list, key=lambda x: x["IndexName"]):
            idx_name:str = idx_info["IndexName"]
            self._lsi[idx_name] = DynamoIndex(
                table = self._table,
                name  = idx_name,
                type  = DynamoIndexTypes.LSI,
                key_schemas = idx_info["KeySchema"]
            )

        # GlobalSecondaryIndex
        gsi_list:List = self._table.global_secondary_indexes or []
        self._gsi = {}
        for idx_info in sorted(gsi_list, key=lambda x: x["IndexName"]):
            idx_name:str = idx_info["IndexName"]
            self._gsi[idx_name] = DynamoIndex(
                table = self._table,
                name  = idx_name,
                type  = DynamoIndexTypes.GSI,
                key_schemas = idx_info["KeySchema"]
            )

        # ttl
        response = dynamodb_cli.describe_time_to_live(TableName=table_name)
        self._ttl_name = response.get("TimeToLiveDescription", {}).get("AttributeName", None)
        self._ttl_default = ttl_default

        # 更新日時属性設定
        self._updated_at_attr   = updated_at_attr
        self._updated_at_format = updated_at_format
        self._time_zone         = ZoneInfo(time_zone or "Asia/Tokyo")

        # 終了
        return


    def set_meta_attr(self, item:Dict, ttl:Union[int, datetime, None]) -> Dict[str, Any]:
        """メタ属性を追加"""

        def __add_updated_at(item:Dict, now_dt:datetime) -> Dict[str, Any]:
            # 名所未設定の場合はそのまま返却
            if not self.updated_at_attr:
                return item

            # 指定フォーマットで文字列化
            now_dt_str:str = now_dt.strftime(self._updated_at_format) \
                if self._updated_at_format else now_dt.isoformat()

            # セットして返却
            item[self.updated_at_attr] = now_dt_str
            return item

        def __add_ttl(item:Dict, ttl:Union[int, datetime, None], now_dt:datetime) -> Dict[str, Any]:
            # 名称未設定はそのまま返却
            if not self.ttl_name:
                return item

            # 個別指定なし（None）の場合はデフォルト値を採用
            ttl_tmp:Union[int, datetime, None] = self.ttl_default if ttl is None else ttl

            if isinstance(ttl_tmp, datetime):
                # datetime の場合はそれをセット
                item[self.ttl_name] = int(ttl_tmp.timestamp())
                return item

            elif isinstance(ttl_tmp, int):
                # int の場合は現在時刻に加算

                # 0 以下の場合はセットせず返却
                if ttl_tmp <= 0:
                    return item

                # 追加して返却
                ttl_dt:datetime = now_dt + timedelta(seconds=ttl_tmp)
                item[self.ttl_name] = int(ttl_dt.timestamp())
                return item

            else:
                # それ以外は何もせず返却
                return item


        # 追加属性をセットして返却
        now_dt:datetime = datetime.now(self.time_zone)
        ret = __add_updated_at(item=item, now_dt=now_dt)
        ret = __add_ttl(item=item, ttl=ttl, now_dt=now_dt)
        return ret


    def get_best_index(self, search_keys:List[str], range_compare_key:str=None) -> Optional[DynamoIndex]:
        """指定キー項目に適合するINDEXを取得"""

        def __calc_sort_priority(index_pair:Tuple[DynamoIndex, Dict[str, List[str]]]) -> Tuple:
            """ソート優先度の算出関数"""
            idx:DynamoIndex              = index_pair[0]
            key_def:Dict[str, List[str]] = index_pair[1]
            return (
                len(key_def["HASH"]) * -1,
                len(key_def["RANGE"]) * -1,
                { DynamoIndexTypes.Primary: 1, DynamoIndexTypes.LSI: 2, DynamoIndexTypes.GSI: 3}[idx.type],
                str(idx.name),
            )

        # パラメータチェック
        if not search_keys:
            raise ValueError("Argument `search_keys` is empty.")


        #-------------------------------
        # マッチする HASH-KEY/RANGE-KEY の数が多いものを返却
        #-------------------------------

        # マッチするキー情報を取得
        matched_indexes:List[Tuple[DynamoIndex, Dict[str, List[str]]]] = []
        for idx in [self.pk, *self.lsi.values(), *self.gsi.values()]:
            key_info = idx.containing_keys(search_keys=search_keys, range_compare_key=range_compare_key)
            if key_info:
                matched_indexes.append((idx, key_info))

        # マッチなしは None を返却
        if len(matched_indexes) == 0:
            return None

        # HASH-KEY数/RANGE-KEY数などでソートして返却
        sorted_indexes:List[DynamoIndex] = sorted(matched_indexes, key=__calc_sort_priority )
        return sorted_indexes[0][0]


    def scan(self, **kwargs) -> Iterator[Dict[str, Any]]:
        """全件取得"""

        while True:
            response = self._table.scan(**kwargs)
            for item in response['Items']:
                yield item
            if 'LastEvaluatedKey' not in response:
                break
            kwargs.update(ExclusiveStartKey=response['LastEvaluatedKey'])


    def truncate(self) -> List[Dict[str, Any]]:
        """データ全削除"""

        # キー値のリストを生成
        delete_keys:dict = [
            { k:v for k,v in x.items() if k in self.pk.all_keys }
            for x in self.scan()
        ]

        # データ削除
        with self._table.batch_writer() as batch:
            for key in delete_keys:
                batch.delete_item(Key=key)
        return delete_keys


    def query(self, KeyConditionExpression, IndexName:str=None, **kwargs) -> Iterator[List[Dict[str, Any]]]:
        """検索"""

        # required
        kwargs.update(KeyConditionExpression=KeyConditionExpression)

        # optional
        if IndexName is not None: kwargs.update(IndexName=IndexName)

        # exec
        while True:
            response = self._table.query(**kwargs)
            for item in response['Items']:
                yield item
            if 'LastEvaluatedKey' not in response:
                break
            kwargs.update(ExclusiveStartKey=response['LastEvaluatedKey'])


    @overload
    def query2(self, key_items:Dict[str, Any], primary_attr_only:bool=False, **kwargs) -> Iterator[List[Dict[str, Any]]]:
        pass

    @overload
    def query2(self, key_items:List[Dict[str, Any]], primary_attr_only:bool=False, **kwargs) -> Iterator[List[Dict[str, Any]]]:
        pass

    def query2(self, key_items:List[Dict[str, Any]], primary_attr_only:bool=False, **kwargs) -> Iterator[List[Dict[str, Any]]]:
        """より簡易に使える query"""

        if isinstance(key_items, list) and len(key_items)== 0:
            # 条件が空の場合は空リストを返却
            return

        elif isinstance(key_items, dict):
            # dictの場合はリスト形式に変換して再帰実行
            yield from self.query2(key_items=[key_items], primary_attr_only=primary_attr_only, **kwargs)

        elif isinstance(key_items, list):
            # 共通するキーを抽出して best-index を判別
            common_keys:List[str] = self.__extract_dict_common_keys(dicts=key_items)
            idx:DynamoIndex = self.get_best_index(search_keys=common_keys, range_compare_key=None)
            if idx is None:
                raise ValueError(f"No Index that matches the key_items. {common_keys}")
            # query実行
            yield from idx.query(items=key_items, primary_attr_only=primary_attr_only, **kwargs)


    def get_item(self, key:Dict[str,Any], **kwargs) -> Union[Dict[str, Any], None]:

        # キーのみ抽出
        get_keys:Dict[str, Any] = { k:v for k,v in key.items() if k in self.pk.all_keys }

        # 実行
        response = self._table.get_item(
            Key=get_keys,
            **kwargs
        )
        ret = response.get("Item", None)
        return ret


    def put_item(self, item, ttl:Union[int, datetime, None]=None, overwrite:bool=True, **kwargs:Dict[str, Any]) -> Union[Dict[str, Any], None]:
        """データ追加/更新"""

        # 追加属性セット
        temp_item:Dict[str, Any] = self.set_meta_attr(item=item, ttl=ttl)


        # 上書き不可：データ非存在を条件に追加
        if not overwrite:
            # 既存条件
            condition_org = kwargs.pop("ConditionExpression", None)

            # データ非存在条件を生成
            upsert_keys:Dict[str, Any] = { k:v for k,v in item.items() if k in self.pk.all_keys }
            condition_exists = Not(self.__join_conditions(
                operator=And, conditions=[Key(k).eq(v) for k,v in upsert_keys.items()]))

            # TTL条件を生成
            condition_ttl = None if self.ttl_name is None else (
                Key(self.ttl_name).lt(int(datetime.now().timestamp()))
            )

            # 連結して条件変数にセット
            kwargs["ConditionExpression"] = \
                self.__join_conditions(operator=And, conditions=[
                    condition_org,
                    self.__join_conditions(operator=Or, conditions=[condition_exists, condition_ttl]),
                ])

        # PUT実行
        try:
            response = self._table.put_item(
                Item=temp_item,
                **kwargs,
            )
            return temp_item
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return None
            else:
                raise


    def put_items(self, items:List[Dict[str,Any]], ttl:int|datetime|None=None) -> List[Dict]:
        """データ追加/更新（一括）"""

        # メタ属性を追加
        items_temp:List[Dict[str, Any]] = [
            self.set_meta_attr(item=item, ttl=ttl)
            for item in items
        ]

        # 実行
        with self._table.batch_writer() as batch:
            for item in items_temp:
                batch.put_item(Item=item)

        return items_temp


    def delete_item(self, key:Dict[str, Any], **kwargs:Dict[str, Any]) -> Union[Dict[str, Any], None]:
        """データ削除"""

        # キーのみ抽出
        delete_key:Dict[str, Any] = { k:v for k,v in key.items() if k in self.pk.all_keys }

        # データ存在を条件に追加（返却値の分岐のため）
        condition = self.__make_key_condition(keys=delete_key, type=Key, operator=And)
        condition_org = kwargs.pop("ConditionExpression", None)
        if condition_org:
            condition = And(condition, condition_org)

        # 削除実行
        try:
            self._table.delete_item(Key=delete_key, ConditionExpression=condition, **kwargs)
            return delete_key
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return None
            else:
                raise


    def delete_items(self, keys:List[Dict[str, Any]]) -> Dict[str, Any]:
        """データ削除（一括）"""

        # キー値のリストを生成
        delete_keys:List[Dict[str, Any]] = [ { k:v for k,v in x.items() if k in self.pk.all_keys } for x in keys ]

        # 実行
        with self._table.batch_writer() as batch:
            for key in delete_keys:
                batch.delete_item(Key=key)

        return delete_keys


    def update_item(self, 
        key:Dict[str, Any],
        set_attrs:Dict[str, Any]=None,
        add_attrs:Dict[str, Any]=None,
        remove_attrs:List[str]=None,
        ttl:Union[int, datetime, None]=None,
        **kwargs
    ):
        """
        データ更新
        ---
        まだ仕様が詰め切れていないため、使用は非推奨。
        """

        # キー抽出
        update_key:Dict[str, Any] = { k:v for k,v in key.items() if k in self.pk.all_keys }

        # 追加属性をセット
        set_attrs_temp:Dict[str, Any] = self.set_meta_attr(item=set_attrs, ttl=ttl)

        # 更新パラメータ生成
        update_params:Dict = DynamoTools.make_update_expression(
            set_attrs=set_attrs_temp,
            add_attrs=add_attrs,
            remove_attrs=remove_attrs,
        )

        response:Dict = self._table.update_item(
            Key=update_key,
            **update_params,
            **kwargs,
        )
        return response["Attributes"]



    def __join_conditions(self, operator:And|Or, conditions: List[AttributeBase|None]) -> AttributeBase|None:
        # 連結処理
        ret:None|AttributeBase = None
        for condition in [ x for x in conditions if x is not None]:
            # conditionを指定演算子で連結
            ret = condition if ret is None else operator(ret, condition)

        # 返却
        return ret


    def __make_key_condition(
            self,
            keys:Dict[str, Any],
            type:Key|Attr,
            operator:And|Or=And,
        ) -> AttributeBase:
        """
        Docstring for __make_key_condition  
        Key/Filterの条件リソースインタフェースを生成  
        """

        ret = None
        for k,v in keys.items():
            if ret is None:
                ret = type(k).eq(v)
            else:
                ret = operator(ret, type(k).eq(v))
        return ret


    def __make_hashable(self, obj) -> Tuple[Any]:
        if isinstance(obj, dict):
            return tuple(sorted((k, self.__make_hashable(v)) for k, v in obj.items()))
        elif isinstance(obj, list):
            return tuple(self.__make_hashable(i) for i in obj)
        else:
            return obj


    def __extract_dict_common_keys(self, dicts:List[Dict]) -> List:
        """dict of list から共通する dict キーを抽出"""
        if len(dicts) == 0:
            return []
        results: List = list(dicts[0].keys())
        for d in dicts:
            results = [ k for k in d.keys() if k in results ]
        return results

