{
	"name": "sample-001",
	"dump_dir" : "{var.work_dir}/dump/{wf.name}/",
	"max_workers": 5,
	"graph": [
		{
			"name": "find_excel",
			"job": "file.find",
			"parameters" : {
				"path" : "{var.work_dir}/input/*.xlsx"
			}
		},
		{
			"name": "aaa.loop"
			"items" : 
		}
	]
}