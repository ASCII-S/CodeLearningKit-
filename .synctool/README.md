# MDSync

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Contributions Welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](https://github.com/yourusername/mdsync/issues)
[![Language: 中文](https://img.shields.io/badge/语言-中文-red.svg)](README.md)

> 一个强大的双向同步工具，用于在Markdown文件和Jupyter Notebook之间保持无缝同步

## 💡 解决的问题

**当前的痛点：**

- **Markdown**：结构清晰、易于展示和阅读，但在代码学习中无法得到即时的执行反馈
- **Jupyter Notebook**：可边笔记边执行代码，但格式臃肿，不利于知识展示和建立笔记间的关联
- **学习效率低**：在两种格式间切换和复制内容浪费大量时间

**MDSync提供的解决方案：**

- 🔄 **实时双向同步**：在Markdown和Jupyter之间保持无缝同步
- 💻 **利用编辑器优势**：通过Cursor打开ipynb文件，更快速地制作精准的代码学习笔记
- 🚀 **提升学习效率**：在熟悉的环境中专注内容创作，而非格式转换

MDSync实现了Markdown文件夹和Jupyter Notebook文件夹之间的双向同步功能。它允许用户在Markdown中编辑笔记，并在Jupyter Notebook中运行其中的代码部分；同时在Jupyter Notebook中的编辑也会同步到Markdown中。这是一个理想的工具，用于在文档编辑和代码执行之间无缝切换。

<div align="center">
  <h4>Markdown 文件与 Jupyter Notebook 双向实时同步</h4>
  <pre>
  ┌────────────────┐                      ┌────────────────┐
  │                │                      │                │
  │    Markdown    │◄─────同步更新─────►   │  Jupyter       │
  │    文件夹       │                      │  Notebook      │
  │                │                      │                │
  └────────────────┘                      └────────────────┘
  </pre>
</div>

## ✨ 特点

- **双向实时同步** - 在Markdown和Jupyter Notebook之间保持实时、双向的内容同步
- **智能代码语言检测** - 自动识别和处理不同编程语言的代码块
- **文件一致性检查** - 自动检测和处理文件结构差异
- **时间戳同步机制** - 保持源文件和目标文件的时间戳一致，避免重复同步
- **高度可配置** - 通过JSON配置文件自定义各种同步行为和策略
- **WSL环境支持** - 特别优化了在Windows Subsystem for Linux中的性能

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/mdsync.git
cd mdsync

# 安装依赖
pip install watchdog
```

### 基本使用

1. 配置同步目录（编辑`.synctool/config.json`）：

```json
{
  "md_dir": "/path/to/markdown/files",
  "ipynb_dir": "/path/to/jupyter/notebooks"
}
```

2. 运行同步工具：

```bash
python synctool.py
```

## 📚 详细文档

### 命令行选项

```
用法: synctool.py [选项]

选项:
  --config, -c PATH       指定配置文件路径
  --md-dir PATH           指定Markdown文件目录
  --ipynb-dir PATH        指定Jupyter Notebook文件目录
  --check-only            仅检查一致性，不进行同步
  --sync-once             执行一次同步后退出
  --dry-run               模拟运行，不实际修改文件
  --verbose, -v           显示详细日志
  --debug, -d             显示调试日志
  --quiet, -q             只显示错误和警告日志
```

### 配置文件详解

MDSync使用JSON格式的配置文件来控制其行为。默认配置文件位于`.synctool/config.json`。

| 配置项                | 类型    | 默认值                     | 描述                                   |
| --------------------- | ------- | -------------------------- | -------------------------------------- |
| `md_dir`              | string  | "./mdtest"                 | Markdown文件目录                       |
| `ipynb_dir`           | string  | "./ipynbtest"              | Jupyter Notebook文件目录               |
| `ignore_patterns`     | array   | [".*", "__pycache__", ...] | 要忽略的文件/目录模式                  |
| `debounce_delay`      | float   | 0.8                        | 事件去抖动延迟（秒）                   |
| `watch_interval`      | float   | 1.0                        | 文件监控间隔（秒）                     |
| `sync_on_start`       | boolean | true                       | 启动时是否执行同步                     |
| `check_on_start`      | boolean | true                       | 启动时是否执行一致性检查               |
| `bidirectional_sync`  | boolean | true                       | 是否双向同步                           |
| `conflict_resolution` | string  | "newer"                    | 冲突解决策略（"newer", "md", "ipynb"） |
| `delete_orphaned`     | boolean | true                       | 是否删除孤立文件                       |
| `default_language`    | string  | "python"                   | 默认代码块语言                         |
| `preserve_output`     | boolean | true                       | 是否保留输出结果                       |
| `time_threshold`      | integer | 5                          | 时间戳比较阈值（秒）                   |

## 📝 工作原理

MDSync的工作流程如下：

1. 扫描配置的两个目录并检查文件一致性
2. 根据配置的同步策略，执行初始同步
3. 启动文件监控，实时监测文件变化
4. 当检测到文件变化时，自动触发同步操作

## 🔧 高级使用

### WSL环境优化

在Windows Subsystem for Linux (WSL) 环境下，标准的文件系统监控有时无法正确检测到`.ipynb`文件的变化。MDSync采用了双重监控策略：

- 对于Markdown文件夹：使用标准的Observer监控
- 对于Jupyter Notebook文件夹：使用轮询式的PollingObserver监控

如果文件变更未被检测到，可以尝试：

1. 使用`--debug`参数运行，查看详细日志
2. 增加配置文件中的`poll_interval`值，调整轮询间隔

### 特殊文件处理

MDSync对特殊文件有专门处理：

- **空文件**：创建对应的空目标文件
- **格式错误的IPYNB文件**：创建包含错误信息的MD文件
- **不同语言的代码块**：正确保留代码块语言信息

## 💡 常见问题

<details>
<summary><b>循环同步问题</b></summary>
如果每次启动都触发同步，即使文件没有实际变化，请检查：

1. 确保`time_threshold`配置适当（默认5秒）
2. 设置`check_on_start: false`避免启动时自动同步
3. 查看是否有外部程序正在修改这些文件
</details>

<details>
<summary><b>文件变更未检测到</b></summary>
可能原因：

1. 文件系统特性或操作系统兼容性问题
2. 监控间隔设置过长
3. 文件被忽略模式匹配

解决方案：
- 调整`watch_interval`和`poll_interval`值
- 使用`--debug`模式查看详细日志
</details>

<details>
<summary><b>配置文件问题</b></summary>
如果配置不生效：

1. 检查JSON格式是否正确
2. 确保路径使用正确的分隔符（Windows上使用`\\`或`/`）
3. 尝试使用绝对路径
</details>

## 👥 贡献

欢迎贡献！请随时提交问题或拉取请求。对于重大更改，请先打开一个issue讨论您想要更改的内容。

贡献步骤：
1. Fork该仓库
2. 创建您的功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个Pull Request

## 📄 许可证

本项目采用MIT许可证 - 详情参见[LICENSE](LICENSE)文件。

## 📬 联系方式

项目维护者 - [@yourusername](https://github.com/yourusername)

项目链接：[https://github.com/yourusername/mdsync](https://github.com/yourusername/mdsync) 