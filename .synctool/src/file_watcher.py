"""
文件监控模块

负责监控文件系统变化并触发同步
"""

import os
import time
import stat
from pathlib import Path
from collections import defaultdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers.polling import PollingObserver  # 添加轮询观察者

from .utils import logger, Color, is_markdown_file, is_notebook_file

class SyncFileHandler(FileSystemEventHandler):
    """处理文件系统事件，转发给同步引擎"""
    
    def __init__(self, sync_engine):
        """初始化文件处理器
        
        Args:
            sync_engine: 同步引擎实例
        """
        self.engine = sync_engine
        # 跟踪已被处理的删除事件，避免重复处理
        self.processed_deletes = set()
        self.last_event_time = time.time()
        
    def dispatch(self, event):
        """重写调度方法，确保所有事件都能被记录
        
        Args:
            event: 文件系统事件
        """
        current_time = time.time()
        # 记录时间以便调试
        path = event.src_path if hasattr(event, 'src_path') else "未知路径"
        event_type = event.event_type if hasattr(event, 'event_type') else "未知事件"
        
        logger.debug(f"{Color.MAGENTA}[原始事件] 接收到事件 {event_type}: {path} ({current_time - self.last_event_time:.3f}秒前){Color.RESET}")
        self.last_event_time = current_time
        
        # 调用父类方法继续处理
        super().dispatch(event)
    
    def on_modified(self, event):
        """处理文件修改事件
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            path = event.src_path
            logger.debug(f"{Color.CYAN}[文件修改] 检测到文件修改: {path}{Color.RESET}")
            
            # 特别检查是否为ipynb或md文件
            if path.endswith('.ipynb'):
                logger.info(f"{Color.GREEN}[IPYNB修改] 检测到IPYNB文件修改: {path}{Color.RESET}")
            elif path.endswith('.md'):
                logger.info(f"{Color.GREEN}[MD修改] 检测到MD文件修改: {path}{Color.RESET}")
            
            self.engine.handle_file_event(Path(path), "modified")
    
    def on_created(self, event):
        """处理文件创建事件
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            path = event.src_path
            logger.debug(f"{Color.CYAN}[文件创建] 检测到文件创建: {path}{Color.RESET}")
            
            # 特别检查是否为ipynb或md文件
            if path.endswith('.ipynb'):
                logger.info(f"{Color.GREEN}[IPYNB创建] 检测到IPYNB文件创建: {path}{Color.RESET}")
            elif path.endswith('.md'):
                logger.info(f"{Color.GREEN}[MD创建] 检测到MD文件创建: {path}{Color.RESET}")
                
            self.engine.handle_file_event(Path(path), "created")
    
    def on_moved(self, event):
        """处理文件移动事件
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            dest_path = event.dest_path
            logger.debug(f"{Color.CYAN}[文件移动] 检测到文件移动: {event.src_path} -> {dest_path}{Color.RESET}")
            
            # 特别检查是否为ipynb或md文件
            if dest_path.endswith('.ipynb'):
                logger.info(f"{Color.GREEN}[IPYNB移动] 检测到IPYNB文件移动: {event.src_path} -> {dest_path}{Color.RESET}")
            elif dest_path.endswith('.md'):
                logger.info(f"{Color.GREEN}[MD移动] 检测到MD文件移动: {event.src_path} -> {dest_path}{Color.RESET}")
                
            self.engine.handle_file_event(Path(dest_path), "moved")
            
    def on_deleted(self, event):
        """处理文件删除事件
        
        Args:
            event: 文件系统事件
        """
        if not event.is_directory:
            path = Path(event.src_path)
            path_str = str(path)
            
            logger.debug(f"{Color.CYAN}[文件删除] 检测到文件删除: {path}{Color.RESET}")
            
            # 特别检查是否为ipynb或md文件
            if path_str.endswith('.ipynb'):
                logger.info(f"{Color.GREEN}[IPYNB删除] 检测到IPYNB文件删除: {path}{Color.RESET}")
            elif path_str.endswith('.md'):
                logger.info(f"{Color.GREEN}[MD删除] 检测到MD文件删除: {path}{Color.RESET}")
            
            # 避免重复处理同一个删除事件
            if path_str in self.processed_deletes:
                logger.debug(f"{Color.GRAY}[跳过] 重复的删除事件: {path}{Color.RESET}")
                return
                
            logger.info(f"{Color.CYAN}[检测到删除] {path}{Color.RESET}")
            
            # 标记为已处理
            self.processed_deletes.add(path_str)
            
            try:
                # 添加到事件队列，设置短延迟使删除优先处理
                current_time = time.time()
                self.engine.file_watcher.pending_events[path_str] = {
                    'timestamp': current_time - self.engine.file_watcher.debounce_delay + 0.1, 
                    'type': "deleted", 
                    'path': path
                }
                logger.info(f"{Color.YELLOW}[加入队列] 删除事件已加入队列: {path}{Color.RESET}")
            except Exception as e:
                logger.error(f"{Color.RED}[处理失败] 删除事件处理失败: {path}, 错误: {e}{Color.RESET}")
                # 从已处理集合中移除，以便下次重试
                self.processed_deletes.discard(path_str)

    def handle_delete_directly(self, path):
        """直接处理删除事件，绕过事件队列
        
        Args:
            path (Path): 被删除的文件路径
        """
        logger.info(f"{Color.YELLOW}[直接处理] 立即处理删除事件: {path}{Color.RESET}")
        try:
            self.engine.handle_file_event(path, "deleted")
        except Exception as e:
            logger.error(f"{Color.RED}[处理失败] 删除事件处理出错: {path}, 错误: {e}{Color.RESET}")


class FileWatcher:
    """监控文件系统变化"""
    
    def __init__(self, sync_engine):
        """初始化文件监控器
        
        Args:
            sync_engine: 同步引擎实例
        """
        self.sync_engine = sync_engine
        self.config = sync_engine.config
        self.md_dir = self.config.get_md_dir()
        self.ipynb_dir = self.config.get_ipynb_dir()
        self.observer = None
        self.ipynb_observer = None  # 为ipynb文件夹单独创建一个观察器
        self.handler = None  # 存储处理器引用
        self.ipynb_handler = None  # 存储ipynb处理器引用
        
        # 确保目录存在
        self.md_dir.mkdir(parents=True, exist_ok=True)
        if not self.ipynb_dir.exists():
            self.ipynb_dir.mkdir(parents=True, exist_ok=True)
        elif not self.ipynb_dir.is_dir():
            raise NotADirectoryError(f"{self.ipynb_dir} 已存在但不是目录！")
        
        # 事件队列，用于去抖动处理
        self.pending_events = defaultdict(lambda: {'timestamp': 0, 'type': None, 'path': None})
        self.debounce_delay = self.config.get('debounce_delay', 0.8)
        
        # 上次清理时间
        self.last_cleanup_time = time.time()
        self.cleanup_interval = 60  # 60秒清理一次
        
        # 文件状态缓存，用于轮询检查
        self.file_states = {}
        self.last_poll_time = time.time()
        self.poll_interval = 2.0  # 轮询间隔（秒）
        
        logger.info(f"{Color.BLUE}已初始化文件监控器, MD目录: {self.md_dir}, IPYNB目录: {self.ipynb_dir}{Color.RESET}")
    
    def start(self):
        """启动文件监控"""
        if self.observer:
            return
            
        # 创建事件处理器
        self.handler = SyncFileHandler(self.sync_engine)
        self.ipynb_handler = SyncFileHandler(self.sync_engine)  # 为ipynb创建单独的处理器
        
        # 为MD文件夹也使用轮询观察者，以确保在WSL环境中也能工作
        self.observer = PollingObserver()
        logger.info(f"{Color.GREEN}开始监控目录(轮询): {self.md_dir} (含子目录){Color.RESET}")
        self.observer.schedule(self.handler, str(self.md_dir), recursive=True)
        
        # 为IPYNB文件夹使用轮询观察者，以确保在WSL环境中也能工作
        self.ipynb_observer = PollingObserver()
        logger.info(f"{Color.GREEN}开始监控目录(轮询): {self.ipynb_dir} (含子目录){Color.RESET}")
        self.ipynb_observer.schedule(self.ipynb_handler, str(self.ipynb_dir), recursive=True)
        
        # 启动观察者
        self.observer.start()
        self.ipynb_observer.start()
        logger.info(f"{Color.BLUE}文件监控已启动{Color.RESET}")
        
        # 初始化文件状态
        self.scan_files_state()
    
    def stop(self):
        """停止文件监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            
        if self.ipynb_observer:
            self.ipynb_observer.stop()
            self.ipynb_observer.join()
            self.ipynb_observer = None
            
        logger.info(f"{Color.YELLOW}文件监控已停止{Color.RESET}")
    
    def scan_files_state(self):
        """扫描并记录所有文件的状态"""
        logger.debug(f"{Color.GRAY}[扫描] 开始扫描文件状态{Color.RESET}")
        
        # 扫描MD文件夹
        self.scan_directory_state(self.md_dir)
        
        # 扫描IPYNB文件夹
        self.scan_directory_state(self.ipynb_dir)
    
    def scan_directory_state(self, directory):
        """扫描目录中的文件状态
        
        Args:
            directory (Path): 要扫描的目录
        """
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.md') or file.endswith('.ipynb'):
                    try:
                        stat_info = os.stat(file_path)
                        self.file_states[file_path] = {
                            'mtime': stat_info.st_mtime,
                            'size': stat_info.st_size
                        }
                        logger.debug(f"{Color.GRAY}[扫描] 记录文件状态: {file_path}{Color.RESET}")
                    except Exception as e:
                        logger.error(f"{Color.RED}[错误] 获取文件状态失败: {file_path}, 错误: {e}{Color.RESET}")
    
    def check_files_changes(self):
        """检查文件是否有变化"""
        current_time = time.time()
        if current_time - self.last_poll_time < self.poll_interval:
            return
            
        self.last_poll_time = current_time
        logger.debug(f"{Color.GRAY}[轮询] 检查文件变化{Color.RESET}")
        
        # 检查ipynb目录的文件
        changed_files_ipynb = self.check_directory_changes(self.ipynb_dir)
        
        # 检查md目录的文件
        changed_files_md = self.check_directory_changes(self.md_dir)
        
        # 合并变化文件列表
        changed_files = changed_files_ipynb + changed_files_md
        
        # 处理变化的文件
        for file_path, change_type in changed_files:
            # 处理ipynb和md文件
            if file_path.endswith('.ipynb') or file_path.endswith('.md'):
                logger.info(f"{Color.GREEN}[检测变化] {change_type} 文件: {file_path}{Color.RESET}")
                # 创建一个合成事件
                event = FileSystemEvent(file_path)
                event.event_type = change_type
                event.is_directory = False
                
                # 根据文件类型选择合适的处理器
                handler = self.ipynb_handler if file_path.endswith('.ipynb') else self.handler
                
                # 手动触发处理器
                if change_type == 'modified':
                    handler.on_modified(event)
                elif change_type == 'created':
                    handler.on_created(event)
                elif change_type == 'deleted':
                    handler.on_deleted(event)
    
    def check_directory_changes(self, directory):
        """检查目录中的文件变化
        
        Args:
            directory (Path): 要检查的目录
            
        Returns:
            list: 变化的文件列表
        """
        changed_files = []
        current_files = {}
        
        # 扫描当前文件
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if file.endswith('.md') or file.endswith('.ipynb'):
                    try:
                        stat_info = os.stat(file_path)
                        current_files[file_path] = {
                            'mtime': stat_info.st_mtime,
                            'size': stat_info.st_size
                        }
                    except FileNotFoundError:
                        continue
        
        # 检查新增或修改的文件
        for file_path, state in current_files.items():
            if file_path not in self.file_states:
                changed_files.append((file_path, 'created'))
            elif state['mtime'] > self.file_states[file_path]['mtime'] or state['size'] != self.file_states[file_path]['size']:
                changed_files.append((file_path, 'modified'))
        
        # 检查删除的文件
        for file_path in list(self.file_states.keys()):
            if file_path.startswith(str(directory)) and file_path not in current_files:
                changed_files.append((file_path, 'deleted'))
                del self.file_states[file_path]
        
        # 更新状态缓存
        self.file_states.update(current_files)
        
        return changed_files
    
    def add_pending_event(self, file_path, event_type):
        """添加待处理事件到去抖动队列
        
        Args:
            file_path (Path): 文件路径
            event_type (str): 事件类型
        """
        path_str = str(file_path)
        current_time = time.time()
        
        # 检查这是Markdown还是Jupyter文件
        is_md = is_markdown_file(path_str)
        is_ipynb = is_notebook_file(path_str)
        
        if not (is_md or is_ipynb):
            logger.debug(f"{Color.GRAY}[忽略] 忽略非目标文件类型: {file_path}{Color.RESET}")
            return
        
        # 删除事件特殊处理，设置更低的延迟
        if event_type == "deleted":
            # 删除事件使用更短的延迟(几乎立即处理)
            self.pending_events[path_str] = {
                'timestamp': current_time - self.debounce_delay + 0.1,  # 几乎立即处理
                'type': event_type, 
                'path': file_path
            }
            logger.debug(f"{Color.YELLOW}[优先事件队列] {event_type:10s} {file_path} (优先处理){Color.RESET}")
        else:
            # 其他事件正常处理
            self.pending_events[path_str] = {
                'timestamp': current_time, 
                'type': event_type, 
                'path': file_path
            }
            logger.debug(f"{Color.GRAY}[事件队列] {event_type:10s} {file_path}{Color.RESET}")
    
    def cleanup_processed_deletes(self):
        """清理过期的已处理删除事件记录"""
        current_time = time.time()
        if current_time - self.last_cleanup_time > self.cleanup_interval and self.handler:
            logger.debug(f"{Color.GRAY}[清理] 清理过期的删除事件记录{Color.RESET}")
            if self.handler:
                self.handler.processed_deletes.clear()
            if self.ipynb_handler:
                self.ipynb_handler.processed_deletes.clear()
            self.last_cleanup_time = current_time
    
    def process_pending_events(self):
        """处理去抖动后的待处理事件"""
        current_time = time.time()
        processed_paths = []
        
        # 检查文件变化（基于轮询）
        self.check_files_changes()
        
        try:
            # 创建待处理事件的副本，避免在循环中修改原字典
            pending_events_copy = dict(self.pending_events)
            
            for path_str, event_info in pending_events_copy.items():
                # 只处理超过去抖动延迟的事件
                if current_time - event_info['timestamp'] >= self.debounce_delay:
                    path = event_info['path']
                    event_type = event_info['type']
                    
                    logger.debug(f"{Color.CYAN}[处理事件] {event_type:10s} {path}{Color.RESET}")
                    
                    try:
                        # 分别处理不同类型的事件
                        if event_type == "deleted":
                            logger.info(f"{Color.RED}[处理删除] 处理文件删除: {path}{Color.RESET}")
                            self.sync_engine.handle_file_deletion(path)
                        else:
                            logger.info(f"{Color.GREEN}[处理变更] 处理文件变更: {path}{Color.RESET}")
                            self.sync_engine.sync_file_if_needed(path)
                        
                        processed_paths.append(path_str)
                    except Exception as e:
                        logger.error(f"{Color.RED}[事件处理错误] 处理事件 {event_type} 失败: {path}, 错误: {e}{Color.RESET}")
                        import traceback
                        logger.debug(f"{Color.RED}[详细错误] {traceback.format_exc()}{Color.RESET}")
                        # 尽管出错，仍将其标记为已处理以避免无限重试
                        processed_paths.append(path_str)
            
            # 移除已处理的事件
            for path_str in processed_paths:
                if path_str in self.pending_events:  # 确保键存在再删除
                    self.pending_events.pop(path_str, None)
                
        except RuntimeError as e:
            logger.error(f"{Color.RED}[字典错误] 处理事件时字典发生变化: {e}{Color.RESET}")
            # 在发生字典大小变化错误时，简单清空待处理事件
            self.pending_events.clear()
        except Exception as e:
            logger.error(f"{Color.RED}[事件循环错误] 处理事件队列失败: {e}{Color.RESET}")
            import traceback
            logger.debug(f"{Color.RED}[详细错误] {traceback.format_exc()}{Color.RESET}")
            
        # 定期清理过期的已处理删除事件记录
        self.cleanup_processed_deletes()
    
    def should_sync_file(self, file_path):
        """检查文件是否应该同步
        
        Args:
            file_path (Path): 文件路径
            
        Returns:
            bool: 是否应该同步
        """
        # 检查文件是否存在
        if not file_path.exists():
            return False
            
        # 检查是否是隐藏文件或临时文件
        filename = file_path.name
        if filename.startswith('.') or filename.startswith('~') or filename.endswith('.tmp'):
            return False
            
        # 检查扩展名
        if is_markdown_file(str(file_path)) or is_notebook_file(str(file_path)):
            return True
            
        return False
    
    def __del__(self):
        """析构函数，确保停止监控"""
        self.stop()
