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
| const | dict | `var` `wf` |
| dump_dir | str | `var` `wf` `const` |
| graph | list | `var` `wf` `const` `payload`  |
| graph<BR> (inside each) | list | `var` `wf` `const` `payload` `each` `each.parent`  |

### 変数

#### var
| 変数 | 備考 |
| -- | -- |
| `{var.xxx}` | `workflow.run` 実行時にパラメータ `var` で指定する。 |

#### wf
| 変数 | 備考 |
| -- | -- |
| `{wf.name}` | workflow.name で設定した workflow 名 |
| `{wf.run_id}` | workflow 実行ID（8桁の英数字） |
| `{wf.start_time}` | workflow 実行開始時日時。 |

#### const

| 変数 | 備考 |
| -- | -- |
| `{const.xxx}` | workflow.const で設定した定数。 |

#### payload

| 変数 | 備考 |
| -- | -- |
| `{payload.xxx}` | 実行済みjobの出力結果。 |

#### each

| 変数 | 備考 |
| -- | -- |
| `{each.index}` | 繰り返し要素の連番 |
| `{each.key}`   | 繰り返し要素のキー（Dictの場合のみ） |
| `{each.value}` | 繰り返し要素の値 |

#### each.parent

ネストされた `each` で親階層の繰り返し要素を参照する変数。  
多段ネストの場合は、 `each.parent.parent...` と `.parent` を続けることで参照可能。

| 変数 | 備考 |
| -- | -- |
| `{each.parent.index}` | 親階層の繰り返し要素の連番 |
| `{each.parent.key}`   | 親階層の繰り返し要素のキー（Dictの場合のみ） |
| `{each.parent.value}` | 親階層の繰り返し要素の値 |




## 開発メモ


### 構成要素（用語の定義）

```
workflow
  └ graph
    └ job
    └ each ... List|Dict データの繰り返し処理
      └ graph
        └ ...
```



#### each の書き方
{
	"name": "loop-A"
	"flow": "each":						# job との並存は不可とする
	"items": "{payload.job_name_01}",	# これの要素でループする
	"graph" : [
		{
			...
		}
	]
}


