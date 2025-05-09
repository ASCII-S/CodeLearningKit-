"""
一致性检查模块

检查MD和IPYNB文件夹的结构是否一致，识别需要同步的文件
"""

import os
import re
import fnmatch
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from .utils import logger, Color, is_markdown_file, is_notebook_file

class ConsistencyChecker:
    """一致性检查类"""
    
    def __init__(self, config_manager):
        """初始化一致性检查器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.md_dir = self.config.get_md_dir()
        self.ipynb_dir = self.config.get_ipynb_dir()
        self.ignore_patterns = self.config.get('ignore_patterns', [])
        
    def is_ignored(self, path):
        """检查路径是否应被忽略
        
        Args:
            path (str): 文件或目录路径
            
        Returns:
            bool: 是否应被忽略
        """
        filename = os.path.basename(path)
        
        # 检查是否匹配任何忽略模式
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
                
        return False
        
    def get_corresponding_path(self, path, source_dir, target_dir, target_ext):
        """获取对应的目标路径
        
        Args:
            path (Path): 源文件路径
            source_dir (Path): 源目录
            target_dir (Path): 目标目录
            target_ext (str): 目标文件扩展名
            
        Returns:
            Path: 对应的目标路径
        """
        # 获取相对路径
        rel_path = path.relative_to(source_dir)
        
        # 更改扩展名并返回目标路径
        target_path = target_dir / rel_path.parent / (rel_path.stem + target_ext)
        return target_path
    
    def scan_directory(self, directory, base_dir=None):
        """扫描目录并返回文件信息
        
        Args:
            directory (Path): 要扫描的目录
            base_dir (Path, optional): 基准目录，用于计算相对路径
            
        Returns:
            dict: 文件信息字典，键为相对路径，值为文件信息
        """
        if base_dir is None:
            base_dir = directory
            
        files_info = {}
        
        # 确保目录存在
        if not directory.exists():
            logger.warning(f"{Color.YELLOW}目录不存在: {directory}{Color.RESET}")
            return files_info
            
        # 遍历目录
        for root, dirs, files in os.walk(directory):
            # 跳过忽略的目录
            dirs[:] = [d for d in dirs if not self.is_ignored(os.path.join(root, d))]
            
            # 处理文件
            for file in files:
                file_path = Path(root) / file
                
                # 跳过忽略的文件
                if self.is_ignored(file_path):
                    continue
                    
                # 计算相对路径
                rel_path = file_path.relative_to(base_dir)
                
                # 获取文件信息
                if file_path.exists():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    size = file_path.stat().st_size
                else:
                    mtime = None
                    size = 0
                
                # 添加到文件信息字典
                files_info[str(rel_path)] = {
                    'path': file_path,
                    'rel_path': rel_path,
                    'mtime': mtime,
                    'size': size,
                    'extension': file_path.suffix
                }
                
        return files_info
        
    def check_consistency(self):
        """检查MD和IPYNB文件夹的一致性
        
        Returns:
            dict: 包含同步操作的字典
        """
        # 扫描MD目录
        md_files = self.scan_directory(self.md_dir)
        logger.info(f"{Color.BLUE}扫描到 {len(md_files)} 个 MD 文件{Color.RESET}")
        
        # 扫描IPYNB目录
        ipynb_files = self.scan_directory(self.ipynb_dir)
        logger.info(f"{Color.BLUE}扫描到 {len(ipynb_files)} 个 IPYNB 文件{Color.RESET}")
        
        # 构建需要同步的文件列表
        sync_actions = {
            'md_to_ipynb': [],  # MD -> IPYNB 同步列表
            'ipynb_to_md': [],  # IPYNB -> MD 同步列表
            'conflict': [],     # 冲突文件列表
            'orphaned_md': [],  # 孤立的MD文件
            'orphaned_ipynb': []  # 孤立的IPYNB文件
        }
        
        # 检查MD文件对应的IPYNB文件
        for rel_path, md_info in md_files.items():
            if not is_markdown_file(str(md_info['path'])):
                continue
                
            # 计算对应的IPYNB路径
            rel_ipynb_path = str(Path(rel_path).parent / (Path(rel_path).stem + '.ipynb'))
            
            if rel_ipynb_path in ipynb_files:
                # 文件在两边都存在，检查修改时间决定同步方向
                md_mtime = md_info['mtime']
                ipynb_mtime = ipynb_files[rel_ipynb_path]['mtime']
                
                # 计算时间差的绝对值(秒)
                time_diff = abs((md_mtime - ipynb_mtime).total_seconds())
                
                # 如果时间差小于阈值，认为文件是同步的，避免因同步操作导致的时间戳轻微变化
                time_threshold = self.config.get('time_threshold', 5)  # 使用配置中的阈值，默认5秒
                if time_diff < time_threshold:
                    logger.info(f"{Color.YELLOW}[跳过同步] 文件时间戳相近(差异{time_diff:.2f}秒): {rel_path} ↔ {rel_ipynb_path}{Color.RESET}")
                    continue
                
                # 日志记录时间差，便于调试
                logger.debug(f"{Color.GRAY}[时间差] {rel_path} ↔ {rel_ipynb_path} 时间差: {time_diff:.2f}秒, MD: {md_mtime}, IPYNB: {ipynb_mtime}{Color.RESET}")
                
                # 如果MD文件较新，或者配置指定优先使用MD文件
                if (md_mtime > ipynb_mtime) or self.config.get('conflict_resolution') == 'md':
                    sync_actions['md_to_ipynb'].append({
                        'source': md_info['path'],
                        'target': ipynb_files[rel_ipynb_path]['path'],
                        'rel_path': rel_path,
                        'time_diff': time_diff
                    })
                    logger.debug(f"{Color.BLUE}[同步方向] MD → IPYNB ({time_diff:.2f}秒): {rel_path}{Color.RESET}")
                # 如果IPYNB文件较新，或者配置指定优先使用IPYNB文件
                elif (md_mtime < ipynb_mtime) or self.config.get('conflict_resolution') == 'ipynb':
                    sync_actions['ipynb_to_md'].append({
                        'source': ipynb_files[rel_ipynb_path]['path'],
                        'target': md_info['path'],
                        'rel_path': rel_ipynb_path,
                        'time_diff': time_diff
                    })
                    logger.debug(f"{Color.BLUE}[同步方向] IPYNB → MD ({time_diff:.2f}秒): {rel_ipynb_path}{Color.RESET}")
            else:
                # IPYNB文件不存在，添加到MD->IPYNB同步列表
                ipynb_path = self.get_corresponding_path(md_info['path'], self.md_dir, self.ipynb_dir, '.ipynb')
                sync_actions['md_to_ipynb'].append({
                    'source': md_info['path'],
                    'target': ipynb_path,
                    'rel_path': rel_path,
                    'time_diff': float('inf')  # 无对应文件，时间差设为无穷大
                })
                logger.debug(f"{Color.BLUE}[单向同步] MD → IPYNB (新文件): {rel_path}{Color.RESET}")
        
        # 检查IPYNB文件对应的MD文件
        for rel_path, ipynb_info in ipynb_files.items():
            if not is_notebook_file(str(ipynb_info['path'])):
                continue
                
            # 计算对应的MD路径
            rel_md_path = str(Path(rel_path).parent / (Path(rel_path).stem + '.md'))
            
            if rel_md_path not in md_files:
                # MD文件不存在，添加到IPYNB->MD同步列表
                md_path = self.get_corresponding_path(ipynb_info['path'], self.ipynb_dir, self.md_dir, '.md')
                sync_actions['ipynb_to_md'].append({
                    'source': ipynb_info['path'],
                    'target': md_path,
                    'rel_path': rel_path,
                    'time_diff': float('inf')  # 无对应文件，时间差设为无穷大
                })
                logger.debug(f"{Color.BLUE}[单向同步] IPYNB → MD (新文件): {rel_path}{Color.RESET}")
        
        # 标记孤立文件
        if self.config.get('delete_orphaned', False):
            # 检查孤立的MD文件
            for rel_path, md_info in md_files.items():
                if not is_markdown_file(str(md_info['path'])):
                    continue
                    
                rel_ipynb_path = str(Path(rel_path).parent / (Path(rel_path).stem + '.ipynb'))
                if rel_ipynb_path not in ipynb_files and not any(action['rel_path'] == rel_path for action in sync_actions['md_to_ipynb']):
                    sync_actions['orphaned_md'].append(md_info['path'])
                    logger.debug(f"{Color.RED}[孤立文件] MD: {rel_path}{Color.RESET}")
            
            # 检查孤立的IPYNB文件
            for rel_path, ipynb_info in ipynb_files.items():
                if not is_notebook_file(str(ipynb_info['path'])):
                    continue
                    
                rel_md_path = str(Path(rel_path).parent / (Path(rel_path).stem + '.md'))
                if rel_md_path not in md_files and not any(action['rel_path'] == rel_path for action in sync_actions['ipynb_to_md']):
                    sync_actions['orphaned_ipynb'].append(ipynb_info['path'])
                    logger.debug(f"{Color.RED}[孤立文件] IPYNB: {rel_path}{Color.RESET}")
        
        # 统计需要同步的文件数量
        md_to_ipynb_count = len(sync_actions['md_to_ipynb'])
        ipynb_to_md_count = len(sync_actions['ipynb_to_md'])
        conflict_count = len(sync_actions['conflict'])
        orphaned_md_count = len(sync_actions['orphaned_md'])
        orphaned_ipynb_count = len(sync_actions['orphaned_ipynb'])
        
        logger.info(f"{Color.GREEN}一致性检查完成:{Color.RESET}")
        logger.info(f"  {Color.CYAN}MD → IPYNB: {md_to_ipynb_count} 个文件{Color.RESET}")
        logger.info(f"  {Color.CYAN}IPYNB → MD: {ipynb_to_md_count} 个文件{Color.RESET}")
        logger.info(f"  {Color.YELLOW}冲突文件: {conflict_count} 个文件{Color.RESET}")
        logger.info(f"  {Color.RED}孤立MD文件: {orphaned_md_count} 个文件{Color.RESET}")
        logger.info(f"  {Color.RED}孤立IPYNB文件: {orphaned_ipynb_count} 个文件{Color.RESET}")
        
        return sync_actions
