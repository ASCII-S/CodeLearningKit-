#!/bin/bash

# CodeLearningKit 集成脚本 - 直接调用各工具的功能

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 工具定义
JUPYTER_TOOL="$SCRIPT_DIR/.jupyter-setup/bin/jupyter-cpp"
SYNC_TOOL_DIR="$SCRIPT_DIR/.synctool/src"

# 显示工具列表
function show_tools {
    echo -e "${BLUE}===== CodeLearningKit 工具集 =====${NC}"
    echo ""
    
    # 检查Jupyter工具
    if [ -f "$JUPYTER_TOOL" ]; then
        echo -e "${GREEN}[可用]${NC} ${CYAN}jupyter${NC} - Jupyter C++环境工具"
        echo -e "       源自: ${YELLOW}.jupyter-setup${NC}"
        echo -e "       用法: ${GREEN}./kit.sh jupyter [命令] [参数]${NC}"
        echo -e "       命令: setup, notebook, lab, browser, dir, help"
        echo ""
    else
        echo -e "${RED}[不可用]${NC} ${CYAN}jupyter${NC} - Jupyter环境工具 (未找到)"
        echo ""
    fi
    
    # 检查同步工具
    if [ -d "$SYNC_TOOL_DIR" ]; then
        echo -e "${GREEN}[可用]${NC} ${PURPLE}sync${NC} - MD与IPYNB文件同步工具"
        echo -e "       源自: ${YELLOW}.synctool${NC}"
        echo -e "       用法: ${GREEN}./kit.sh sync [选项]${NC}"
        echo -e "       选项: --check-only, --sync-once, --dry-run, --verbose, --debug, --quiet"
        echo -e "             --config=FILE, --md-dir=DIR, --ipynb-dir=DIR"
        echo ""
    else
        echo -e "${RED}[不可用]${NC} ${PURPLE}sync${NC} - 文件同步工具 (未找到)"
        echo ""
    fi
    
    echo -e "通用命令:"
    echo -e "  ${GREEN}./kit.sh tools${NC}    - 显示此工具列表"
    echo -e "  ${GREEN}./kit.sh help${NC}     - 显示帮助信息"
    echo -e "  ${GREEN}./kit.sh <工具> help${NC} - 显示特定工具的帮助"
}

# 展示 Jupyter 工具的帮助信息
function show_jupyter_help {
    if [ -f "$JUPYTER_TOOL" ]; then
        echo -e "${BLUE}Jupyter C++环境工具 - 帮助信息${NC}"
        echo -e "源自: ${YELLOW}.jupyter-setup${NC}"
        echo ""
        echo -e "用法: ${GREEN}./kit.sh jupyter [命令] [参数]${NC}"
        echo ""
        echo "可用命令:"
        echo "  setup       设置C++ Jupyter环境"
        echo "  notebook    启动Jupyter Notebook"
        echo "  lab         启动JupyterLab (默认)"
        echo "  browser     配置浏览器设置"
        echo "  dir         配置工作目录"
        echo "  help        显示此帮助信息"
        echo ""
        echo "选项:"
        echo "  --port=XXXX       指定端口号 (默认: 8888)"
        echo "  --bg              在后台运行"
        echo "  --force-browser   强制打开浏览器(忽略配置)"
        echo "  --dir=PATH        指定工作目录(覆盖配置)"
        echo ""
        echo "示例:"
        echo "  ./kit.sh jupyter setup                  # 安装和配置C++ Jupyter环境"
        echo "  ./kit.sh jupyter lab                    # 启动JupyterLab"
        echo "  ./kit.sh jupyter notebook               # 启动Jupyter Notebook"
        echo "  ./kit.sh jupyter lab --force-browser    # 启动JupyterLab并强制打开浏览器"
    else
        echo -e "${RED}错误: Jupyter工具未找到${NC}"
    fi
}

# 展示同步工具的帮助信息
function show_sync_help {
    if [ -d "$SYNC_TOOL_DIR" ]; then
        echo -e "${BLUE}MD与IPYNB文件同步工具 - 帮助信息${NC}"
        echo -e "源自: ${YELLOW}.synctool${NC}"
        echo ""
        echo -e "用法: ${GREEN}./kit.sh sync [选项]${NC}"
        echo ""
        echo "操作模式:"
        echo "  --check-only      仅检查一致性，不进行同步"
        echo "  --sync-once       执行一次同步后退出"
        echo "  --dry-run         模拟运行，不实际修改文件"
        echo ""
        echo "配置选项:"
        echo "  --config=FILE     指定配置文件路径"
        echo "  --md-dir=DIR      指定Markdown文件目录"
        echo "  --ipynb-dir=DIR   指定Jupyter Notebook文件目录"
        echo ""
        echo "日志选项:"
        echo "  --verbose, -v     显示详细日志"
        echo "  --debug, -d       显示调试日志"
        echo "  --quiet, -q       只显示错误和警告日志"
        echo ""
        echo "示例:"
        echo "  ./kit.sh sync                     # 启动同步服务"
        echo "  ./kit.sh sync --check-only        # 仅检查一致性"
        echo "  ./kit.sh sync --sync-once         # 执行一次同步后退出"
        echo "  ./kit.sh sync --md-dir=./notes    # 指定Markdown目录"
    else
        echo -e "${RED}错误: 同步工具未找到${NC}"
    fi
}

# 显示通用帮助信息
function show_help {
    echo -e "${BLUE}CodeLearningKit 集成工具 - 帮助信息${NC}"
    echo ""
    echo -e "用法: ${GREEN}./kit.sh <工具|命令> [子命令] [选项]${NC}"
    echo ""
    echo "可用工具和命令:"
    echo "  jupyter    - Jupyter C++环境工具 (来自 .jupyter-setup)"
    echo "  sync       - MD与IPYNB文件同步工具 (来自 .synctool)"
    echo "  tools      - 显示可用工具列表"
    echo "  help       - 显示此帮助信息"
    echo ""
    echo "获取特定工具的帮助:"
    echo "  ./kit.sh jupyter help"
    echo "  ./kit.sh sync help"
    echo ""
    echo "示例用法:"
    echo "  ./kit.sh tools                      # 列出所有可用工具"
    echo "  ./kit.sh jupyter lab                # 启动JupyterLab"
    echo "  ./kit.sh sync --check-only          # 运行同步工具的一致性检查"
}

# 处理Jupyter命令
function handle_jupyter {
    if [ ! -f "$JUPYTER_TOOL" ]; then
        echo -e "${RED}错误: Jupyter工具未找到 ($JUPYTER_TOOL)${NC}"
        return 1
    fi
    
    # 检查是否是帮助命令
    if [ "$1" == "help" ] || [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
        show_jupyter_help
        return
    fi
    
    # 直接调用jupyter-cpp脚本
    echo -e "${GREEN}[Jupyter工具]${NC} 执行命令: $@"
    bash "$JUPYTER_TOOL" "$@"
}

# 处理同步命令
function handle_sync {
    if [ ! -d "$SYNC_TOOL_DIR" ]; then
        echo -e "${RED}错误: 同步工具未找到 ($SYNC_TOOL_DIR)${NC}"
        return 1
    fi
    
    # 检查是否是帮助命令
    if [ "$1" == "help" ] || [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
        show_sync_help
        return
    fi
    
    # 使用Python执行同步工具
    echo -e "${GREEN}[同步工具]${NC} 执行命令"
    python -m "$SCRIPT_DIR".synctool.src.main "$@"
}

# 主函数
function main {
    if [ $# -eq 0 ]; then
        show_tools
        return
    fi
    
    case "$1" in
        jupyter)
            shift
            handle_jupyter "$@"
            ;;
        sync)
            shift
            handle_sync "$@"
            ;;
        tools)
            show_tools
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}错误: 未知工具或命令 '$1'${NC}"
            show_tools
            return 1
            ;;
    esac
}

# 执行主函数
main "$@" 