#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MDSync - 一个Markdown和Jupyter Notebook文件之间的双向同步工具

该工具允许用户在Markdown中编辑笔记，并在Jupyter Notebook中运行其中的代码部分；
同时在Jupyter Notebook中的编辑也会同步到Markdown中。
"""

import sys
from pathlib import Path

# 添加当前目录到Python路径，以便导入模块
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.append(str(SCRIPT_DIR))

# 导入主程序
from src.main import main

if __name__ == "__main__":
    main() 