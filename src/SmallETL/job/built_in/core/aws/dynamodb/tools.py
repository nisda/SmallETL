from typing import List, Dict, Any, Union, Self
from boto3.dynamodb.types import TypeSerializer, TypeDeserializer, Binary


class DynamoTools():

    @staticmethod
    def _convert_binary_to_bytes(item:Union[Binary, List, Dict, Any]) -> Any:
        """Convert: boto3.dynamodb.types.Binary -> bytes"""

        if isinstance(item, list):
            return [ Self.__convert_binary_to_bytes(x) for x in item ]
        if isinstance(item, dict):
            return { k: Self.__convert_binary_to_bytes(v) for k,v in item.items() }
        if isinstance(item, Binary):
            return item.value
        else:
            return item

    @staticmethod
    def type_serialize(item: Dict):
        return {k: TypeSerializer().serialize(value=v) for k, v in item.items()}

    @staticmethod
    def type_deserialize(item: Dict):
        return Self._convert_binary_to_bytes(item={k: TypeDeserializer().deserialize(value=v) for k, v in item.items()})

    @staticmethod
    def make_update_expression(
            set_attrs:Dict[str, Any]=None,
            add_attrs:Dict[str, Any]=None,
            remove_attrs:List[str]=None
        ):

        # INPUTパラメータの調整
        set_attrs    = set_attrs or {}
        add_attrs    = add_attrs or {}
        remove_attrs = remove_attrs or []

        # 更新情報の生成
        update_expressions:List[str] = []

        set_expressions:List    = [ f"#{k} = :{k}" for k in set_attrs.keys()]
        set_attr_names:dict     = { f"#{k}":k for k in set_attrs.keys() }
        set_attr_values:dict    = { f":{k}":v for k,v in set_attrs.items() }
        if len(set_expressions) > 0:
            update_expressions.append("SET " + ', '.join(set_expressions))

        remove_expressions:List = [ f"#{k}" for k in remove_attrs]
        remove_attr_names:dict   = { f"#{k}":k for k in remove_attrs }
        if len(remove_expressions) > 0:
            update_expressions.append("REMOVE " + ', '.join(remove_expressions))

        add_expressions:List    = [ f"#{k} = :{k}" for k in add_attrs.keys()]
        add_attr_names:dict     = { f"#{k}":k for k in add_attrs.keys() }
        add_attr_values:dict    = { f":{k}":v for k,v in add_attrs.items() }
        if len(add_expressions) > 0:
            update_expressions.append("ADD " + ', '.join(add_expressions))

        # 返却
        return {
            "UpdateExpression": " ".join(update_expressions),
            "ExpressionAttributeNames": {
                **set_attr_names,
                **remove_attr_names,
                **add_attr_names,
            },
            "ExpressionAttributeValues": {
                **set_attr_values,
                **add_attr_values,
            },
        }


