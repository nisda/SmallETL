# SmallETL


```bash
※未実装
python ./workflow/sample_01.json --log-level DEBUG
```

## workflow 定義

| キー | データ型 | 使用可能な変数 |
| -- | -- |-- |
| name | str | - |
| description | str | - |
| secret | dict | `var` `env` |
| const | dict | `var` `env` `wf` `secret` |
| dump_dir | str | `var` `env` `wf` `secret` `const` |
| graph | list | `var` `env` `wf` `secret` `const` `output`  |
| graph<BR> (inside each) | list | `var` `env`  `wf` `secret` `const` `output` `each` `each.parent`  |

### 変数

#### var
| 変数 | 備考 |
| -- | -- |
| `{var.xxx}` | `workflow.run` 実行時にパラメータ `var` で指定した値。 |


#### secret
| 変数 | 備考 |
| -- | -- |
| `{secret.xxx}` | workflow 定義の "secret" で設定した値。 |

#### wf
| 変数 | 備考 |
| -- | -- |
| `{wf.name}` | workflow 定義の "name" で設定した値。 |
| `{wf.run_id}` | workflow 実行ID（8桁の英数字） |
| `{wf.start_time}` | workflow 実行開始時日時。 |

#### const

| 変数 | 備考 |
| -- | -- |
| `{const.xxx}` | workflow 定義の "const" で設定した値。 |

#### output

| 変数 | 備考 |
| -- | -- |
| `{output.xxx}` | 実行済みjobの出力結果。 |

#### each

`"flow": "each"` 内の繰り返し要素。

| 変数 | 備考 |
| -- | -- |
| `{each.index}` | 繰り返し要素の連番 |
| `{each.key}`   | 繰り返し要素のキー（listのときはindexと同値） |
| `{each.value}` | 繰り返し要素の値 |

#### each.parent

ネストされた `each` で親階層の繰り返し要素を参照する変数。  
多段ネストの場合は、 `each.parent.parent...` と `.parent` を続けることで参照可能。

| 変数 | 備考 |
| -- | -- |
| `{each.parent.index}` | 親階層の繰り返し要素の連番 |
| `{each.parent.key}`   | 親階層の繰り返し要素のキー（Dictの場合のみ） |
| `{each.parent.value}` | 親階層の繰り返し要素の値 |




# 開発メモ


### 構成要素（用語の定義）

```
workflow
  └ graph
    └ job
    └ each ... List|Dict データの繰り返し処理
      └ graph
        └ ...
```

| class		| 基底			| output
| --		| --			|
| workflow	| -				|
| graph		| -				|
| ComponentBase
|   job		| ComponentBase	| 
|   each		| ComponentBase	|

graph				status 
ComponentBase		output を保存する。
	job				output を↑に戻す
	each			output を↑に戻す。
						中止をどうやって上に渡すか？ ⇒ componentBase にメソッド用意する？
						フロー制御の場合は戻り値を dict にして status と output をまとめて dict にして渡す？
						本来は FlowCompornent とか継承クラスを挟んだほうがいいんだろうけど、そこまでは面倒。

graph も Component を継承できないか？
	⇒ Condition とか無いのでNG。

#### each の書き方
{
	"name": "loop-A"
	"flow": "each":						# job との並存は不可とする
	"items": "{output.job_name_01}",	# これの要素でループする
	"graph" : [
		{
			...
		}
	]
}



## 課題

* 終了コード
	const の ExitCode と
	ComponentBase の ComponentStatus に分かれてしまっている。
		⇒これじゃ別でいい。
	途中の Stopped 等を Workflow.run でキャッチできていない。正常終了扱いになっている。
		⇒これは対応すべき。



* フロー制御で条件分岐したい。
	if ではなく switch があれば足りそう。
	```json
	{
		"flow" : "switch",
		"case" : {
			"<条件文1>" : {},
			"<条件文2>" : {},
		},
		"else" : {	//default のほうが一般的か。
			...
		}
	}
	```

* ジョブ結果をキャッシュする仕組みを用意したい。
	更新頻度が低いマスタデータ取得などの用途で。
	カスタムジョブへの反映を考慮して、ジョブ個別で実装するのではなくデコレータなどで用意したい。

