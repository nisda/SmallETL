from typing import Any, Dict, List, Callable, Tuple, Literal, Type
import ast
import operator
import sys
import builtins
from string import Formatter as Formatter


class Evaluater():

    UNARY_OPERATORS = {
        ast.Not: operator.not_,    # not x
        ast.UAdd: operator.pos,    # +x
        ast.USub: operator.neg,    # -x
        ast.Invert: operator.invert # ~x
    }

    BIN_OPERATORS = {
        ast.Add: operator.add,  # +
        ast.Sub: operator.sub,  # -
        ast.Mult: operator.mul, # *
        ast.Div: operator.truediv, # /
        ast.Pow: operator.pow, # **
        ast.Mod: operator.mod, # %
    }

    COMPARE_OPERATORS = {
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Is: operator.is_,
        ast.IsNot: operator.is_not,
        ast.In: lambda a, b: a in b,
        ast.NotIn: lambda a, b: a not in b,
    }


    @property
    def funcs(self) -> Dict[str, Callable|None]|None:
        return self.__funcs

    @funcs.setter
    def funcs(self, funcs:Dict[str, Callable|None]|None):
        self.__funcs = funcs

    @property
    def dot_access(self) -> bool:
        return self.__dot_access

    @dot_access.setter
    def dot_access(self, value:bool):
        self.__dot_access = value


    # コンストラクタ
    def __init__(self, funcs:Dict[str, Callable|None]|None=None, dot_access:bool=True):
        """コンストラクタ"""
        self.funcs = funcs
        self.dot_access = dot_access


    def __evaluate_dict(self, node:ast.Dict, context:Dict[str, Any]):
        result = {}
        for k_node, v_node in zip(node.keys, node.values):
            if k_node is None:
                # **dict_obj のアンパック処理
                dict_to_unpack = self.__evaluate_node(v_node, context)
                if not isinstance(dict_to_unpack, dict):
                    raise TypeError(f"Cannot unpack non-dict type: {type(dict_to_unpack)}")
                result.update(dict_to_unpack)
            else:
                # 通常の key: value
                key = self.__evaluate_node(k_node, context)
                val = self.__evaluate_node(v_node, context)
                result[key] = val
        return result

    def __evaluate_set(self, node:ast.Set, context:Dict[str, Any]):
        result = set()
        for elt in node.elts:
            if isinstance(elt, ast.Starred):
                # {1, *others} のアンパック処理
                iterable = self.__evaluate_node(elt.value, context)
                result.update(iterable)
            else:
                # 通常の要素
                val = self.__evaluate_node(elt, context)
                result.add(val)
        return result

    def __evaluate_unary_op(self, node:ast.UnaryOp, context:Dict[str, Any]):
        val = self.__evaluate_node(node.operand, context)
        op_func = self.UNARY_OPERATORS[type(node.op)]
        return op_func(val)

    def __evaluate_subscript(self, node:ast.Subscript, context:Dict[str, Any]):
        """添え字処理"""
        obj = self.__evaluate_node(node.value, context)
        key = self.__evaluate_node(node.slice, context)
        try:
            # operator.getitem(obj, key) は obj[key] と等価
            return operator.getitem(obj, key)
        except (IndexError, KeyError, TypeError) as e:
            raise e

    def __evaluate_bin_op(self, node:ast.BinOp, context:Dict[str, Any]):
        op_func = self.BIN_OPERATORS[type(node.op)]
        return op_func(
            self.__evaluate_node(node.left, context),
            self.__evaluate_node(node.right, context)
        )

    def __evaluate_compare(self, node:ast.Compare, context:Dict[str, Any]):
        left_val = self.__evaluate_node(node.left, context)
        for op, right in zip(node.ops, node.comparators):
            op_func = self.COMPARE_OPERATORS[type(op)]
            right_val = self.__evaluate_node(right, context)
            if not op_func(left_val, right_val):
                return False
            left_val = right_val
        else:
            return True

    def __evaluate_bool_op(self, node:ast.BoolOp, context:Dict[str, Any]):
        """and / or を評価する (短絡評価対応)"""

        if isinstance(node.op, ast.And):
            for value_node in node.values:
                val = self.__evaluate_node(value_node, context)
                if not val:
                    return val
            return val #
            
        elif isinstance(node.op, ast.Or):
            for value_node in node.values:
                val = self.__evaluate_node(value_node, context)
                if val:
                    return val
            return val

    def __evaluate_call(self, node:ast.Call, context:Dict[str, Any]):
        # 引数の再帰的評価
        args = [ self.__evaluate_node(arg, context) for arg in node.args ]
        kwargs = { kw.arg: self.__evaluate_node(kw.value, context) for kw in node.keywords }

        if isinstance(node.func, ast.Name):
            # func の実体を取得して実行
            func_name = node.func.id

            # 関数定義あり
            safe_funcs = self.funcs
            if isinstance(safe_funcs, Dict):
                # 定義あり且つfunc名がマッチしない場合は不許可
                if func_name not in safe_funcs.keys():
                    raise PermissionError(f"execution of `{func_name}` is not permitted.")

                # functionが登録されている場合はそれを実行
                func_to_call = safe_funcs.get(func_name)
                if func_to_call is not None:
                    return func_to_call(*args, **kwargs)

            # global に指定 function が存在すれば実行
            if func_name in globals().keys():
                func_to_call = globals()[func_name]
                return func_to_call(*args, **kwargs)

            # builtins に指定 function が存在すれば実行
            if hasattr(builtins, func_name):
                func_to_call = getattr(builtins, func_name)
                return func_to_call(*args, **kwargs)

            # 該当する function なし。
            raise NameError(f"function '{func_name}' is not defined")

        else:
            # メソッドなどの場合
            func_to_call = self.__evaluate_node(node.func, context)
            return func_to_call(*args, **kwargs)

    def __evaluate_attrubute(self, node:ast.Attribute, context:Dict[str, Any]):
        obj = self.__evaluate_node(node.value, context)
        seg:str = node.attr

        if not self.dot_access:
            # ドットアクセスなしの時は attr 取得のみ
            return getattr(obj, seg)
        else:
            ## '0' は、ここに入ってこないみたい。
            # if isinstance(obj, (List, Tuple)):
            #     index:int = int(seg)
            #     return obj[index]

            if isinstance(obj, Dict):
                if seg in obj.keys():
                    return obj[seg]
                # if seg.isdigit():
                #     index:int = int(seg)
                #     if index in obj.keys():
                #         return obj[index]
                if hasattr(obj, seg):
                    return getattr(obj, seg)
                # 取得できない場合はエラー（KeyError優先）
                raise KeyError(seg)

            # Dict以外はgetattr
            return getattr(obj, seg)




    def __evaluate_joined_str(self, node:ast.JoinedStr, context:Dict[str, Any]):
        result = []
        for part in node.values:
            res = self.__evaluate_node(part, context)
            result.append(res)
        return "".join(result)

    def __evaluate_formatted_value(self, node:ast.FormattedValue, context:Dict[str, Any]):
        # 変数や式が含まれる部分 {value}
        val = self.__evaluate_node(node.value, context)
    
        # 1. 変換フラグ (!r, !s, !a) の適用
        if node.conversion == 115:   # !s
            val = str(val)
        elif node.conversion == 114: # !r
            val = repr(val)
        elif node.conversion == 97:  # !a
            val = ascii(val)
    
        # 2. 書式指定 (:02d 等) の適用
        if node.format_spec:
            # format_spec 自体も JoinedStr なので再帰的に評価
            spec = self.__evaluate_node(node.format_spec, context)
            val = format(val, spec)
        else:
            val = str(val)
        return val


    """node本処理"""
    def __evaluate_node(self, node:ast.AST, context:Dict[str, Any]) -> Any:

        # None
        if node is None:
            return None

        # リテラル（定数値）
        if isinstance(node, ast.Constant):
            return ast.literal_eval(node)


        # List
        if isinstance(node, ast.List):
            # 各要素 (node.elts) を再帰的に評価してリストにまとめる
            return [self.__evaluate_node(elt, context) for elt in node.elts]

        # Tuple
        if isinstance(node, ast.Tuple):
            return tuple(self.__evaluate_node(elt, context) for elt in node.elts)

        # Dict
        if isinstance(node, ast.Dict):
            return self.__evaluate_dict(node, context)

        # Set
        if isinstance(node, ast.Set):
            return self.__evaluate_set(node, context)

        # 変数名／識別子
        if isinstance(node, ast.Name):
            var_name:str = node.id
            return context[var_name]

        # 添え字
        if isinstance(node, ast.Subscript):
            return self.__evaluate_subscript(node, context)

        # slice
        if isinstance(node, ast.Slice):
            start = self.__evaluate_node(node.lower, context)
            stop = self.__evaluate_node(node.upper, context)
            step = self.__evaluate_node(node.step, context)
            return slice(start, stop, step)

        # 単項演算演算子
        if isinstance(node, ast.UnaryOp):
            return self.__evaluate_unary_op(node, context)

        # ２項演算
        if isinstance(node, ast.BinOp):
            return self.__evaluate_bin_op(node, context)

        # 比較
        if isinstance(node, ast.Compare):
            return self.__evaluate_compare(node, context)

        # 論理演算 (and / or)
        if isinstance(node, ast.BoolOp):
            return self.__evaluate_bool_op(node, context)

        # 関数
        if isinstance(node, ast.Call):
            return self.__evaluate_call(node, context)

        # Attribute
        if isinstance(node, ast.Attribute):
            return self.__evaluate_attrubute(node, context)

        # f-string
        if isinstance(node, ast.JoinedStr):
            return self.__evaluate_joined_str(node, context)

        # format-placeholder
        if isinstance(node, ast.FormattedValue):
            return self.__evaluate_formatted_value(node, context)

        # 未対応!!
        raise ValueError(f"{type(node)} are not supported")



    def eval(self, expression:str, /, mapping:Dict[str, Any]):
        # ast解析
        tree = ast.parse(expression)

        # 要素の有無をチェック
        if len(tree.body) == 0:
            return None
        if len(tree.body) > 1:
            raise ValueError("Multiple commands are not supported.")

        # ノード情報を取得
        node = tree.body[0].value

        return self.__evaluate_node(node=node, context=mapping)




    def format(
            self,
            template:str|Dict|List|Tuple,
            /,
            mapping:Dict[str, Any],
            recursive:bool = True,
            original_type:bool=True,
            errors:Literal['raise', 'coerce', 'ignore']='raise',
        ) -> Any:
        """テンプレートへのデータマッピング（再帰実行可）"""


        # オリジナルタイプ変換可否関数
        def __is_fieldname_only(expr:str) -> bool:
            try:
                # format(expr) を分解
                elements = [
                    dict(zip(['literal_text', 'field_name', 'format_spec', 'conversion'], p))
                    for p in Formatter().parse(expr)
                ]
                # １要素のみ且つ field_name のみである
                ret = bool(
                    len(elements) == 1
                    and not elements[0]['literal_text']
                    and not elements[0]['format_spec']
                    and not elements[0]['conversion']
                    and elements[0]['field_name']
                )
                return ret
            except Exception as e:
                return False


        # データ割り当て関数
        def __assign_data(expr:str, mapping:Dict):
            try:
                try:
                    if original_type and __is_fieldname_only(expr):
                        return self.eval(expr[1:-1], mapping=mapping)
                    else:
                        escaped_expr = expr.replace('"', '\\"')
                        return self.eval(f'f"{escaped_expr}"', mapping=mapping)
                except Exception as e:
                    e_type:Type = type(e)
                    e_msg:str   = f"{str(e).rstrip('.')}. occurred at expression='{expr}'"
                    raise e_type(e_msg) from e
            except Exception as e:
                if errors == 'coerce':
                    return None
                elif errors == 'ignore':
                    return expr
                else:
                    raise

        # パラメータまとめ
        common_params = {
            "mapping" : mapping,
            "recursive" : recursive,
            "original_type" : original_type,
            "errors" : errors,
        }

        # タイプ別に再帰実行
        if not recursive:
            # 再帰なし = 文字列であれば処理
            if isinstance(template, str):
                return __assign_data(template, mapping=mapping)
            else:
                return template

        elif isinstance(template, Dict):
            return {
                k: self.format(v, **common_params)
                for k,v in template.items()
            }

        elif isinstance(template, List):
            return [
                self.format(v, **common_params)
                for v in template
            ]

        elif isinstance(template, Tuple):
            return tuple(
                self.format(v, **common_params)
                for v in template
            )

        elif isinstance(template, str):
            return __assign_data(template, mapping=mapping)

        else:
            return template


