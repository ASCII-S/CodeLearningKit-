"""
配置管理模块

负责读取和管理配置，提供默认配置及用户自定义配置
"""

import os
import json
from pathlib import Path

from .utils import logger, Color

class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config_path=None):
        """初始化配置管理器
        
        Args:
            config_path (str, optional): 配置文件路径
        """
        # 设置默认配置路径
        if config_path is None:
            self.config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        else:
            self.config_path = config_path
            
        # 默认配置
        self.default_config = {
            # 目录配置
            'md_dir': str(Path.cwd() / 'mdtest'),  # Markdown文件目录
            'ipynb_dir': str(Path.cwd() / 'ipynbtest'),  # Jupyter Notebook文件目录
            
            # 文件同步配置
            'md_extensions': ['.md'],  # Markdown文件扩展名
            'ipynb_extensions': ['.ipynb'],  # Jupyter Notebook文件扩展名
            'ignore_patterns': [  # 忽略的文件/目录模式
                '.*',  # 所有以.开头的隐藏文件/目录
                '__pycache__',
                '.ipynb_checkpoints',
                '.git',
                '.vscode',
                'node_modules',
            ],
            
            # 监视配置
            'debounce_delay': 0.8,  # 去抖动延迟（秒）
            'watch_interval': 1.0,  # 监视间隔（秒）
            
            # 同步配置
            'sync_on_start': True,  # 启动时执行同步
            'bidirectional_sync': True,  # 双向同步
            'conflict_resolution': 'newer',  # 冲突解决策略: newer, md, ipynb
            'delete_orphaned': True,  # 是否删除孤立文件
            
            # 转换配置
            'default_language': 'python',  # 默认代码块语言
            'preserve_output': True,  # 保留输出结果
            'execution_count': True,  # 保留执行计数
            
            # 日志级别设置
            'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        }
        
        # 加载配置
        self.config = self.load_config()
        
    def load_config(self):
        """加载配置文件
        
        Returns:
            dict: 加载的配置
        """
        # 合并配置
        config = self.default_config.copy()
        
        # 如果存在配置文件，则加载
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    config.update(user_config)
                logger.info(f"{Color.GREEN}已加载配置文件: {self.config_path}{Color.RESET}")
            except Exception as e:
                logger.error(f"{Color.RED}加载配置文件失败: {e}{Color.RESET}")
        else:
            logger.warning(f"{Color.YELLOW}配置文件不存在，使用默认配置: {self.config_path}{Color.RESET}")
            self.save_config(config)  # 保存默认配置
            
        return config
    
    def save_config(self, config=None):
        """保存配置到文件
        
        Args:
            config (dict, optional): 要保存的配置，默认为当前配置
        """
        if config is None:
            config = self.config
            
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logger.info(f"{Color.GREEN}已保存配置到: {self.config_path}{Color.RESET}")
        except Exception as e:
            logger.error(f"{Color.RED}保存配置失败: {e}{Color.RESET}")
    
    def get(self, key, default=None):
        """获取配置项
        
        Args:
            key (str): 配置项键名
            default: 默认值，如果配置项不存在
            
        Returns:
            配置项的值
        """
        return self.config.get(key, default)
    
    def set(self, key, value):
        """设置配置项
        
        Args:
            key (str): 配置项键名
            value: 配置项的值
        """
        self.config[key] = value
        
    def update(self, config_dict):
        """更新多个配置项
        
        Args:
            config_dict (dict): 包含配置项的字典
        """
        self.config.update(config_dict)
    
    def get_md_dir(self):
        """获取Markdown目录的Path对象
        
        Returns:
            Path: Markdown目录
        """
        return Path(self.get('md_dir'))
    
    def get_ipynb_dir(self):
        """获取Jupyter Notebook目录的Path对象
        
        Returns:
            Path: Jupyter Notebook目录
        """
        return Path(self.get('ipynb_dir'))
