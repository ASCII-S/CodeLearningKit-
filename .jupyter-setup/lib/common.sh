#!/bin/bash
# 共享函数库 - 包含所有脚本共用的函数

# 颜色和格式
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# 脚本目录
SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIB_DIR="$SCRIPT_ROOT/lib"
CONFIG_DIR="$SCRIPT_ROOT/config"
BIN_DIR="$SCRIPT_ROOT/bin"

# 配置文件路径
JUPYTER_CONFIG="$CONFIG_DIR/jupyter_notebook_config.py"
BROWSER_CONFIG="$CONFIG_DIR/browser_config.sh"
JUPYTER_DIR_CONFIG="$CONFIG_DIR/jupyter_dir_config.sh"

# 默认工作目录
PROJECT_ROOT="$(dirname $(dirname "$SCRIPT_ROOT"))"

# 日志函数
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1" >&2
}

log_error() {
    log "${RED}[ERROR]${NC} $1" >&2
}

# 检查命令是否存在
command_exists() {
    command -v "$1" &> /dev/null
}

# 检查文件是否存在
file_exists() {
    [ -f "$1" ]
}

# 检查目录是否存在
dir_exists() {
    [ -d "$1" ]
}

# 查找conda路径并初始化环境变量
find_conda() {
    if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
        CONDA_SH_PATH=~/miniconda3/etc/profile.d/conda.sh
        CONDA_DIR=~/miniconda3
    elif [ -f ~/anaconda3/etc/profile.d/conda.sh ]; then
        CONDA_SH_PATH=~/anaconda3/etc/profile.d/conda.sh
        CONDA_DIR=~/anaconda3
    else
        # 尝试动态查找
        CONDA_BASE=$(conda info --base 2>/dev/null || echo "$HOME/miniconda3")
        CONDA_SH_PATH="$CONDA_BASE/etc/profile.d/conda.sh"
        CONDA_DIR=$CONDA_BASE
    fi
    
    # 导出变量以供其他脚本使用
    export CONDA_SH_PATH
    export CONDA_DIR
}

# 激活conda环境
activate_conda_env() {
    local env_name="$1"
    
    if [ -f "$CONDA_SH_PATH" ]; then
        source "$CONDA_SH_PATH"
        conda activate "$env_name" || log_error "无法激活环境 $env_name"
        return $?
    else
        log_error "找不到conda.sh，请确保Conda已正确安装"
        return 1
    fi
}

# 检查并安装包
check_and_install_package() {
    local package="$1"
    local channel="$2"
    
    log_info "🔍 检查 $package 是否已安装..."
    if conda list | grep -q "^$package[[:space:]]"; then
        log_success "✅ $package 已通过conda安装"
        return 0
    fi
    
    if python -c "import $package" &>/dev/null; then
        log_success "✅ $package 已通过pip安装"
        return 0
    fi
    
    log_info "📦 安装 $package..."
    if [ -z "$channel" ]; then
        conda install -y "$package" || pip install "$package"
    else
        conda install -y -c "$channel" "$package" || pip install "$package"
    fi
    
    return $?
}

# 检查端口是否被占用
check_port() {
    local port="$1"
    local pid=$(lsof -i :"$port" -t 2>/dev/null | head -n1)
    
    if [ -n "$pid" ]; then
        return 0 # 端口被占用
    else
        return 1 # 端口未被占用
    fi
}

# 处理端口占用
handle_port_conflict() {
    local port="$1"
    local pid=$(lsof -i :"$port" -t 2>/dev/null | head -n1)
    
    if [ -n "$pid" ]; then
        log_warning "端口 $port 已被占用！"
        echo "占用进程信息："
        lsof -i :"$port"
        echo
        echo "请选择操作："
        echo "  1) 杀死占用进程 ($pid)"
        echo "  2) 自动切换到下一个端口"
        echo "  3) 取消启动"
        read -p "请输入选项 [1/2/3]: " CHOICE
        
        if [ "$CHOICE" = "1" ]; then
            kill -9 "$pid"
            log_info "已杀死进程 $pid，重试..."
            sleep 1
            # 再次检查端口
            if check_port "$port"; then
                log_error "端口 $port 仍被占用，请尝试其他选项"
                return 1
            else
                return 0
            fi
        elif [ "$CHOICE" = "2" ]; then
            local new_port=$((port+1))
            log_info "切换到端口 $new_port..."
            echo "$new_port"
            return 2
        else
            log_info "已取消启动。"
            return 1
        fi
    fi
    
    return 0 # 端口未被占用
}

# 运行Jupyter
run_jupyter() {
    local mode=$1  # notebook 或 lab
    local port=$2
    local bg=$3    # true表示后台运行
    
    if [ "$mode" = "notebook" ]; then
        cmd="jupyter notebook"
    else
        cmd="jupyter lab"
    fi
    
    if [ "$bg" = "true" ]; then
        $cmd --no-browser --port="$port" --ServerApp.ip=127.0.0.1 --config="$JUPYTER_CONFIG" &
        echo $!  # 返回进程ID
    else
        $cmd --port="$port" --ServerApp.ip=127.0.0.1 --config="$JUPYTER_CONFIG"
    fi
}

# 构建Jupyter URL
build_jupyter_url() {
    local mode=$1  # notebook 或 lab
    local port=$2
    
    # 检查是否设置了密码
    if grep -q "c.ServerApp.password" "$JUPYTER_CONFIG" 2>/dev/null; then
        # 有密码，使用localhost
        if [ "$mode" = "notebook" ]; then
            echo "http://localhost:$port"
        else
            echo "http://localhost:$port/lab"
        fi
    else
        # 无密码，尝试获取带token的URL
        local list_cmd="jupyter $mode list"
        local server_url=$($list_cmd 2>/dev/null | grep -m 1 -o 'http://[^ ]*' || echo "")
        
        if [ -n "$server_url" ]; then
            # 提取token
            local token=$(echo "$server_url" | grep -o 'token=[a-zA-Z0-9]*' || echo "")
            
            if [ -n "$token" ]; then
                if [ "$mode" = "notebook" ]; then
                    echo "http://localhost:$port/?$token"
                else
                    echo "http://localhost:$port/lab?$token"
                fi
            else
                if [ "$mode" = "notebook" ]; then
                    echo "http://localhost:$port"
                else
                    echo "http://localhost:$port/lab"
                fi
            fi
        else
            # 使用基本URL
            if [ "$mode" = "notebook" ]; then
                echo "http://localhost:$port"
            else
                echo "http://localhost:$port/lab"
            fi
        fi
    fi
}

# 打开浏览器
open_browser() {
    local url="$1"
    
    log_info "尝试打开浏览器，URL: $url"
    
    # 加载浏览器配置
    if file_exists "$BROWSER_CONFIG"; then
        source "$BROWSER_CONFIG"
        log_info "已加载浏览器配置文件: $BROWSER_CONFIG"
        log_info "AUTO_OPEN_BROWSER=$AUTO_OPEN_BROWSER, BROWSER=$BROWSER"
        
        if [ "$AUTO_OPEN_BROWSER" = true ] && [ -f "$BROWSER" ]; then
            log_info "使用配置的浏览器打开: $BROWSER"
            "$BROWSER" "$url" >/dev/null 2>&1 &
            return $?
        fi
    else
        log_warning "未找到浏览器配置文件: $BROWSER_CONFIG"
    fi
    
    # 尝试通用浏览器路径
    local CHROME_PATH="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
    local EDGE_PATH="/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
    local FIREFOX_PATH="/mnt/c/Program Files/Mozilla Firefox/firefox.exe"
    
    if [ -f "$CHROME_PATH" ]; then
        log_info "尝试使用Chrome打开URL"
        "$CHROME_PATH" "$url" >/dev/null 2>&1 &
        return 0
    elif [ -f "$EDGE_PATH" ]; then
        log_info "尝试使用Edge打开URL"
        "$EDGE_PATH" "$url" >/dev/null 2>&1 &
        return 0
    elif [ -f "$FIREFOX_PATH" ]; then
        log_info "尝试使用Firefox打开URL"
        "$FIREFOX_PATH" "$url" >/dev/null 2>&1 &
        return 0
    fi
    
    log_warning "无法自动打开浏览器，请手动访问: $url"
    log_info "您可以使用以下命令手动打开: \"/mnt/c/Program Files/Google/Chrome/Application/chrome.exe\" \"$url\""
    return 1
}

# 显示帮助信息
show_help() {
    echo "Jupyter C++环境工具 - 帮助信息"
    echo "用法: jupyter-cpp [命令] [参数]"
    echo
    echo "可用命令:"
    echo "  setup       设置C++ Jupyter环境"
    echo "  notebook    启动Jupyter Notebook"
    echo "  lab         启动JupyterLab (默认)"
    echo "  browser     配置浏览器设置"
    echo "  help        显示此帮助信息"
    echo
    echo "选项:"
    echo "  --port=XXXX       指定端口号 (默认: 8888)"
    echo "  --bg              在后台运行"
    echo "  --force-browser   强制打开浏览器(忽略配置)"
    echo
    echo "示例:"
    echo "  jupyter-cpp setup                  # 安装和配置C++ Jupyter环境"
    echo "  jupyter-cpp lab                    # 启动JupyterLab"
    echo "  jupyter-cpp notebook               # 启动Jupyter Notebook"
    echo "  jupyter-cpp lab --force-browser    # 启动JupyterLab并强制打开浏览器"
    echo "  jupyter-cpp browser                # 配置浏览器设置"
    echo
} 