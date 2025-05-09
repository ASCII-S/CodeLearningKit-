#!/bin/bash
# 浏览器配置模块

# 加载共享函数库
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# 浏览器检测函数
detect_browsers() {
    # 创建浏览器列表数组
    BROWSERS=()
    BROWSER_NAMES=()
    
    # 定义常见浏览器路径
    local BROWSER_PATHS=(
        "/mnt/c/Program Files/Google/Chrome/Application/chrome.exe:Google Chrome"
        "/mnt/c/Program Files (x86)/Google/Chrome/Application/chrome.exe:Google Chrome"
        "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe:Microsoft Edge"
        "/mnt/c/Program Files/Microsoft/Edge/Application/msedge.exe:Microsoft Edge"
        "/mnt/c/Program Files/Mozilla Firefox/firefox.exe:Mozilla Firefox"
        "/mnt/c/Program Files (x86)/Mozilla Firefox/firefox.exe:Mozilla Firefox"
        "/mnt/c/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe:Brave"
        "/mnt/c/Program Files/Opera/launcher.exe:Opera"
        "/mnt/c/Program Files (x86)/Opera/launcher.exe:Opera"
        "/mnt/c/Program Files/Vivaldi/Application/vivaldi.exe:Vivaldi"
    )
    
    # 检查每个浏览器
    for browser_info in "${BROWSER_PATHS[@]}"; do
        # 分割路径和名称
        local path="${browser_info%%:*}"
        local name="${browser_info#*:}"
        
        if [ -f "$path" ]; then
            BROWSERS+=("$path")
            BROWSER_NAMES+=("$name")
        fi
    done
    
    # 始终添加Windows资源管理器作为后备选项
    BROWSERS+=("/mnt/c/Windows/explorer.exe")
    BROWSER_NAMES+=("Windows资源管理器")
}

# 配置浏览器函数
configure_browser() {
    log_info "配置浏览器..."
    
    # 检测系统中可用的浏览器
    detect_browsers
    
    # 询问是否自动打开浏览器
    echo "是否在启动Jupyter时自动打开浏览器？"
    echo "1) 是（推荐）"
    echo "2) 否"
    read -p "请选择 [1/2，默认1]: " AUTO_OPEN_CHOICE
    AUTO_OPEN_CHOICE=${AUTO_OPEN_CHOICE:-1}
    
    if [ "$AUTO_OPEN_CHOICE" = "1" ]; then
        AUTO_OPEN_BROWSER=true
        
        # 显示检测到的浏览器列表
        echo ""
        echo "检测到的Windows浏览器:"
        for i in "${!BROWSER_NAMES[@]}"; do
            echo "$((i+1))) ${BROWSER_NAMES[i]} (${BROWSERS[i]})"
        done
        echo "$((${#BROWSER_NAMES[@]}+1))) 手动输入其他浏览器路径"
        
        # 选择浏览器
        read -p "请选择默认浏览器 [1-$((${#BROWSER_NAMES[@]}+1))，默认1]: " BROWSER_CHOICE
        BROWSER_CHOICE=${BROWSER_CHOICE:-1}
        
        if [ "$BROWSER_CHOICE" -le "${#BROWSER_NAMES[@]}" ]; then
            BROWSER_PATH="${BROWSERS[$((BROWSER_CHOICE-1))]}"
            SELECTED_BROWSER="${BROWSER_NAMES[$((BROWSER_CHOICE-1))]}"
        else
            echo "请输入浏览器的完整路径（例如：/mnt/c/Program Files/Google/Chrome/Application/chrome.exe）"
            read -p "路径: " BROWSER_PATH
            # 验证路径是否存在
            if [ ! -f "$BROWSER_PATH" ]; then
                log_warning "警告：路径 '$BROWSER_PATH' 不存在或不是文件！"
                echo "您确定要使用这个路径吗？Jupyter可能无法自动打开浏览器。"
                read -p "继续？ [y/N]: " CONTINUE
                if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
                    log_error "操作已取消。请重新运行脚本。"
                    return 1
                fi
            fi
            SELECTED_BROWSER="自定义浏览器"
        fi
    else
        AUTO_OPEN_BROWSER=false
        BROWSER_PATH=""
        SELECTED_BROWSER="无"
    fi
    
    # 创建配置目录
    mkdir -p "$CONFIG_DIR"
    
    # 保存浏览器配置
    cat > "$BROWSER_CONFIG" << EOF
#!/bin/bash
# Jupyter浏览器配置
# 配置于：$(date)
export AUTO_OPEN_BROWSER=$AUTO_OPEN_BROWSER
export BROWSER="$BROWSER_PATH"
EOF
    
    chmod +x "$BROWSER_CONFIG"
    log_success "浏览器配置已保存到: $BROWSER_CONFIG"
    
    if [ "$AUTO_OPEN_BROWSER" = true ]; then
        log_success "配置完成，Jupyter将使用 '$SELECTED_BROWSER' 自动打开。"
    else
        log_success "配置完成，Jupyter将不会自动打开浏览器。"
    fi
    
    return 0
} 