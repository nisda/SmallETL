# SmallETL


```bash
python ./workflow/sample_01.json --log-level DEBUG
```

## 開発メモ

### パラメータ


### ループ制御


#### graph の書き方
{
	"name": "loop-A"
	"flow": "loop":				# job との並存は不可とする
	"items": "get_holidays",	# これの要素でループする
	"graph" : [
		{
			...
		}
	]
}

### 内部データの持ち方
loop-A[0].

⇒これ、あとのjobで参照できる？
	⇒ループの後の参照って難しいな。
	たぶんデータを分解する flow.mapping が必要



### ログの出し方
01-01_loop-A



