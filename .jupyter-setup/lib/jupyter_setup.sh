#!/bin/bash
# Jupyter设置模块

# 加载共享函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
source "$SCRIPT_DIR/lib/browser_config.sh"

# 安装Miniconda
install_miniconda() {
    if command_exists conda; then
        log_success "已检测到conda安装，跳过Miniconda安装"
        return 0
    fi
    
    log_info "未找到conda命令，正在安装Miniconda..."
    
    # 安装Miniconda
    log_info "==== 安装Miniconda ===="
    mkdir -p ~/miniconda3
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
    bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
    rm ~/miniconda3/miniconda.sh
    
    # 初始化conda
    log_info "==== 初始化conda ===="
    ~/miniconda3/bin/conda init bash
    
    # 刷新环境变量以获取conda命令
    source ~/.bashrc
    
    log_success "Miniconda安装完成"
    return 0
}

# 初始化conda环境
setup_conda_env() {
    # 寻找conda路径
    find_conda
    
    log_info "Conda脚本路径: $CONDA_SH_PATH"
    log_info "Conda目录: $CONDA_DIR"
    
    # 激活conda
    source "$CONDA_SH_PATH"
    
    # 初始化conda（如果未初始化）
    if ! grep -q "conda initialize" ~/.bashrc; then
        log_info "初始化conda"
        conda init bash
    fi
    
    # 检查cpp环境是否已存在
    if ! conda env list | grep -q "^cpp "; then
        log_info "创建cpp环境"
        conda create -n cpp -y
    else
        log_info "cpp环境已存在，跳过创建步骤"
    fi
    
    # 激活环境
    log_info "激活cpp环境"
    conda activate cpp
    
    return 0
}

# 安装并验证xeus-cling
install_xeus_cling() {
    log_info "==== 安装xeus-cling (C++内核) ===="
    
    # 尝试从conda-forge安装xeus-cling
    log_info "尝试安装xeus-cling..."
    conda install -y -c conda-forge xeus-cling || {
        log_warning "标准安装失败，尝试使用指定版本..."
        conda install -y -c conda-forge xeus-cling=0.12.1 || {
            log_error "xeus-cling安装失败。请确保conda-forge通道可用。"
            log_info "您可以尝试手动运行: conda install -y -c conda-forge xeus-cling"
            return 1
        }
    }
    
    # 验证C++内核是否已安装
    log_info "正在验证C++内核安装..."
    if jupyter kernelspec list 2>/dev/null | grep -q "xcpp"; then
        log_success "C++内核(xcpp)已成功安装"
        return 0
    fi
    
    # 如果未找到内核，尝试手动注册
    log_warning "C++内核(xcpp)未找到，尝试手动注册..."
    
    # 查找内核路径
    local KERNEL_PATH=$(find "$CONDA_DIR/envs/cpp" -path "*/share/jupyter/kernels/xcpp*" -type d 2>/dev/null | head -n 1)
    
    if [ -n "$KERNEL_PATH" ]; then
        log_info "找到C++内核路径: $KERNEL_PATH"
        log_info "正在手动注册内核..."
        jupyter kernelspec install --user "$KERNEL_PATH" && {
            log_success "C++内核注册成功"
            return 0
        } || {
            log_error "C++内核注册失败"
            return 1
        }
    else
        log_error "无法找到C++内核目录。xeus-cling可能安装不完整。"
        log_info "建议重新创建环境："
        log_info "  conda env remove -n cpp"
        log_info "  conda create -n cpp -c conda-forge xeus-cling"
        return 1
    fi
}

# 安装必要的包
install_packages() {
    log_info "==== 安装必要的包 ===="
    
    # 安装基本包
    check_and_install_package "notebook" || log_warning "notebook安装失败"
    check_and_install_package "jupyterlab" || log_warning "jupyterlab安装失败"
    check_and_install_package "ipython_genutils" || log_warning "ipython_genutils安装失败"
    
    # 安装和验证xeus-cling
    install_xeus_cling || log_error "xeus-cling安装或注册失败"
    
    # 显示所有可用的内核
    log_info "已安装的Jupyter内核列表:"
    jupyter kernelspec list
    
    return 0
}

# 配置Jupyter
configure_jupyter() {
    log_info "==== 配置Jupyter ===="
    
    # 询问端口、IP和密码
    read -p "请输入Jupyter监听端口（默认8888）: " JUPYTER_PORT
    JUPYTER_PORT=${JUPYTER_PORT:-8888}
    read -p "请输入Jupyter监听IP（默认127.0.0.1，仅本地访问）: " JUPYTER_IP
    JUPYTER_IP=${JUPYTER_IP:-127.0.0.1}
    read -p "是否设置Jupyter密码用于连接？[Y/n]: " SET_PWD
    
    # 创建配置目录
    mkdir -p "$CONFIG_DIR"
    
    # 处理密码设置
    local JUPYTER_PWD_HASH=""
    if [[ ! $SET_PWD =~ ^[Nn]$ ]]; then
        echo "请输入Jupyter密码（输入时不会显示）: "
        read -s JUPYTER_PWD
        echo
        
        # 生成密码哈希
        log_info "生成密码哈希..."
        JUPYTER_PWD_HASH=$(python3 -c "from jupyter_server.auth import passwd; print(passwd('$JUPYTER_PWD'))" 2>/dev/null)
        
        # 如果上面的命令失败，尝试使用notebook的passwd函数
        if [ -z "$JUPYTER_PWD_HASH" ]; then
            JUPYTER_PWD_HASH=$(python3 -c "from notebook.auth import passwd; print(passwd('$JUPYTER_PWD'))")
        fi
        
        if [ -z "$JUPYTER_PWD_HASH" ]; then
            log_warning "无法生成密码哈希，将不设置密码"
        else
            log_success "密码哈希生成成功"
        fi
    fi
    
    # 生成配置内容
    log_info "生成Jupyter配置文件..."
    cat > "$JUPYTER_CONFIG" << EOF
c = get_config()
c.ServerApp.ip = '$JUPYTER_IP'
c.ServerApp.port = $JUPYTER_PORT
c.ServerApp.disable_check_xsrf = True
EOF
    
    if [ -n "$JUPYTER_PWD_HASH" ]; then
        echo "c.ServerApp.password = '$JUPYTER_PWD_HASH'" >> "$JUPYTER_CONFIG"
    fi
    
    # 创建用户主目录的Jupyter配置目录
    USER_JUPYTER_DIR=~/.jupyter
    mkdir -p $USER_JUPYTER_DIR
    
    # 复制配置文件到用户Jupyter配置目录
    cp "$JUPYTER_CONFIG" "$USER_JUPYTER_DIR/"
    log_success "已复制Jupyter配置文件到: $USER_JUPYTER_DIR/jupyter_notebook_config.py"
    
    return 0
}

# 配置Jupyter根目录
configure_jupyter_dir() {
    log_info "==== 配置Jupyter工作目录 ===="
    
    # 默认目录是项目根目录
    local default_dir="$PROJECT_ROOT"
    
    echo "请选择Jupyter启动时的工作目录："
    echo "1) 项目根目录 ($default_dir)"
    echo "2) 用户主目录 ($HOME)"
    echo "3) 自定义目录"
    read -p "请选择 [1/2/3，默认1]: " DIR_CHOICE
    DIR_CHOICE=${DIR_CHOICE:-1}
    
    local jupyter_dir
    if [ "$DIR_CHOICE" = "1" ]; then
        jupyter_dir="$default_dir"
        DIR_NAME="项目根目录"
    elif [ "$DIR_CHOICE" = "2" ]; then
        jupyter_dir="$HOME"
        DIR_NAME="用户主目录"
    else
        echo "请输入自定义目录的完整路径："
        read -p "路径: " jupyter_dir
        
        # 验证目录是否存在
        if [ ! -d "$jupyter_dir" ]; then
            log_warning "警告：目录 '$jupyter_dir' 不存在！"
            echo "您要创建这个目录吗？"
            read -p "创建目录？ [Y/n]: " CREATE_DIR
            if [[ ! $CREATE_DIR =~ ^[Nn]$ ]]; then
                mkdir -p "$jupyter_dir" || {
                    log_error "无法创建目录 '$jupyter_dir'，将使用默认目录"
                    jupyter_dir="$default_dir"
                    DIR_NAME="项目根目录(默认)"
                }
            else
                log_warning "未创建目录，将使用默认目录"
                jupyter_dir="$default_dir"
                DIR_NAME="项目根目录(默认)"
            fi
        else
            DIR_NAME="自定义目录"
        fi
    fi
    
    # 创建配置目录
    mkdir -p "$CONFIG_DIR"
    
    # 保存工作目录配置
    cat > "$JUPYTER_DIR_CONFIG" << EOF
#!/bin/bash
# Jupyter工作目录配置
# 配置于：$(date)
export JUPYTER_WORKING_DIR="$jupyter_dir"
EOF
    
    chmod +x "$JUPYTER_DIR_CONFIG"
    log_success "工作目录配置已保存到: $JUPYTER_DIR_CONFIG"
    log_success "Jupyter将在 '$DIR_NAME' ($jupyter_dir) 中启动"
    
    return 0
}

# 安装和配置C++ Jupyter环境
setup_cpp_jupyter() {
    log_info "==== 开始设置C++ Jupyter环境 ===="
    
    # 安装Miniconda (如果需要)
    install_miniconda
    
    # 设置conda环境
    setup_conda_env
    
    # 安装必要的包
    install_packages
    
    # 配置Jupyter
    configure_jupyter
    
    # 配置工作目录
    configure_jupyter_dir
    
    # 配置浏览器
    configure_browser
    
    log_success "==== C++ Jupyter环境设置完成 ===="
    log_info "现在您可以使用以下命令启动JupyterLab:"
    log_info "  $SCRIPT_DIR/bin/jupyter-cpp lab"
    
    return 0
} 