#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
KIT_SCRIPT="$SCRIPT_DIR/kit.sh"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== 启动所有服务 =====${NC}"

# 首先在后台启动同步服务
echo -e "${YELLOW}[1] 启动后台同步服务...${NC}"
bash "$KIT_SCRIPT" sync &
SYNC_PID=$!
echo -e "${GREEN}同步服务已在后台启动 (PID: $SYNC_PID)${NC}"

# 然后启动JupyterLab
echo -e "${YELLOW}[2] 启动JupyterLab...${NC}"
bash "$KIT_SCRIPT" jupyter lab

# 注意：当JupyterLab关闭时，我们也应该关闭同步服务
echo -e "${YELLOW}JupyterLab已关闭，正在终止同步服务...${NC}"
kill $SYNC_PID 2>/dev/null || true
echo -e "${GREEN}所有服务已停止${NC}" 

# 避免脚本立即退出,按任意键退出
read -n 1 -s -r -p "按任意键退出..."