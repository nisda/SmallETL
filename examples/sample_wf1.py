# coding: utf-8

import sys
import os
import logging
import argparse 
from typing import Dict, List, Any
import json


# src フォルダをインポート（上位フォルダ経由のため必要）
SCRIPT_DIR = os.path.dirname(__file__)
sys.path.append(os.path.join(SCRIPT_DIR, '../src/'))
from SmallETL import WorkFlow


# 設定
DEFAULT_LOG_LEVEL :str = "DEBUG"
WORK_DIR :str = os.path.join(SCRIPT_DIR, '_sample')



if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('workflow_path', type=str, help='Workflow-FilePath (absolute or relative)')
    parser.add_argument('--log-level', type=str, default=DEFAULT_LOG_LEVEL,
                    help='Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    # parser.set_defaults(func=main)

    # args 解析
    args = parser.parse_args()

    # ルートロガーの設定
    logging.basicConfig(
        filename=None,
        level=logging.getLevelName(str(args.log_level).upper()),
        # format="[%(levelname)s] %(name)s:%(message)s",
        # style='{', format='{asctime} [{levelname:.4}] {name}: {message}',   # styleで書式変更できる
        style='{', format='{asctime} [{levelname:.3}] {name} | {message}',   # styleで書式変更できる
        )

    # ロガー取得
    logger = logging.getLogger(__name__)

    # ワークフロー実行
    wf:WorkFlow = WorkFlow(filepath=args.workflow_path, encoding="utf-8")
    ret = wf.run(var={"work_dir": WORK_DIR})

    # 終了
    sys.exit(0)

