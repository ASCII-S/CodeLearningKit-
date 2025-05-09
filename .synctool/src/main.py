"""
主程序模块

程序入口，初始化各个模块，处理命令行参数
"""

import os
import sys
import time
import signal
import argparse
import logging
from pathlib import Path

from .utils import logger, Color
from .config_manager import ConfigManager
from .consistency_checker import ConsistencyChecker
from .sync_engine import SyncEngine
from .file_watcher import FileWatcher

def parse_arguments():
    """解析命令行参数
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description='MD和IPYNB文件同步工具')
    
    # 配置文件
    parser.add_argument('--config', '-c', 
                      help='配置文件路径', 
                      default=None)
    
    # 目录配置
    parser.add_argument('--md-dir', 
                      help='Markdown文件目录路径', 
                      default=None)
    parser.add_argument('--ipynb-dir', 
                      help='Jupyter Notebook文件目录路径', 
                      default=None)
    
    # 操作模式
    parser.add_argument('--check-only', action='store_true',
                      help='仅检查一致性，不进行同步')
    parser.add_argument('--sync-once', action='store_true',
                      help='执行一次同步后退出')
    parser.add_argument('--dry-run', action='store_true',
                      help='模拟运行，不实际修改文件')
    
    # 日志设置
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='显示详细日志')
    parser.add_argument('--debug', '-d', action='store_true',
                      help='显示调试日志')
    parser.add_argument('--quiet', '-q', action='store_true',
                      help='只显示错误和警告日志')
    
    return parser.parse_args()

def setup_signal_handlers(file_watcher):
    """设置信号处理器
    
    Args:
        file_watcher: 文件监控器实例
    """
    def signal_handler(sig, frame):
        logger.info(f"{Color.YELLOW}接收到中断信号，正在停止...{Color.RESET}")
        file_watcher.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # 终止信号

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志级别
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug(f"{Color.GRAY}已启用调试日志{Color.RESET}")
    elif args.verbose:
        logger.setLevel(logging.INFO)
    elif args.quiet:
        logger.setLevel(logging.WARNING)
    else:
        # 默认日志级别
        logger.setLevel(logging.INFO)
    
    # 显示欢迎信息
    logger.info(f"{Color.GREEN}=== MD和IPYNB文件同步工具 ==={Color.RESET}")
    
    # 初始化配置管理器
    config_manager = ConfigManager(args.config)
    
    # 命令行参数覆盖配置文件
    if args.md_dir:
        config_manager.set('md_dir', args.md_dir)
    if args.ipynb_dir:
        config_manager.set('ipynb_dir', args.ipynb_dir)
    
    # 打印配置信息
    md_dir = config_manager.get_md_dir()
    ipynb_dir = config_manager.get_ipynb_dir()
    logger.info(f"{Color.BLUE}Markdown目录: {md_dir}{Color.RESET}")
    logger.info(f"{Color.BLUE}Jupyter Notebook目录: {ipynb_dir}{Color.RESET}")
    
    # 初始化一致性检查器
    consistency_checker = ConsistencyChecker(config_manager)
    
    # 初始化同步引擎
    sync_engine = SyncEngine(config_manager, consistency_checker)
    
    # 初始化文件监控器
    file_watcher = FileWatcher(sync_engine)
    
    # 连接同步引擎和文件监控器
    sync_engine.set_file_watcher(file_watcher)
    
    # 设置信号处理器
    setup_signal_handlers(file_watcher)
    
    # 执行一致性检查
    if args.check_only:
        logger.info(f"{Color.BLUE}仅执行一致性检查...{Color.RESET}")
        consistency_checker.check_consistency()
        return
    
    # 执行初始同步
    if not args.dry_run:
        # 检查配置是否允许启动时执行一致性检查和同步
        check_on_start = config_manager.get('check_on_start', True)
        sync_on_start = config_manager.get('sync_on_start', True)
        
        if check_on_start:
            if sync_on_start:
                logger.info(f"{Color.BLUE}[初始化] 执行初始同步...{Color.RESET}")
                sync_engine.perform_initial_sync()
            else:
                logger.info(f"{Color.YELLOW}[初始化] 仅执行一致性检查，不进行同步{Color.RESET}")
                consistency_checker.check_consistency()
        else:
            logger.info(f"{Color.YELLOW}[跳过] 初始一致性检查和同步已在配置中禁用{Color.RESET}")
    else:
        logger.info(f"{Color.YELLOW}[模拟] 跳过初始同步{Color.RESET}")
    
    # 如果是单次同步模式，直接退出
    if args.sync_once:
        logger.info(f"{Color.GREEN}单次同步完成，退出程序{Color.RESET}")
        return
        
    # 启动文件监控
    if not args.dry_run:
        file_watcher.start()
    else:
        logger.info(f"{Color.YELLOW}[模拟] 跳过启动文件监控{Color.RESET}")
    
    try:
        # 主循环
        logger.info(f"{Color.GREEN}进入监控循环，按Ctrl+C退出{Color.RESET}")
        while True:
            try:
                # 处理待处理的事件
                file_watcher.process_pending_events()
            except Exception as e:
                logger.error(f"{Color.RED}事件处理出错，但监控将继续: {e}{Color.RESET}")
                import traceback
                logger.debug(f"{Color.RED}[详细错误] {traceback.format_exc()}{Color.RESET}")
            
            # 睡眠一段时间，避免CPU占用过高
            time.sleep(config_manager.get('watch_interval', 1.0))
    except KeyboardInterrupt:
        logger.info(f"{Color.YELLOW}接收到键盘中断，正在停止...{Color.RESET}")
    except Exception as e:
        logger.error(f"{Color.RED}程序发生错误: {e}{Color.RESET}")
        import traceback
        logger.error(f"{Color.RED}[详细错误] {traceback.format_exc()}{Color.RESET}")
    finally:
        # 停止文件监控
        file_watcher.stop()
        logger.info(f"{Color.GREEN}程序已停止{Color.RESET}")

if __name__ == "__main__":
    main()
