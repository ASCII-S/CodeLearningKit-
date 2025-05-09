#!/bin/bash
# Jupyter启动模块

# 加载共享函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# 启动Jupyter函数
start_jupyter() {
    local mode=${1:-"lab"}  # 默认为lab模式
    local port=${2:-8888}   # 默认端口8888
    
    log_info "==== 启动Jupyter $mode ===="
    
    # 查找conda路径
    find_conda
    
    # 检查端口是否被占用
    local port_status
    while check_port "$port"; do
        # 获取占用端口的进程信息
        local pid=$(lsof -i :"$port" -t 2>/dev/null | head -n1)
        
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
                continue
            else
                break
            fi
        elif [ "$CHOICE" = "2" ]; then
            port=$((port+1))
            log_info "切换到端口 $port..."
            continue
        else
            log_error "已取消启动。"
            return 1
        fi
    done
    
    # 设置conda环境变量
    if [ -d "$CONDA_DIR" ]; then
        log_info "设置conda环境变量"
        export PATH="$CONDA_DIR/bin:$CONDA_DIR/condabin:$PATH"
    fi
    
    # 激活conda环境
    activate_conda_env "cpp" || return 1
    
    # 检查C++内核是否可用
    if ! jupyter kernelspec list 2>/dev/null | grep -q "xcpp"; then
        log_warning "未检测到C++内核，这可能会导致无法在Jupyter中使用C++"
        log_info "请确保xeus-cling已正确安装，可以尝试重新运行setup命令"
    else
        log_info "检测到C++内核可用"
    fi
    
    # 检查配置文件是否存在
    if ! file_exists "$JUPYTER_CONFIG"; then
        log_warning "找不到Jupyter配置文件 $JUPYTER_CONFIG"
        log_info "创建默认配置..."
        
        # 创建配置目录
        mkdir -p "$CONFIG_DIR"
        
        # 创建默认配置
        cat > "$JUPYTER_CONFIG" << EOF
c = get_config()
c.ServerApp.ip = '127.0.0.1'
c.ServerApp.port = $port
c.ServerApp.disable_check_xsrf = True
EOF
    fi
    
    # 加载浏览器配置
    if file_exists "$BROWSER_CONFIG"; then
        source "$BROWSER_CONFIG"
        log_info "已加载浏览器配置: AUTO_OPEN_BROWSER=$AUTO_OPEN_BROWSER"
    else
        log_warning "找不到浏览器配置文件，将使用默认设置"
        AUTO_OPEN_BROWSER=true  # 默认启用自动打开
    fi
    
    # 检查是否强制打开浏览器
    if [ "$FORCE_BROWSER" = true ]; then
        log_info "启用强制打开浏览器模式"
        AUTO_OPEN_BROWSER=true
    fi
    
    # 确定工作目录
    local working_dir="$PROJECT_ROOT"
    
    # 优先使用命令行指定的目录
    if [ -n "$JUPYTER_CUSTOM_DIR" ]; then
        if [ -d "$JUPYTER_CUSTOM_DIR" ]; then
            working_dir="$JUPYTER_CUSTOM_DIR"
            log_info "使用命令行指定的工作目录: $working_dir"
        else
            log_warning "命令行指定的目录不存在: $JUPYTER_CUSTOM_DIR"
        fi
    # 其次尝试加载配置文件中的目录
    elif file_exists "$JUPYTER_DIR_CONFIG"; then
        source "$JUPYTER_DIR_CONFIG"
        if [ -n "$JUPYTER_WORKING_DIR" ] && [ -d "$JUPYTER_WORKING_DIR" ]; then
            working_dir="$JUPYTER_WORKING_DIR"
            log_info "使用配置的工作目录: $working_dir"
        fi
    fi
    
    # 切换到工作目录
    log_info "切换到工作目录: $working_dir"
    cd "$working_dir" || {
        log_warning "无法切换到指定工作目录，尝试切换到项目根目录"
        cd "$PROJECT_ROOT" || {
            log_warning "无法切换到项目根目录，将在当前目录启动"
        }
    }
    
    # 显示当前工作目录
    log_info "当前工作目录: $(pwd)"
    
    # 构建Jupyter命令和URL
    local jupyter_cmd
    local url="http://localhost:$port"
    
    if [ "$mode" = "notebook" ]; then
        jupyter_cmd="jupyter notebook"
    else
        jupyter_cmd="jupyter lab"
        url="${url}/lab"
    fi
    
    log_info "=========================="
    log_info "Jupyter URL: $url"
    log_info "=========================="
    
    # 启动Jupyter
    if [ "$AUTO_OPEN_BROWSER" = true ]; then
        # 后台启动服务器
        log_info "后台启动Jupyter，并将打开浏览器..."
        eval "$jupyter_cmd --no-browser --port=$port --ServerApp.ip=127.0.0.1 --config='$JUPYTER_CONFIG'" &
        local server_pid=$!
        
        # 等待服务器启动
        log_info "等待Jupyter服务器启动..."
        sleep 3
        
        # 尝试获取带token的URL
        local token_url=$(jupyter $mode list | grep -m 1 -o 'http://[^?]*\?token=[a-zA-Z0-9]*' || echo "")
        if [ -n "$token_url" ]; then
            # 替换URL中的主机名为localhost
            token_url=$(echo "$token_url" | sed 's|http://[^/]*|http://localhost:'"$port"'|')
            log_info "找到带token的URL: $token_url"
            url="$token_url"
        fi
        
        # 打开浏览器
        open_browser "$url"
        
        # 等待服务器进程结束
        wait $server_pid || true
    else
        # 前台运行
        log_info "前台启动Jupyter (不自动打开浏览器)..."
        eval "$jupyter_cmd --no-browser --port=$port --ServerApp.ip=127.0.0.1 --config='$JUPYTER_CONFIG'"
    fi
    
    log_info "Jupyter服务器已终止"
    
    return 0
}

# 启动Jupyter Notebook
start_notebook() {
    local port=${1:-8888}
    start_jupyter "notebook" "$port"
    return $?
}

# 启动JupyterLab
start_lab() {
    local port=${1:-8888}
    start_jupyter "lab" "$port"
    return $?
} 