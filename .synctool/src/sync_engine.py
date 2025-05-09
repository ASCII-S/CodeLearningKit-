"""
同步引擎模块

负责处理文件同步逻辑，决定同步方向和策略，调用转换器进行文件转换
"""

import os
import time
import shutil
from pathlib import Path
from datetime import datetime

from .utils import logger, Color, is_markdown_file, is_notebook_file, ensure_dir_exists, get_relative_path
from .converter import Converter

class SyncEngine:
    """同步引擎类"""
    
    def __init__(self, config_manager, consistency_checker):
        """初始化同步引擎
        
        Args:
            config_manager: 配置管理器实例
            consistency_checker: 一致性检查器实例
        """
        self.config = config_manager
        self.consistency_checker = consistency_checker
        self.converter = Converter(config_manager)
        self.md_dir = self.config.get_md_dir()
        self.ipynb_dir = self.config.get_ipynb_dir()
        
        # 跟踪已同步的文件，避免循环同步
        self.recently_synced = set()
        self.sync_timeout = 5  # 同步超时时间（秒）
        
        # 文件监控器，后续初始化
        self.file_watcher = None
        
    def set_file_watcher(self, file_watcher):
        """设置文件监控器
        
        Args:
            file_watcher: 文件监控器实例
        """
        self.file_watcher = file_watcher
        
    def handle_file_event(self, file_path, event_type):
        """处理文件事件
        
        Args:
            file_path (Path): 文件路径
            event_type (str): 事件类型（created, modified, moved, deleted）
        """
        logger.info(f"{Color.CYAN}[事件] {event_type:10s} {file_path}{Color.RESET}")
        
        # 将事件添加到文件监控器的待处理队列
        if self.file_watcher:
            self.file_watcher.add_pending_event(file_path, event_type)
        else:
            # 如果文件监控器未初始化，直接处理
            if event_type == "deleted":
                self.handle_file_deletion(file_path)
            else:
                self.sync_file_if_needed(file_path)
    
    def handle_file_deletion(self, file_path):
        """处理文件删除事件
        
        Args:
            file_path (Path): 被删除的文件路径
        """
        try:
            # 确定文件是MD还是IPYNB
            is_md = is_markdown_file(str(file_path))
            is_ipynb = is_notebook_file(str(file_path))
            
            if not (is_md or is_ipynb):
                logger.debug(f"{Color.GRAY}[跳过] 忽略非目标文件类型: {file_path}{Color.RESET}")
                return
                
            # 确定对应的目标文件
            if is_md:
                # 被删除的是MD文件，找到对应的IPYNB文件
                rel_path = get_relative_path(file_path, self.md_dir)
                target_path = self.ipynb_dir / Path(rel_path).with_suffix('.ipynb')
            else:
                # 被删除的是IPYNB文件，找到对应的MD文件
                rel_path = get_relative_path(file_path, self.ipynb_dir)
                target_path = self.md_dir / Path(rel_path).with_suffix('.md')
            
            # 如果目标文件存在且配置允许删除对应文件
            if target_path.exists() and self.config.get('delete_orphaned', False):
                logger.info(f"{Color.RED}[删除] 删除对应的目标文件: {target_path}{Color.RESET}")
                try:
                    target_path.unlink()  # 删除目标文件
                except FileNotFoundError:
                    logger.warning(f"{Color.YELLOW}[注意] 文件已不存在: {target_path}{Color.RESET}")
                except PermissionError:
                    logger.error(f"{Color.RED}[错误] 没有权限删除文件: {target_path}{Color.RESET}")
                except Exception as e:
                    logger.error(f"{Color.RED}[错误] 删除文件时出错: {target_path}, 错误: {e}{Color.RESET}")
            else:
                logger.info(f"{Color.YELLOW}[保留] 目标文件未删除: {target_path}{Color.RESET}")
                
        except Exception as e:
            logger.error(f"{Color.RED}[错误] 处理删除事件出错: {file_path}, 错误: {e}{Color.RESET}")
            # 记录详细的错误信息以便调试
            import traceback
            logger.debug(f"{Color.RED}[详细错误] {traceback.format_exc()}{Color.RESET}")
    
    def sync_file_if_needed(self, file_path):
        """如果需要，同步文件
        
        Args:
            file_path (Path): 文件路径
        """
        file_path = Path(file_path)
        path_str = str(file_path)
        
        # 检查文件是否存在
        if not file_path.exists():
            logger.debug(f"{Color.GRAY}[跳过] 文件不存在: {file_path}{Color.RESET}")
            return
            
        # 检查是否是最近同步的文件
        if path_str in self.recently_synced:
            current_time = time.time()
            # 从集合中移除，避免无限增长
            self.recently_synced.remove(path_str)
            logger.debug(f"{Color.GRAY}[跳过] 最近同步过的文件: {file_path}{Color.RESET}")
            return
            
        # 检查文件类型
        is_md = is_markdown_file(path_str)
        is_ipynb = is_notebook_file(path_str)
        
        if not (is_md or is_ipynb):
            logger.debug(f"{Color.GRAY}[跳过] 不支持的文件类型: {file_path}{Color.RESET}")
            return
            
        try:
            # 根据文件类型决定同步方向
            if is_md:
                # 从MD到IPYNB的同步
                source_dir = self.md_dir
                target_dir = self.ipynb_dir
                
                # 检查文件是否在MD目录中
                if self.md_dir in file_path.parents or self.md_dir == file_path.parent:
                    rel_path = get_relative_path(file_path, source_dir)
                    # 修复：确保rel_path是Path对象
                    rel_path = Path(rel_path)
                    target_path = target_dir / rel_path.with_suffix('.ipynb')
                    
                    # 执行同步
                    self.sync_md_to_ipynb(file_path, target_path)
                else:
                    logger.debug(f"{Color.GRAY}[跳过] MD文件不在配置的目录中: {file_path}{Color.RESET}")
                    
            elif is_ipynb:
                # 从IPYNB到MD的同步
                source_dir = self.ipynb_dir
                target_dir = self.md_dir
                
                # 检查文件是否在IPYNB目录中
                if self.ipynb_dir in file_path.parents or self.ipynb_dir == file_path.parent:
                    rel_path = get_relative_path(file_path, source_dir)
                    # 修复：确保rel_path是Path对象
                    rel_path = Path(rel_path)
                    target_path = target_dir / rel_path.with_suffix('.md')
                    
                    # 执行同步
                    self.sync_ipynb_to_md(file_path, target_path)
                else:
                    logger.debug(f"{Color.GRAY}[跳过] IPYNB文件不在配置的目录中: {file_path}{Color.RESET}")
        
        except Exception as e:
            logger.error(f"{Color.RED}[错误] 同步失败: {file_path}, 错误: {e}{Color.RESET}")
    
    def sync_md_to_ipynb(self, md_path, ipynb_path):
        """将MD文件同步到IPYNB文件
        
        Args:
            md_path (Path): MD文件路径
            ipynb_path (Path): 目标IPYNB文件路径
        """
        logger.info(f"{Color.GREEN}[同步] MD → IPYNB: {md_path} → {ipynb_path}{Color.RESET}")
        
        # 确保目标目录存在
        ensure_dir_exists(ipynb_path.parent)
        
        # 检查目标文件是否存在，决定处理策略
        if ipynb_path.exists():
            # 根据配置决定是否覆盖
            conflict_resolution = self.config.get('conflict_resolution', 'newer')
            
            if conflict_resolution == 'md':
                # 总是优先使用MD文件
                pass  # 继续同步
            elif conflict_resolution == 'ipynb':
                # 总是优先使用IPYNB文件
                logger.info(f"{Color.YELLOW}[跳过] 配置优先使用IPYNB: {ipynb_path}{Color.RESET}")
                return
            elif conflict_resolution == 'newer':
                # 比较修改时间，使用较新的文件
                md_mtime = datetime.fromtimestamp(md_path.stat().st_mtime)
                ipynb_mtime = datetime.fromtimestamp(ipynb_path.stat().st_mtime)
                
                # 计算时间差的绝对值（秒）
                time_diff = abs((md_mtime - ipynb_mtime).total_seconds())
                
                # 如果时间差小于配置的阈值，则认为文件相同，不需要同步
                time_threshold = self.config.get('time_threshold', 3)  # 默认3秒
                if time_diff < time_threshold:
                    logger.info(f"{Color.YELLOW}[跳过] 文件时间戳相近(差异{time_diff:.2f}秒): {md_path} ↔ {ipynb_path}{Color.RESET}")
                    return
                
                if ipynb_mtime > md_mtime:
                    logger.info(f"{Color.YELLOW}[跳过] IPYNB文件较新: {ipynb_path} ({ipynb_mtime} > {md_mtime}){Color.RESET}")
                    return
        
        # 执行转换
        try:
            # 记录为最近同步的文件，避免循环同步
            self.recently_synced.add(str(ipynb_path))
            
            # 转换文件
            self.converter.md_to_ipynb(md_path, ipynb_path)
            
            logger.info(f"{Color.BLUE}[完成] MD → IPYNB: {md_path} → {ipynb_path}{Color.RESET}")
        except Exception as e:
            logger.error(f"{Color.RED}[失败] MD → IPYNB转换错误: {md_path} → {ipynb_path}, 错误: {e}{Color.RESET}")
    
    def sync_ipynb_to_md(self, ipynb_path, md_path):
        """将IPYNB文件同步到MD文件
        
        Args:
            ipynb_path (Path): IPYNB文件路径
            md_path (Path): 目标MD文件路径
        """
        logger.info(f"{Color.GREEN}[同步] IPYNB → MD: {ipynb_path} → {md_path}{Color.RESET}")
        
        # 确保目标目录存在
        ensure_dir_exists(md_path.parent)
        
        # 检查目标文件是否存在，决定处理策略
        if md_path.exists():
            # 根据配置决定是否覆盖
            conflict_resolution = self.config.get('conflict_resolution', 'newer')
            
            if conflict_resolution == 'ipynb':
                # 总是优先使用IPYNB文件
                pass  # 继续同步
            elif conflict_resolution == 'md':
                # 总是优先使用MD文件
                logger.info(f"{Color.YELLOW}[跳过] 配置优先使用MD: {md_path}{Color.RESET}")
                return
            elif conflict_resolution == 'newer':
                # 比较修改时间，使用较新的文件
                ipynb_mtime = datetime.fromtimestamp(ipynb_path.stat().st_mtime)
                md_mtime = datetime.fromtimestamp(md_path.stat().st_mtime)
                
                # 计算时间差的绝对值（秒）
                time_diff = abs((ipynb_mtime - md_mtime).total_seconds())
                
                # 如果时间差小于配置的阈值，则认为文件相同，不需要同步
                time_threshold = self.config.get('time_threshold', 3)  # 默认3秒
                if time_diff < time_threshold:
                    logger.info(f"{Color.YELLOW}[跳过] 文件时间戳相近(差异{time_diff:.2f}秒): {ipynb_path} ↔ {md_path}{Color.RESET}")
                    return
                
                if md_mtime > ipynb_mtime:
                    logger.info(f"{Color.YELLOW}[跳过] MD文件较新: {md_path} ({md_mtime} > {ipynb_mtime}){Color.RESET}")
                    return
        
        # 执行转换
        try:
            # 记录为最近同步的文件，避免循环同步
            self.recently_synced.add(str(md_path))
            
            # 转换文件
            self.converter.ipynb_to_md(ipynb_path, md_path)
            
            logger.info(f"{Color.BLUE}[完成] IPYNB → MD: {ipynb_path} → {md_path}{Color.RESET}")
        except Exception as e:
            logger.error(f"{Color.RED}[失败] IPYNB → MD转换错误: {ipynb_path} → {md_path}, 错误: {e}{Color.RESET}")
    
    def perform_initial_sync(self):
        """执行初始同步，确保两个目录的一致性"""
        if not self.config.get('sync_on_start', True):
            logger.info(f"{Color.YELLOW}[跳过] 初始同步已在配置中禁用{Color.RESET}")
            return
            
        logger.info(f"{Color.BLUE}[初始化] 执行初始同步...{Color.RESET}")
        
        # 执行一致性检查
        sync_actions = self.consistency_checker.check_consistency()
        
        # 执行MD到IPYNB的同步
        for action in sync_actions['md_to_ipynb']:
            self.sync_md_to_ipynb(action['source'], action['target'])
            
        # 执行IPYNB到MD的同步
        for action in sync_actions['ipynb_to_md']:
            self.sync_ipynb_to_md(action['source'], action['target'])
            
        # 处理孤立文件
        if self.config.get('delete_orphaned', False):
            # 删除孤立的MD文件
            for path in sync_actions['orphaned_md']:
                logger.info(f"{Color.RED}[删除] 孤立的MD文件: {path}{Color.RESET}")
                Path(path).unlink(missing_ok=True)
                
            # 删除孤立的IPYNB文件
            for path in sync_actions['orphaned_ipynb']:
                logger.info(f"{Color.RED}[删除] 孤立的IPYNB文件: {path}{Color.RESET}")
                Path(path).unlink(missing_ok=True)
        
        logger.info(f"{Color.GREEN}[完成] 初始同步已完成{Color.RESET}")
