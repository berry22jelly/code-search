from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
from typing import Optional
from ui.functions.doc_function import analyze_and_export_symbols
from ui.core.IPanel import IPanel
import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional

class SymbolAnalyzerPanel(IPanel):
    """符号分析器面板，用于展示代码符号分析结果"""
    
    def __init__(self, master: tk.Widget):
        """初始化面板
        
        参数:
            master (tk.Widget): 父容器部件
        """
        self.master = master
        self._directory_path: Optional[str] = None
        self._file_pattern: str = "*.py"  # 默认文件模式
        
        # 创建主框架
        self.frame = ttk.Frame(master, padding="10")
        
        # 创建控件
        self._create_widgets()
        
    def get_frame(self) -> tk.Widget:
        """获取面板的主框架
        
        返回:
            tk.Widget: 面板的主框架部件
        """
        return self.frame
    
    def _create_widgets(self):
        """创建面板内的所有控件"""
        # 顶部控制面板
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 目录选择部分
        dir_frame = ttk.Frame(control_frame)
        dir_frame.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        ttk.Label(dir_frame, text="目标目录:").pack(side=tk.LEFT)
        self.dir_entry = ttk.Entry(dir_frame)
        self.dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        dir_btn = ttk.Button(
            dir_frame, 
            text="浏览...", 
            command=self._select_directory
        )
        dir_btn.pack(side=tk.LEFT)
        
        # 文件模式选择部分
        pattern_frame = ttk.Frame(control_frame)
        pattern_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(pattern_frame, text="文件模式:").pack(side=tk.LEFT)
        self.pattern_entry = ttk.Entry(pattern_frame, width=15)
        self.pattern_entry.insert(0, self._file_pattern)
        self.pattern_entry.pack(side=tk.LEFT, padx=5)
        
        # 分析按钮
        analyze_btn = ttk.Button(
            control_frame,
            text="分析符号",
            command=self._analyze_symbols
        )
        analyze_btn.pack(side=tk.RIGHT)
        
        # 结果显示区域
        result_frame = ttk.Frame(self.frame)
        result_frame.pack(expand=True, fill=tk.BOTH)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(result_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 文本框用于显示结果
        self.result_text = tk.Text(
            result_frame,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set,
            font=('Consolas', 10)  # 使用等宽字体更好看
        )
        self.result_text.pack(expand=True, fill=tk.BOTH)
        
        scrollbar.config(command=self.result_text.yview)
        
        # 禁用文本框的编辑功能
        self.result_text.config(state=tk.DISABLED)
    
    def _select_directory(self):
        """选择目录"""
        directory = filedialog.askdirectory()
        if directory:
            self._directory_path = directory
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
    
    def _analyze_symbols(self):
        """分析符号并显示结果"""
        if not self._directory_path:
            tk.messagebox.showerror("错误", "请先选择目录")
            return
            
        # 获取用户输入的文件模式
        self._file_pattern = self.pattern_entry.get().strip()
        if not self._file_pattern:
            self._file_pattern = "*"  # 默认匹配所有文件
            
        try:
            # 调用分析函数，传入文件模式
            result = analyze_and_export_symbols(self._directory_path, self._file_pattern)
            
            # 更新文本框
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, result)
            self.result_text.config(state=tk.DISABLED)
            
        except Exception as e:
            tk.messagebox.showerror("分析错误", f"分析过程中发生错误:\n{str(e)}")