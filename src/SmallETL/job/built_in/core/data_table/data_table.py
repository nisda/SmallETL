from typing import Tuple, List, Dict, Any, Union, Self, overload, Type, Optional, Final, Literal, Callable, Set
from itertools import zip_longest, product
from functools import cmp_to_key
from collections import defaultdict
import re
import statistics
from .libs.data_converter import DataConverter
from collections import Counter
import copy



class DataTable():

    class _Tools():

        @classmethod
        def is_array(cls, data:Any) -> bool:
            """list化可能なデータかどうかを判定"""
            # list化可能だが除外するタイプ
            if isinstance(data, (str, bytes, bytearray)):
                return False
            # list化してみて判定する
            try:
                list(data)
                return True
            except:
                return False

        @classmethod
        def array_length(cls, data:Any) -> int:
            """list化した場合の長さを取得。NGの場合は-1"""
            return len(list(data)) if cls.is_array(data) else -1

        @classmethod
        def indexes(cls, values:List[Any], search:List[Any], compare_int_str:bool=True) -> List[int]:
            """
            リストから複数指定値を検索し、indexリストを取得する。
            存在しない値は Null を返却。
            """
            ret = []
            for key in search:
                if key in values:
                    # 存在する場合
                    ret.append(values.index(key))
                else:
                    # マッチしない場合は None
                    ret.append(None)

            return ret


        @classmethod
        def custom_compare(cls, a, b, keys=[]):
            """ dict/list の比較関数"""
            def __compare_core(a, b):
                if isinstance(a, tuple) and isinstance(b, tuple):
                    # 先頭要素から比較
                    for i in range(0, min(len(a), len(b))):
                        ret = __compare_core(a[i], b[i])
                        if ret != 0:
                            return ret
                    else:
                        # 最後まで一致していたら長さで比較
                        return len(a) - len(b)

                if a is None:
                    return -1
                if b is None:
                    return 1
                if a < b:
                    return -1
                if a > b:
                    return 1
                return 0

            if keys:
                a = [ a[k] for k in keys]
                b = [ b[k] for k in keys]
            elif isinstance(a, dict):
                a = a.values()
                b = b.values()
        
            return __compare_core(a=tuple(a), b=tuple(b))


        @classmethod
        def is_contains(cls, data:Any, condition:Any) -> bool:
            """
            dict条件合致判断
            data に condition が含まれているかを判定する。
            """

            if isinstance(condition, dict):
                # dict の場合は子要素を比較

                if not isinstance(data, dict):
                    # 両方dictでなかったらNG
                    return False

                if ( (data.keys() & condition.keys()) ^ condition.keys() ):
                    # conditionで指定されたkeyがすべて含まれていなかったらNG
                    return False

                # 再帰呼び出しで下層を比較
                for k in condition.keys():
                    if not cls.is_contains(data[k], condition[k]):
                        return False

                # すべて通ったらTrue
                return True

            elif isinstance(condition, list):
                # list の場合は、data の値が list に含まれていたらOK
                for c in condition:
                    if cls.is_contains(data, c):
                        return True
                return False

            elif isinstance(condition, re.Pattern):
                # condition が正規表現の場合、それにマッチしたらOK
                return bool(condition.match(data))

            elif isinstance(condition, Callable):
                # condition が Callable のときはデータをパラメータにしてコール
                return condition(data)

            else:
                # それ以外のパターンは値として単純比較
                return bool(data == condition)



        @classmethod
        def grouping_rows(cls, data:List[List[Any]], indexes:List[int]) -> Dict[Tuple[Any], List[List[Any]]]:
            """データリストを指定キーでグループ化"""

            # グループ化
            ret:dict = defaultdict(list)
            for d in data:
                keys = tuple([ d[i] for i in indexes ])
                ret[keys].append(d)

            # キーでソート
            sorted_keys = sorted(ret.keys(), key=cmp_to_key(lambda x,y: cls.custom_compare(x, y)))
            ret = {
                k: ret[k]
                for k in sorted_keys
            }

            return dict(ret)



    @property
    def columns(self) -> Tuple[str]:
        """カラム名のリスト"""
        return tuple(self.__columns)


    @columns.setter
    def columns(self, value:List[str]|None):
        """カラム名のリスト[setter]"""

        # None の場合は連番[str]をセット
        if value is None:
            col_len:int = len(self.__records[0]) if self.__records else 0
            self.__columns = [ str(i) for i in range(0, col_len) ]
            return

        # データ型チェック
        if not isinstance(value, (List, Tuple)):
            raise TypeError("Type of `columns` must be 'list' or 'tuple'")

        # カラム名の変換および重複チェック
        str_columns = [ str(v) for v in value ]
        dup_keys:List[str] = [ k for k,v in Counter(str_columns).items() if v > 1 ]
        if dup_keys:
            error_keys:List[str] = [
                f"{i}:{x} <{type(x).__name__}>" for i, x in enumerate(str_columns)
                if str(x) == dup_keys[0]
            ]
            raise ValueError(f"column names are duplicated. ({','.join(error_keys)})")

        # 列数チェック＆セット
        if not ( self.row_count == 0 or self.column_count == len(str_columns) ):
            raise ValueError("The `column` length does not match the data-length.")

        # カラム名セット（更新）
        self.__columns = str_columns

    @property
    def row_count(self) -> int:
        """レコード数"""
        return len(self.__records)

    @property
    def column_count(self) -> int:
        """カラム数"""
        if 0 < self.row_count:
            # データが１件でも存在する場合はその長さ
            return len(self.__records[0])
        elif self.columns is not None:
            # カラム名が設定されているときはその長さ
            return len(self.columns)
        else:
            # 計測不能
            return 0



    @overload
    def __init__(self, data:Dict[str, List[Any]], columns:List[str]=None):
        pass

    @overload
    def __init__(self, data:Dict[str, Any], columns:List[str]=None):
        pass

    @overload
    def __init__(self, data:List[Dict[str, Any]], columns:List[str]=None):
        pass

    @overload
    def __init__(self, data:List[List[Any]], columns:List[str]=None):
        pass

    @overload
    def __init__(self, data:List[Any], columns:List[str]=None):
        pass

    @overload
    def __init__(self, data:Any, columns:List[str]=None):
        pass



    # コンストラクタ（本体）
    def __init__(self, data, columns:List[str]=None):
        """コンストラクタ"""

        # 初期化
        self.__columns: List[str]       = []
        self.__records: List[List[Any]] = []


        # データ読み込み
        keys, recs = self.__load_records(data=data)

        # レコードをセット
        self.__records = recs

        # カラム名をセット
        if columns:
            # columns 指定がある場合はそれをセット
            self.columns = columns
        else:
            # columns 指定が無ければデータから読み込んだカラム名をセット
            self.columns = keys


    # 初期処理: データ読み込み（振り分け）
    def __load_records(self, data) -> Tuple[List[str]|None, List[List[Any]]]:
        """データ読み込み"""


        #------------------------------------------
        # データタイプ別の読み込み
        #------------------------------------------
        if data is None:
            # 空テーブル
            return (None, [])

        elif isinstance(data, Dict):

            if len(data) == 0:
                # 空テーブル
                return (None, [])

            elif isinstance(data[tuple(data.keys())[0]], (List, Tuple)):
                # Dict[str, List[Any]]: 列指向データ
                return self.__load_col_oriented(data=data)

            else:
                # Dict[str, Any]
                # List[Dict[str, Any]] 形式に変換して行指向データとして処理
                return self.__load_row_oriented_dict(data=[data])

        elif isinstance(data, (List, Tuple)):

            if len(data) == 0:
                # 空テーブル
                return (None, [])

            elif isinstance(data[0], Dict):
                # List[Dict[str, Any]]: 行指向データ（カラム名あり）
                return self.__load_row_oriented_dict(data=data)

            elif isinstance(data[0], List):
                # List[List[Any]]: 行指向データ（カラム名なし）
                return self.__load_row_oriented_list(data=data)

            else:
                # List[Any]: 1列／複数レコード
                # List[List[Any]]（縦持ち）に変換して読み込み
                return self.__load_row_oriented_list(data=[ [d] for d in data])

        else:
            # Any: 1データのみ
            # List[List[Any]]に変換して読み込み
            return self.__load_row_oriented_list(data=[[data]])


    # 初期処理: データ読み込み（列指向データ）
    def __load_col_oriented(self, data:Dict[str, List[Any]]) -> Tuple[List[str], List[List[Any]]]:
        """列指向データ読み込み"""

        # カラム名を取得
        keys: List[str] = list(data.keys())

        # データを行指向に変換。データ数不足はNone埋め。
        records: List[List[Any]] = [
            list(row) for row in zip_longest(*data.values(), fillvalue=None)
        ]

        # 返却
        return keys, records


    # 初期処理: データ読み込み（行指向データ／カラム名あり[dict]）
    def __load_row_oriented_dict(self, data:List[Dict[str, Any]]) -> Tuple[List[str], List[List[Any]]]:
        """行指向データ（カラム名あり）読み込み"""

        # 全レコードのキーを抽出してユニーク化。
        keys: List[str] = list(dict.fromkeys([key for d in data for key in d.keys()]))

        # 全レコードをキー順にリスト化。非存在キーは None 埋め。
        records: List[List[Any]] = [
            [d.get(k, None) for k in keys] for d in data
        ]

        # 返却
        return keys, records


    # 初期処理: データ読み込み（行指向データ／カラム名なし[list]）
    def __load_row_oriented_list(self, data:List[Any]) -> Tuple[None, List[List[Any]]]:
        """行指向データ（カラム名なし）読み込み"""

        # 1. 最大の列数を取得
        max_len = max(len(row) for row in data)
        
        # 2. 各行が最大列数になるまで None を追加
        records: List[List[Any]] =[
            row + [None] * (max_len - len(row))
            for row in data
        ]

        return None, records


    # DataTable複製
    def clone(self) -> Self:
        """DataTable複製"""
        columns = self.__columns
        records = self.rows(type='list')
        return DataTable(data=records, columns=columns)


    # カラム名リネーム
    def rename(self, columns:Dict|List):
        # list のときはそのままセット（ self.columns と同一 ）
        if isinstance(columns, list):
            self.columns = columns

        # 新しい名前に置き換えつつカラム名リストを生成
        new:List[Any] = []
        for col in self.columns:
            if col in columns.keys():
                new.append(columns[col])
            else:
                new.append(col)

        # セットして終了
        self.columns = new
        return 



    # レコード取得（行指向データ）
    def rows(self, type:Literal['list', 'dict']='list', columns:List[str]=None) -> List[Dict[str, Any]] | List[List[str]]:
        """データ参照（行指向データとして）"""

        # データ整形、返却
        if type == 'list':
            # データ整形＆返却
            return self.__records
        else:
            # column 補正: 取得columns未指定のときは全項目
            columns = columns or self.columns
            # column_index 取得
            col_idxs:List[int] = self._Tools.indexes(values=self.columns, search=columns)
            # データ整形＆返却
            return [
                dict(zip(
                    columns,
                    [rec[idx] for idx in col_idxs]
                ))
                for rec in self.__records
            ]


    # レコード取得（列指向データ）
    def cols(self, type:Literal['list', 'dict']='list', columns:List[str]=None) -> Dict[str, List[Any]] | List[List[str]]:
        """データ参照（列指向データとして）"""

        # データ整形、返却
        if type == 'list':
            # データ整形＆返却
            return [
                [ rec[i] for rec in self.__records ]
                for i in range(0, self.column_count)
            ]

        else:
            # column 補正: 取得columns未指定のときは全項目
            columns = columns or self.columns
            # column_index 取得
            col_idxs:List[int] = self._Tools.indexes(values=self.columns, search=columns)
            # データ整形＆返却
            return {
                columns[i]: [ v[c_idx] for v in self.__records ]
                for i, c_idx in enumerate(col_idxs)
            }



    """列データ取得"""
    def __getitem__(self, key:Any) -> List[Any] | None:
        """列データ取得"""

        # カラムが存在しない場合は None
        if key not in self.columns:
            return None

        # 指定カラムのみを抽出して返却
        idx:int = self.columns.index(key)
        return [
            row[idx]
            for row in self.__records
        ]


    """列データ追加/更新"""
    def __setitem__(self, key:str, value:Any):
        """列データ追加/更新"""
    
        # データ型を調整
        key = str(key)

        # リストの場合はレコード数と同数であること。
        is_array:bool = self._Tools.is_array(value)
        if is_array and len(value) != self.row_count:
            raise ValueError("Length of values does not match row-count.")

        # データの数を調整
        values:List[str] = list(value) if is_array else [value] * self.row_count

        # セット（追加/更新判定）
        if key not in self.columns:
            # カラムが存在しない場合は追加
            self.__columns.append(key)
            for i in range(0, self.row_count):
                self.__records[i].append(values[i])
        else:
            # カラムが存在する場合は値を更新
            idx:int = self.columns.index(key)
            for i in range(0, self.row_count):
                self.__records[i][idx] = values[i]

        return


    """フィルタリング"""
    def filter(self, condition:Dict[str, Any]|List[Dict[str, Any]]) -> Self:
        """
        フィルタリング（条件抽出）
        現在の DataTable は変更せず、データ抽出した DataTable を返却する。
        """

        data = [
            d for d in self.rows(type='dict')
            if self._Tools.is_contains(data=d, condition=condition)
        ]
        return DataTable(data=data)


    """テーブル結合"""
    def join(
            self,table:Self,
            how:Literal["inner", "left", "right", "full", "cross"],
            left_on:List[str]=None,
            right_on:List[str]=None,
            left_prefix:str='left_',
            right_prefix:str='right_',
        ) -> Self:
        """
        テーブル結合
        新しい DataTable を返却する。現在の DataTable は更新しない。
        """

        # パラメータチェック
        if how == "cross":
            # CROSS-JOIN: on の利用不可
            if any([left_on, right_on]):
                raise ValueError("The `on` keyword cannot be used in cross-joins.")
        else:
            # その他のJOIN:

            # on は必須
            if not all([left_on, right_on]):
                raise ValueError(f"In an {how}-join, `on` is required.")

            # left_on と right_on の数は一致する必要あり
            if len(left_on) != len(right_on):
                raise ValueError("The number of left_on and right_on do not match.")


        # JOIN方法によって分岐
        columns_l:List[str|int] = self.columns
        columns_r:List[str|int] = table.columns

        if how == 'cross':
            # cross-join: 全ての組み合わせ
            joined_data = [ a + b for a, b in product(self.rows(type='list'), table.rows(type='list')) ]

        else:
            # cross-join 以外:

            # on の カラムINDEX を取得
            idxs_l:List[int] = [ columns_l.index(c_name) for c_name in left_on ]
            idxs_r:List[int] = [ columns_r.index(c_name) for c_name in right_on ]

            # 指定キーでグループ化
            tree_l = self._Tools.grouping_rows(data=self.rows(type='list'), indexes=idxs_l)
            tree_r = self._Tools.grouping_rows(data=table.rows(type='list'), indexes=idxs_r)

            # キーをマージ
            keys_all = set(list(tree_l.keys()) + list(tree_r.keys()))

            # 空データ作成
            empty_l = [[None] * self.column_count]
            empty_r = [[None] * table.column_count]

            # join処理
            joined_data:List[List] = []
            for k in keys_all:
                rows_l = tree_l.get(k, None)
                rows_r = tree_r.get(k, None)

                if (how == 'inner' and all([rows_l, rows_r])) \
                    or (how == 'left' and rows_l) \
                    or (how == 'right'and rows_r) \
                    or (how == 'full'):
                    joined_data.extend(
                        [
                            a + b for a, b in product(
                                rows_l or empty_l,
                                rows_r or empty_r
                            )
                        ]
                    )


        # カラム名を調整
        columns_joined = [ f"{left_prefix}{c}" for c in columns_l] + [ f"{right_prefix}{c}" for c in columns_r]
        return DataTable(data=joined_data, columns=columns_joined)


    """グループ化＆集計"""
    def grouping(self, group_by:List[str]=[], aggregation:Dict[str, str]={}) -> Self:
        """
        グループ化＆集計
        新しい DataTable を返却する。現在の DataTable は更新しない。
        """

        """
        # 集計関数の例
        # [count, max, min, sum, avg] に対応。sum と avg は数値のみ。  
        aggregation = {  
            "new_column_name1": "count(*)",               # 全件数
            "new_column_name1": "count(column_name)",     # None を除いた件数
            "new_column_name2": "max(column_name)",     # 最大値
            ...  
        }
        """

        # パラメータチェック
        if not any([group_by, aggregation]):
            # グループ化項目も集計項目も指定なしの場合は空のテーブルを返却。
            return DataTable(data=None, columns=None)


        #--------------------------------
        #   集計関数をparse
        #--------------------------------
        aggr_regex:re.Pattern = re.compile(r"\s*(.+)\(\s*(.+)\s*\)\s*")
        parsed_aggregations: List[Dict] = []
        for new_name, expr in aggregation.items():

            # 解析＆文法チェック
            if not (m := aggr_regex.fullmatch(expr)):
                raise SyntaxError(f"The aggregate expression is invalid. [{expr}]")

            # 解析情報をまとめ
            aggre_info:Tuple = (new_name, m.group(1).lower(), m.group(2))

            # 入力チェック
            if aggre_info[1] not in ('count', 'max', 'min', 'sum', 'avg'):
                raise SyntaxError(f"Choose an aggregation function from the following options: ('count', 'max', 'min', 'sum', 'avg')")
            if aggre_info[2] not in ("*", *self.columns):
                raise KeyError(f"Column `{aggre_info[2]}` is not found.")
            if aggre_info[2] == "*" and aggre_info[1] != "count":
                raise SyntaxError(f"The '*' character can only be used in `count`.")

            # 解析情報を調整
            key_index:int = -1 if aggre_info[2] == "*" else self.columns.index(aggre_info[2])
            aggre_info = (*aggre_info, key_index)

            # 解析情報をリスト化
            parsed_aggregations.append(aggre_info)

        #--------------------------------
        # グループ化したレコード群を取得
        #--------------------------------
        if len(group_by) == 0:
            grouped_rows = {(): self.__records}
        else:
            grouped_rows = self._Tools.grouping_rows(
                data=self.__records,
                indexes=self._Tools.indexes(values=self.columns, search=group_by)
            )


        #--------------------------------
        # 集計実行
        #--------------------------------

        # 集計関数生成
        funcs = {
            "count" : lambda x: len(x) if x else 0,
            "min"   : lambda x: min(x) if x else None,
            "max"   : lambda x: max(x) if x else None,
            "sum"   : lambda x: sum(x) if x else None,
            "avg"   : lambda x: statistics.mean(x) if x else None,
        }

        # データ初期化
        new_columns: List[str|any] = [*group_by, *[ t[0] for t in parsed_aggregations]]
        new_records: List[List[Any]] = []

        # グループ単位に
        for index_cols, rows in grouped_rows.items():
            # print(f"-- {index_keys}")
            new_row:List[List[Any]] = [*index_cols]
            for name, func_name, key, idx in parsed_aggregations:
                # new_columns.append(name)
                if idx == -1 and func_name == "count":
                    new_row.append(funcs[func_name](rows))
                else:
                    cols = [ r[idx] for r in rows if r[idx] is not None]
                    ret = funcs[func_name](cols)
                    new_row.append(ret)
                    # print(f"  {name} | {idx}:{key} | {func_name}({cols}) -> {ret}")
            new_records.append(new_row)


        #--------------------------------
        # 新しい DataTable オブジェクトを作成して返却
        #--------------------------------
        return DataTable(data=new_records, columns=new_columns)



    """ソート"""
    def sort(self, sort_by:List[str]) -> Self:
        """
        ソート
        現在の DataTable のデータを指定項目の昇順に並び替える。
        """
        col_idxs:List[int] = self._Tools.indexes(values=self.columns, search=sort_by)
        self.__records = sorted(self.__records, key=cmp_to_key(lambda x,y: self._Tools.custom_compare(x, y, keys=col_idxs)))
        return self


    """データ変換"""
    def convert(
            self,
            column :str,
            dtype :str|Type,
            params :str|list|dict = None,
            is_null :Any = None,
            null_if :Any = None,
            errors :Literal['raise', 'coerce', 'ignore'] = 'raise',
            error_data: List[Any] = None
        ) -> List[Any]:
        """
        列データ変換
        """


        def __dtype_converter(value:Any, dtype:Type|str, params:str|List|Dict, is_null:Any, null_if:Any) -> Any:
            """データ変換（１件）"""

            # None 処理
            if value is None:
                return is_null
            if value == null_if:
                return None

            return DataConverter.convert(value=value, dtype=dtype, params=params)


        col:List = self[column]
        if col is None:
            raise KeyError(f"Column '{column}' does not found.")

        ret = []
        ret_error_data = []
        for value in col:
            try:
                # データ変換＆結果を追加
                ret.append(
                    __dtype_converter(
                        value=value, dtype=dtype, params=params,
                        is_null=is_null, null_if=null_if
                    )
                )
                # 変換エラーなし=Noneセット
                ret_error_data.append(None)
            except Exception as e:
                if errors == 'raise':   # 例外
                    raise e
                if errors == 'coerce':  # 強制
                    ret.append(None)
                if errors == 'ignore':  # 無視
                    ret.append(value)
                # エラーデータを保存
                ret_error_data.append(e)

        # パラメータにリストが渡されていたらエラー情報をセット
        if isinstance(error_data, list):
            error_data.clear()
            for err in ret_error_data:
                error_data.append(err)

        # 終了
        return ret





    """list/dictデータの展開(レコード増幅)"""
    def explode(self, key:str, sep:str='_') -> Self:
        """list/dictデータの展開(レコード増幅)"""

        # カラム存在チェック
        if key not in self.columns:
            raise KeyError(key)

        new_keys:List[str] = []
        buf:List = []
        for row in self.rows(type='dict'):
            key_item:Any = row[key]
            if isinstance(key_item, (List, Tuple)):
                # list/tuple の場合は展開してレコード増幅
                if len(key_item) == 0:
                    new_row:Dict[str, Any] = copy.deepcopy(row)
                    new_row[key] = None
                    buf.append(new_row)
                else:
                    for v in key_item:
                        new_row:Dict[str, Any] = copy.deepcopy(row)
                        new_row[key] = v
                        buf.append(new_row)
            elif isinstance(key_item, Dict):
                # dict の場合はカラム増幅
                new_row:Dict[str, Any] = copy.deepcopy(row)
                for k, v in key_item.items():
                    new_key:str = f"{key}{sep}{k}"
                    new_row[new_key] = v
                    if new_key not in new_keys:
                        new_keys.append(new_key)
                new_row[key] = None
                buf.append(new_row)
            else:
                buf.append(row)

        # カラム名並び替え
        key_pos:int = self.columns.index(key)+1
        reorderd_keys:List[str] = (
            list(self.columns[0:key_pos])
            + new_keys
            + list(self.columns[key_pos:])
        )
        # レコードカラム並び替え
        buf = [
            [ row.get(k) for k in reorderd_keys ] 
            for row in buf 
        ]

        return DataTable(data=buf, columns=reorderd_keys)
