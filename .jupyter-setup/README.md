# C++ Jupyter 环境设置工具

这个工具用于在WSL环境中设置和配置C++ Jupyter环境，使您能够在Jupyter中编写和运行C++代码。它提供了简单的命令行界面，让您可以轻松安装、配置和启动C++ Jupyter环境。

## 功能特点

- 一键安装和配置C++ Jupyter环境
- 支持JupyterLab和Jupyter Notebook
- 自动安装Miniconda（如果尚未安装）
- 创建独立的conda环境用于C++ Jupyter
- 智能检测并配置Windows浏览器
- 自定义工作目录支持
- 命令行参数支持（端口、浏览器强制打开、工作目录等）
- 端口冲突检测和处理
- 详细的日志输出和错误处理

## 快速开始

### 安装和配置

```bash
# 切换到项目根目录
cd /path/to/Project

# 运行安装命令
.jupyter-setup/bin/jupyter-cpp setup
```

安装过程会引导您完成以下配置：
- Jupyter监听端口和IP
- 是否设置密码保护
- 选择工作目录
- 选择浏览器设置

### 启动JupyterLab

```bash
.jupyter-setup/bin/jupyter-cpp lab
```

### 启动Jupyter Notebook

```bash
.jupyter-setup/bin/jupyter-cpp notebook
```

## 命令和参数

### 主要命令

| 命令       | 描述                      |
| ---------- | ------------------------- |
| `setup`    | 安装和配置C++ Jupyter环境 |
| `lab`      | 启动JupyterLab            |
| `notebook` | 启动Jupyter Notebook      |
| `browser`  | 配置浏览器设置            |
| `dir`      | 配置工作目录              |
| `help`     | 显示帮助信息              |

### 可选参数

| 参数              | 描述                       |
| ----------------- | -------------------------- |
| `--port=XXXX`     | 指定端口号（默认8888）     |
| `--bg`            | 后台运行Jupyter服务        |
| `--force-browser` | 强制打开浏览器（忽略配置） |
| `--dir=PATH`      | 指定工作目录（覆盖配置）   |
| `--help`          | 显示帮助信息               |

## 使用示例

```bash
# 安装和配置
.jupyter-setup/bin/jupyter-cpp setup

# 启动JupyterLab（使用默认配置）
.jupyter-setup/bin/jupyter-cpp lab

# 启动Notebook并指定端口
.jupyter-setup/bin/jupyter-cpp notebook --port=9999

# 在特定目录启动JupyterLab并强制打开浏览器
.jupyter-setup/bin/jupyter-cpp lab --dir=/path/to/project --force-browser

# 更新浏览器配置
.jupyter-setup/bin/jupyter-cpp browser

# 更新工作目录配置
.jupyter-setup/bin/jupyter-cpp dir
```

## 自定义配置

### 浏览器配置

您可以随时更新浏览器配置：

```bash
.jupyter-setup/bin/jupyter-cpp browser
```

系统会检测可用的Windows浏览器，并允许您选择是否自动打开浏览器以及使用哪个浏览器。

### 工作目录配置

您可以设置Jupyter启动时的默认工作目录：

```bash
.jupyter-setup/bin/jupyter-cpp dir
```

可选择：
- 项目根目录
- 用户主目录
- 自定义目录

也可以在启动时临时指定目录：

```bash
.jupyter-setup/bin/jupyter-cpp lab --dir=/path/to/your/project
```

## 常见问题

### 1. Jupyter访问出现502错误

- 确保使用`localhost`或`127.0.0.1`而不是`0.0.0.0`访问
- 检查防火墙设置是否阻止了连接

### 2. 密码认证问题

- 首次使用token登录，然后设置密码
- 如果忘记密码，可以查看Jupyter服务日志获取token

### 3. 浏览器无法自动打开

- 检查浏览器路径配置是否正确
- 使用`--force-browser`参数强制打开浏览器
- 手动复制终端中的URL在浏览器中打开

### 4. C++内核未显示或无法使用

- 确认xeus-cling已正确安装：
  ```bash
  conda activate cpp
  conda install -c conda-forge xeus-cling
  ```
- 重新运行setup命令：
  ```bash
  .jupyter-setup/bin/jupyter-cpp setup
  ```

### 5. 端口冲突问题

- 使用`--port`选项指定其他端口
- 或使用工具提供的选项终止占用端口的进程

## 目录结构

```
.jupyter-setup/
├── bin/                 # 可执行脚本目录
│   └── jupyter-cpp      # 主命令行工具
├── lib/                 # 库函数目录
│   ├── common.sh        # 通用函数库
│   ├── jupyter_setup.sh # 环境设置模块
│   ├── jupyter_run.sh   # 运行管理模块
│   └── browser_config.sh# 浏览器配置模块
├── config/              # 配置文件目录
│   ├── jupyter_notebook_config.py # Jupyter配置
│   ├── browser_config.sh          # 浏览器配置
│   └── jupyter_dir_config.sh      # 工作目录配置
└── README.md           # 本文档
```

## 技术细节

- 基于xeus-cling提供C++ Jupyter内核
- 支持C++11、C++14和C++17标准
- 通过conda环境隔离依赖
- 专为WSL环境优化，解决Windows/Linux交互问题
- 智能浏览器检测，支持主流Windows浏览器

## 许可证

MIT 