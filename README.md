# CodeLearningKit

CodeLearningKit 是一个用于技术学习资料管理的工具集，直接集成了各种开发工具的功能。

## 工具组成

- **Jupyter C++环境工具** (来自 `.jupyter-setup`)
  - 提供Jupyter环境的安装、配置和启动
  - 支持C++内核的配置
  - 提供了浏览器和工作目录的配置功能

- **MD与IPYNB文件同步工具** (来自 `.synctool`)
  - 提供Markdown和Jupyter Notebook文件的双向同步
  - 支持一致性检查
  - 提供自动监控和实时同步功能

## 使用方法

所有功能通过主脚本 `kit.sh` 进行调用，基本用法：

```bash
./kit.sh <工具|命令> [子命令] [选项]
```

### 查看可用工具

```bash
./kit.sh tools    # 显示所有可用工具及其来源
./kit.sh help     # 显示帮助信息
```

### Jupyter工具操作

```bash
./kit.sh jupyter setup                  # 安装和配置C++ Jupyter环境
./kit.sh jupyter lab                    # 启动JupyterLab
./kit.sh jupyter notebook               # 启动Jupyter Notebook
./kit.sh jupyter lab --force-browser    # 启动JupyterLab并强制打开浏览器
./kit.sh jupyter browser                # 配置浏览器设置
./kit.sh jupyter dir                    # 配置工作目录
./kit.sh jupyter help                   # 显示Jupyter工具的帮助信息
```

### 同步工具操作

```bash
./kit.sh sync                     # 启动同步服务
./kit.sh sync --check-only        # 仅检查一致性
./kit.sh sync --sync-once         # 执行一次同步后退出
./kit.sh sync --dry-run           # 模拟运行，不实际修改文件
./kit.sh sync --md-dir=./notes    # 指定Markdown目录
./kit.sh sync help                # 显示同步工具的帮助信息
```

## 目录结构

```
.kit/
├── kit.sh                # 主集成脚本
├── .jupyter-setup/       # Jupyter环境设置工具
│   ├── bin/              # 可执行脚本
│   └── lib/              # 函数库
└── .synctool/            # MD与IPYNB文件同步工具
    └── src/              # 源代码
```

## 特点

- **直观的工具调用**：清晰显示每个工具的来源和可用命令
- **直接转发**：命令直接传递给原始工具，保留完整功能
- **统一接口**：提供一致的命令结构，方便记忆和使用
