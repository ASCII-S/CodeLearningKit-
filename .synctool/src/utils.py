"""
工具类模块

提供日志功能、颜色输出和公共工具函数
"""

import os
import sys
import logging
import platform

# 配置日志
logging.basicConfig(
    level=logging.INFO,  # 默认日志级别
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建日志记录器
logger = logging.getLogger('synctool')

# 颜色输出配置
class Color:
    """终端颜色输出"""
    # 是否启用颜色（Windows CMD不支持ANSI颜色）
    ENABLED = not (platform.system() == 'Windows' and not os.environ.get('TERM'))
    
    # 颜色代码
    RESET = '\033[0m' if ENABLED else ''
    RED = '\033[31m' if ENABLED else ''
    GREEN = '\033[32m' if ENABLED else ''
    YELLOW = '\033[33m' if ENABLED else ''
    BLUE = '\033[34m' if ENABLED else ''
    MAGENTA = '\033[35m' if ENABLED else ''
    CYAN = '\033[36m' if ENABLED else ''
    GRAY = '\033[90m' if ENABLED else ''
    
    @staticmethod
    def colorize(text, color):
        """为文本添加颜色
        
        Args:
            text (str): 要着色的文本
            color (str): 颜色代码
            
        Returns:
            str: 着色后的文本
        """
        if Color.ENABLED:
            return f"{color}{text}{Color.RESET}"
        return text

def get_file_extension(file_path):
    """获取文件扩展名（不含点）
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        str: 文件扩展名
    """
    return os.path.splitext(file_path)[1][1:].lower()

def is_markdown_file(file_path):
    """判断是否为Markdown文件
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        bool: 是否为Markdown文件
    """
    ext = get_file_extension(file_path)
    result = ext == 'md'
    if result:
        logger.debug(f"{Color.GRAY}[文件类型] 检测到Markdown文件: {file_path}{Color.RESET}")
    return result

def is_notebook_file(file_path):
    """判断是否为Jupyter Notebook文件
    
    Args:
        file_path (str): 文件路径
        
    Returns:
        bool: 是否为Jupyter Notebook文件
    """
    ext = get_file_extension(file_path)
    result = ext == 'ipynb'
    if result:
        logger.debug(f"{Color.GRAY}[文件类型] 检测到Jupyter Notebook文件: {file_path}{Color.RESET}")
    return result

def get_relative_path(path, base_path):
    """获取相对路径
    
    Args:
        path (str): 文件或目录绝对路径
        base_path (str): 基准目录绝对路径
        
    Returns:
        str: 相对路径
    """
    rel_path = os.path.relpath(path, base_path)
    logger.debug(f"{Color.GRAY}[路径转换] 将绝对路径 {path} 转换为相对路径 {rel_path} (相对于 {base_path}){Color.RESET}")
    return rel_path

def ensure_dir_exists(directory):
    """确保目录存在，不存在则创建
    
    Args:
        directory (str): 目录路径
    """
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"{Color.GREEN}创建目录: {directory}{Color.RESET}")
    else:
        logger.debug(f"{Color.GRAY}[目录检查] 目录已存在: {directory}{Color.RESET}")
