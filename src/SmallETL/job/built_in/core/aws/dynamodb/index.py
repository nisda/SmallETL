from typing import List, Dict, Any, Union, Tuple, Self, overload
from collections.abc import Iterator
from enum import Enum

from boto3.dynamodb.conditions import AttributeBase, Key, Attr, Or, And, Not




class DynamoIndexTypes(Enum):
    Primary = "PrimaryIndex"
    LSI = "LocalSecondaryIndex"
    GSI = "GlobalSecondaryIndex"



class DynamoIndex:

    @property
    def table(self) -> object:
        return self._table

    @property
    def name(self) -> str|None:
        return self._name

    @property
    def type(self) -> DynamoIndexTypes:
        return self._type

    @property
    def hash_keys(self) -> List[str]:
        return self._hash_keys

    @property
    def range_keys(self) -> List[str]:
        return self._range_keys

    @property
    def all_keys(self) -> List[str]:
        return self._hash_keys + self._range_keys


    def __init__(self:Self, table:object, name:str|None , type:DynamoIndexTypes, key_schemas:List[Dict[str, str]]):

        def __divide_key_schemas(schemas) -> Dict[str, List[str]]:
            """キースキーマ定義を HASH と RANGE に分離"""
            hash_keys:List[str] = []
            range_keys:List[str] = []
            for schema in schemas:
                key_type:str = schema["KeyType"]
                attr_name:str = schema["AttributeName"]
                if key_type.upper() == "HASH":
                    hash_keys.append(attr_name)
                elif key_type.upper() == "RANGE":
                    range_keys.append(attr_name)
            return {
                "HASH": hash_keys,
                "RANGE": range_keys
            }

        self._table:object          = table
        self._name:str|None         = name
        self._type:DynamoIndexTypes       = type

        devided_schemas:Dict = __divide_key_schemas(schemas=key_schemas)
        self._hash_keys:List[str]    = devided_schemas["HASH"]
        self._range_keys:List[str]   = devided_schemas["RANGE"]

        return


    def containing_keys(self, search_keys:List[str], range_compare_key:str=None) -> None|Dict[str, List[str]]:
        """含有キー取得（キー項目一致判定）"""

        # HASH キーは全て含まれている必要あり
        if not all(k in search_keys for k in self.hash_keys):
            return None

        if range_compare_key:
            # range_key が指定されている場合は
            # range_key とそれより前方のキーをすべて含む必要あり。

            # range_key を含んでいないときは不一致
            if not range_compare_key in self.range_keys:
                return None

            # INDEXの RANGE-KEY を、指定 range_key の前方と後方に分割
            range_key_idx:int = self.range_keys.index(range_compare_key)
            keys_left:List[str] = self._range_keys[:range_key_idx]

            if all(k in search_keys for k in keys_left):
                # 前方のキーをすべて含んでいればOK
                return {
                    "HASH" : self.hash_keys,
                    "RANGE" : [*keys_left, range_compare_key],
                }
            else:
                # 含んでいなければNG       
                return None

        else:
            # range_key が指定されていない場合は
            # RANGE-KEY を前から順に走査し、検索キーに含まれている分だけ取得

            keys_left:List[str] = []
            for k in self.range_keys:
                if k in search_keys:
                    keys_left.append(k)
                else:
                    # 非含有キーに達したら終了
                    break
            return {
                "HASH"  : self.hash_keys,
                "RANGE" : keys_left,
            }

    @overload
    def query(self, items:Dict[str, Any], primary_attr_only:bool=False, **kwargs:Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        ...

    @overload
    def query(self, items:List[Dict[str, Any]], primary_attr_only:bool=False, **kwargs:Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        ...

    def query(self, items:Union[Dict[str, Any], List[Dict[str, Any]]], primary_attr_only:bool=False,  **kwargs:Dict[str, Any]) -> Iterator[List[Dict[str, Any]]]:
        #-----------------------------------------
        #   パラメータチェック＆調整
        #-----------------------------------------
        if not items:
            raise ValueError("Argument `items` is empty")

        # 条件をリストに変換
        if isinstance(items, dict):
            items = [items]

        # ユニーク化
        items = self.__uniqueness_dict(dicts=items)

        #-----------------------------------------
        #   query条件生成
        #-----------------------------------------

        # 全条件に共通するキーを取得
        common_keys:List[str] = self.__extract_dict_common_keys(dicts=items)


        # 共通キーをもとに検索キー項目を取得
        search_keys = self.containing_keys(search_keys=common_keys, range_compare_key=None)
        if not search_keys:
            raise ValueError(f"No match on INDEX. {common_keys}")


        # 検索キー項目を平坦化（一次元リスト化）
        search_keys_flat: List[str] = [ y for x in search_keys.values() for y in x ]


        # 指定された検索条件を Key/Filter に振り分け
        query_items:List[Dict[str, Dict[str, Any]]]= [
            {
                "key_items" :  { k:v for k,v in item.items() if k in search_keys_flat },
                "filter_items" :  { k:v for k,v in item.items() if k not in search_keys_flat },
            }
            for item in items
        ]

        # key_items でグループ化＆ソート
        temp_items: Dict[Tuple, List] = {}
        for x in query_items:
            hash = self.__make_hashable(x["key_items"])
            if hash in temp_items.keys():
                temp_items[hash]["filter_items"].append(x["filter_items"])
            else:
                temp_items[hash] = {
                    "key_items" : x["key_items"],
                    "filter_items" : [ x["filter_items"] ],
                }
        grouped_items: List[Dict[str, List]] = [
            temp_items[k] for k in sorted(temp_items.keys())
        ]

        #-----------------------------------------
        #   query実行
        #-----------------------------------------
        for tmp_item in grouped_items:
            ret_items = self.__query_one(key_item=tmp_item["key_items"], filter_items=tmp_item["filter_items"], primary_attr_only=primary_attr_only, **kwargs)
            yield from ret_items

        return




    def __query_one(self, key_item:Dict[str, Any], filter_items:List[Dict[str, Any]], primary_attr_only:bool, **kwargs:Dict[str, Any]) -> Iterator[List[Dict[str, Any]]]:
        """
        query実行(1条件)
        """

        #---------------------
        # filter 調整
        #---------------------

        # 空の条件が含まれている場合は None にして条件を排除する。
        # 他のfilter条件にも必ず合致することになり、それらが無意味になるため。
        if {} in filter_items:
            filter_items = []

        #---------------------
        # Conditionオブジェクトに変換
        #---------------------

        # Conditionオブジェクトに変換
        key_condition       = self.__make_condition_eq(keys=key_item, type=Key, operator=And)

        ## 最後に自力でfilterをかけるため不使用（コメントアウト）
        # filter_conditsion   = self.__join_conditions(
        #     operator=Or,
        #     conditions=[
        #         self.__make_condition_eq(keys=x, type=Attr, operator=And)
        #         for x in filter_items
        #     ]
        # )

        #-----------------------------------------
        #   検索実行
        #-----------------------------------------
        # パラメータ調整
        primary_attr_names = [ x["AttributeName"] for x in self.table.key_schema ]
        params: Dict = {
            k:v
            for k,v in {
                "IndexName" : self.name,
                "KeyConditionExpression" : key_condition,
                "ProjectionExpression" : ",".join(primary_attr_names) if primary_attr_only else None
                # "FilterExpression" : filter_conditsion,
            }.items()
            if v
        }

        # 実行（iterator）
        while True:
            response = self._table.query(**kwargs, **params)
            for item in response['Items']:
                if filter_items:
                    for filter_item in filter_items:
                        if filter_item.items() <= item.items():
                            yield item
                            break
                else:
                    yield item

            if 'LastEvaluatedKey' not in response:
                break
            kwargs.update(ExclusiveStartKey=response['LastEvaluatedKey'])

        return


    def __make_condition_eq(self, keys:Dict[str, Any], type:Key|Attr, operator:And|Or=And) -> AttributeBase:
        """
        Key/Filterの条件リソースインタフェースを生成  
        """

        ret = None
        for k,v in keys.items():
            if ret is None:
                ret = type(k).eq(v)
            else:
                # ret = ret & type(k).eq(v)
                ret = operator(ret, type(k).eq(v))
        return ret


    def __join_conditions(self, conditions: List[AttributeBase|None], operator:And|Or) -> AttributeBase|None:
        """
        conditionを指定の結合子で連結
        """

        # 連結処理
        ret:None|AttributeBase = None
        for condition in [ x for x in conditions if x is not None]:
            # conditionを指定演算子で連結
            ret = condition if ret is None else operator(ret, condition)

        # 返却
        return ret


    def __make_hashable(self, obj) -> Tuple[Any]:
        """
        dict/list をhash化
        """

        if isinstance(obj, dict):
            return tuple(sorted((k, self.__make_hashable(v)) for k, v in obj.items()))
        elif isinstance(obj, list):
            return tuple(self.__make_hashable(i) for i in obj)
        else:
            return obj


    def __extract_dict_common_keys(self, dicts:List[Dict]) -> List:
        """
        List[Dict] から共通する dict キーを抽出
        """

        if len(dicts) == 0:
            return []
        results: List = list(dicts[0].keys())
        for d in dicts:
            results = [ k for k in d.keys() if k in results ]
        return results

    def __uniqueness_dict(self, dicts:List[Dict]) -> List[Dict]:
        """
        List[Dict] をユニーク化
        """

        ret:List[Dict] = []
        for d in dicts:
            if d not in ret:
                ret.append(d)
        return ret

