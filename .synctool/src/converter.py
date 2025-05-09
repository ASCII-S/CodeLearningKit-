"""
转换器模块

负责MD和IPYNB文件之间的转换，识别MD代码语言，处理元数据
"""

import os
import re
import json
import uuid
from pathlib import Path
from datetime import datetime

from .utils import logger, Color, ensure_dir_exists

class Converter:
    """文件转换器类"""
    
    def __init__(self, config_manager):
        """初始化转换器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.default_language = self.config.get('default_language', 'python')
        self.preserve_output = self.config.get('preserve_output', True)
        self.execution_count = self.config.get('execution_count', True)
        
    def md_to_ipynb(self, md_path, ipynb_path=None):
        """将Markdown文件转换为Jupyter Notebook
        
        Args:
            md_path (str or Path): Markdown文件路径
            ipynb_path (str or Path, optional): 输出的Jupyter Notebook路径
            
        Returns:
            str or Path: 生成的Jupyter Notebook路径
        """
        md_path = Path(md_path)
        
        # 如果未指定输出路径，则使用与输入相同的文件名，但扩展名为.ipynb
        if ipynb_path is None:
            ipynb_path = md_path.with_suffix('.ipynb')
        else:
            ipynb_path = Path(ipynb_path)
        
        logger.info(f"{Color.GREEN}转换 MD → IPYNB: {md_path} → {ipynb_path}{Color.RESET}")
        
        # 确保目标目录存在
        ensure_dir_exists(ipynb_path.parent)
        
        try:
            # 读取Markdown文件内容
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 获取源文件的访问时间和修改时间
            source_stat = os.stat(md_path)
            access_time = source_stat.st_atime
            modify_time = source_stat.st_mtime
            
            # 初始化Notebook结构
            notebook = {
                'cells': [],
                'metadata': {
                    'kernelspec': {
                        'display_name': 'Python 3',
                        'language': 'python',
                        'name': 'python3'
                    },
                    'language_info': {
                        'codemirror_mode': {
                            'name': 'ipython',
                            'version': 3
                        },
                        'file_extension': '.py',
                        'mimetype': 'text/x-python',
                        'name': 'python',
                        'nbconvert_exporter': 'python',
                        'pygments_lexer': 'ipython3',
                        'version': '3.8.0'
                    }
                },
                'nbformat': 4,
                'nbformat_minor': 4
            }
            
            # 解析Markdown内容，创建cells
            cells = self.parse_md_to_cells(md_content)
            notebook['cells'] = cells
            
            # 写入Jupyter Notebook文件
            with open(ipynb_path, 'w', encoding='utf-8') as f:
                json.dump(notebook, f, indent=2, ensure_ascii=False)
            
            # 设置目标文件的时间戳与源文件一致
            os.utime(ipynb_path, (access_time, modify_time))
            logger.debug(f"{Color.BLUE}[时间戳同步] {ipynb_path} 的时间戳已与 {md_path} 同步{Color.RESET}")
            
            logger.info(f"{Color.BLUE}转换成功: {ipynb_path}{Color.RESET}")
            return ipynb_path
            
        except Exception as e:
            logger.error(f"{Color.RED}转换失败 MD → IPYNB: {md_path} → {ipynb_path}, 错误: {e}{Color.RESET}")
            raise
    
    def ipynb_to_md(self, ipynb_path, md_path=None):
        """将Jupyter Notebook转换为Markdown
        
        Args:
            ipynb_path (str or Path): Jupyter Notebook路径
            md_path (str or Path, optional): 输出的Markdown路径
            
        Returns:
            str or Path: 生成的Markdown路径
        """
        ipynb_path = Path(ipynb_path)
        
        # 如果未指定输出路径，则使用与输入相同的文件名，但扩展名为.md
        if md_path is None:
            md_path = ipynb_path.with_suffix('.md')
        else:
            md_path = Path(md_path)
        
        logger.info(f"{Color.GREEN}转换 IPYNB → MD: {ipynb_path} → {md_path}{Color.RESET}")
        
        # 确保目标目录存在
        ensure_dir_exists(md_path.parent)
        
        try:
            # 获取源文件的访问时间和修改时间
            source_stat = os.stat(ipynb_path)
            access_time = source_stat.st_atime
            modify_time = source_stat.st_mtime
            
            # 检查文件大小
            if ipynb_path.stat().st_size == 0:
                logger.warning(f"{Color.YELLOW}IPYNB文件为空: {ipynb_path}{Color.RESET}")
                # 创建一个空的Markdown文件
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write('')
                # 设置目标文件的时间戳与源文件一致
                os.utime(md_path, (access_time, modify_time))
                logger.debug(f"{Color.BLUE}[时间戳同步] {md_path} 的时间戳已与 {ipynb_path} 同步{Color.RESET}")
                logger.info(f"{Color.BLUE}已创建空的MD文件: {md_path}{Color.RESET}")
                return md_path
            
            # 读取Jupyter Notebook文件内容
            try:
                with open(ipynb_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        # 处理空内容但文件不为0字节的情况
                        logger.warning(f"{Color.YELLOW}IPYNB文件内容为空: {ipynb_path}{Color.RESET}")
                        with open(md_path, 'w', encoding='utf-8') as mf:
                            mf.write('')
                        # 设置目标文件的时间戳与源文件一致
                        os.utime(md_path, (access_time, modify_time))
                        logger.debug(f"{Color.BLUE}[时间戳同步] {md_path} 的时间戳已与 {ipynb_path} 同步{Color.RESET}")
                        logger.info(f"{Color.BLUE}已创建空的MD文件: {md_path}{Color.RESET}")
                        return md_path
                    
                    notebook = json.loads(content)
            except json.JSONDecodeError as je:
                logger.error(f"{Color.RED}IPYNB文件不是有效的JSON格式: {ipynb_path}, 错误: {je}{Color.RESET}")
                # 创建一个包含错误信息的Markdown文件
                with open(md_path, 'w', encoding='utf-8') as f:
                    f.write(f"# 注意：原IPYNB文件格式有误\n\n原文件路径：{ipynb_path}\n\n错误信息：{je}")
                # 设置目标文件的时间戳与源文件一致
                os.utime(md_path, (access_time, modify_time))
                logger.debug(f"{Color.BLUE}[时间戳同步] {md_path} 的时间戳已与 {ipynb_path} 同步{Color.RESET}")
                logger.info(f"{Color.BLUE}已创建包含错误信息的MD文件: {md_path}{Color.RESET}")
                return md_path
            
            # 将Notebook转换为Markdown
            md_content = self.convert_notebook_to_md(notebook)
            
            # 写入Markdown文件
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            # 设置目标文件的时间戳与源文件一致
            os.utime(md_path, (access_time, modify_time))
            logger.debug(f"{Color.BLUE}[时间戳同步] {md_path} 的时间戳已与 {ipynb_path} 同步{Color.RESET}")
            
            logger.info(f"{Color.BLUE}转换成功: {md_path}{Color.RESET}")
            return md_path
            
        except Exception as e:
            logger.error(f"{Color.RED}转换失败 IPYNB → MD: {ipynb_path} → {md_path}, 错误: {e}{Color.RESET}")
            raise
    
    def parse_md_to_cells(self, md_content):
        """解析Markdown内容，创建Jupyter Notebook单元格
        
        Args:
            md_content (str): Markdown内容
            
        Returns:
            list: Jupyter Notebook单元格列表
        """
        cells = []
        
        # 使用正则表达式查找代码块和普通文本
        pattern = r'```(\w*)([\s\S]*?)```'
        
        # 分割文本
        parts = re.split(pattern, md_content)
        
        # 初始位置
        current_pos = 0
        
        # 处理每个部分
        i = 0
        while i < len(parts):
            if i % 3 == 0:
                # 这是普通文本部分
                text = parts[i]
                if text.strip():
                    cells.append({
                        'cell_type': 'markdown',
                        'metadata': {},
                        'source': self.prepare_cell_source(text)
                    })
                i += 1
            else:
                # 这是代码块部分
                lang = parts[i].strip() or self.default_language
                code = parts[i + 1]
                
                # 创建代码单元格
                cell = {
                    'cell_type': 'code',
                    'execution_count': None,
                    'metadata': {
                        'trusted': True
                    },
                    'source': self.prepare_cell_source(code),
                    'outputs': []
                }
                
                # 设置语言
                if lang == 'python' or lang == 'py':
                    pass  # 默认已经设置为Python
                else:
                    cell['metadata']['language'] = lang
                
                cells.append(cell)
                i += 2
        
        return cells
    
    def convert_notebook_to_md(self, notebook):
        """将Jupyter Notebook转换为Markdown
        
        Args:
            notebook (dict): Jupyter Notebook对象
            
        Returns:
            str: Markdown内容
        """
        md_lines = []
        
        # 从notebook全局元数据中获取语言信息
        notebook_language = self.default_language  # 默认语言
        
        # 优先从language_info中获取语言名称
        lang_info = notebook.get('metadata', {}).get('language_info', {})
        if 'name' in lang_info:
            notebook_language = lang_info['name'].lower()
            # 特殊情况处理，某些语言在Markdown中的标识与Jupyter中不同
            if notebook_language == 'c++':
                notebook_language = 'cpp'
        
        # 如果language_info中没有找到，尝试从kernelspec获取
        elif 'kernelspec' in notebook.get('metadata', {}):
            kernelspec = notebook.get('metadata', {}).get('kernelspec', {})
            if 'language' in kernelspec:
                kernel_language = kernelspec['language'].lower()
                # 处理特殊情况
                if 'c++' in kernel_language:
                    notebook_language = 'cpp'
                else:
                    notebook_language = kernel_language
        
        logger.debug(f"{Color.BLUE}[语言检测] 从Notebook获取的语言: {notebook_language}{Color.RESET}")
        
        # 处理每个单元格
        for cell in notebook.get('cells', []):
            cell_type = cell.get('cell_type', '')
            source = cell.get('source', [])
            
            # 确保source是字符串列表
            if isinstance(source, str):
                source = [source]
            
            # 合并source为一个字符串
            source_text = ''.join(source)
            
            if cell_type == 'markdown':
                # 添加Markdown单元格内容
                md_lines.append(source_text)
                
            elif cell_type == 'code':
                # 先尝试从单元格元数据获取语言，如果没有则使用全局语言
                language = cell.get('metadata', {}).get('language', notebook_language)
                
                # 添加代码块
                md_lines.append(f'```{language}')
                md_lines.append(source_text)
                
                # 如果配置了保留输出并且有输出
                if self.preserve_output and 'outputs' in cell and cell['outputs']:
                    outputs = []
                    for output in cell['outputs']:
                        output_type = output.get('output_type', '')
                        
                        if output_type == 'stream':
                            name = output.get('name', 'stdout')
                            text = output.get('text', [])
                            if isinstance(text, list):
                                text = ''.join(text)
                            outputs.append(f"# {name}:\n# {text.replace(chr(10), chr(10)+'# ')}")
                            
                        elif output_type in ('execute_result', 'display_data'):
                            if 'data' in output:
                                data = output['data']
                                if 'text/plain' in data:
                                    text = data['text/plain']
                                    if isinstance(text, list):
                                        text = ''.join(text)
                                    outputs.append(f"# Output:\n# {text.replace(chr(10), chr(10)+'# ')}")
                        
                        elif output_type == 'error':
                            ename = output.get('ename', '')
                            evalue = output.get('evalue', '')
                            outputs.append(f"# Error: {ename}: {evalue}")
                    
                    if outputs:
                        md_lines.append('\n'.join(outputs))
                
                md_lines.append('```')
        
        return '\n\n'.join(md_lines)
    
    def prepare_cell_source(self, text):
        """准备单元格源代码格式
        
        Args:
            text (str): 源代码文本
            
        Returns:
            list: 处理后的源代码列表
        """
        # 分割为行
        lines = text.split('\n')
        
        # 添加换行符
        source = []
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                source.append(line + '\n')
            else:
                if line:  # 最后一行，如果不为空，则不添加换行符
                    source.append(line)
        
        return source
    
    def detect_code_language(self, code_block):
        """检测代码块的语言
        
        Args:
            code_block (str): 代码块内容
            
        Returns:
            str: 推测的语言
        """
        # 简单的语言检测逻辑
        # 未来可以扩展为更复杂的语言检测
        
        if not code_block.strip():
            return self.default_language
            
        # Python特征
        if re.search(r'import\s+[\w.]+|def\s+\w+\s*\(|class\s+\w+\s*:', code_block):
            return 'python'
            
        # JavaScript特征
        if re.search(r'var\s+\w+|let\s+\w+|const\s+\w+|function\s+\w+\s*\(|=>\s*{', code_block):
            return 'javascript'
            
        # Java特征
        if re.search(r'public\s+class|private\s+\w+|protected\s+\w+', code_block):
            return 'java'
            
        # C/C++特征
        if re.search(r'#include\s+[<"]|int\s+main\s*\(', code_block):
            return 'cpp'
            
        # Bash特征
        if re.search(r'^#!/bin/bash|^\s*for\s+\w+\s+in\s+|^\s*if\s+\[\[', code_block):
            return 'bash'
            
        # 默认返回Python
        return self.default_language
