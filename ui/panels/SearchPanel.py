import tkinter as tk
from tkinter import ttk, messagebox
from db.sqlite import SymbolDatabase
from embedding_util.vector_store import query_symbols
from ui.core.IPanel import IPanel
from typing import List, Dict, Any
import ui.core.i18n as i18n 

locale=i18n.display_dict.get("SEARCH_PANEL")

class SearchPanel(IPanel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.db = SymbolDatabase('symbols.db')  # 使用默认数据库路径
        self.frame = ttk.Frame(self.master)
        self.current_results = []
        
        # 国际化字符串字典
        self.i18n = locale
        
        self.create_widgets()
        self.setup_layout()

    def create_widgets(self):
        """创建所有UI组件"""
        # 搜索区域
        self.search_frame = ttk.Frame(self.frame)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            self.search_frame, 
            textvariable=self.search_var,
            width=40
        )
        self.search_entry.bind('<Return>', lambda e: self.do_search())
        
        self.search_button = ttk.Button(
            self.search_frame,
            text=self.i18n['search'],
            command=self.do_search
        )
        
        # 搜索选项
        self.search_type = tk.StringVar(value="text")
        self.text_search_radio = ttk.Radiobutton(
            self.search_frame,
            text=self.i18n['text_search'],
            variable=self.search_type,
            value="text"
        )
        self.semantic_search_radio = ttk.Radiobutton(
            self.search_frame,
            text=self.i18n['semantic_search'],
            variable=self.search_type,
            value="semantic"
        )
        
        # 结果列表
        self.result_tree = ttk.Treeview(
            self.frame,
            columns=('type', 'location', 'doc'),
            selectmode='browse',
            height=15
        )
        self.result_tree.heading('#0', text=self.i18n['name'])
        self.result_tree.heading('type', text=self.i18n['type'])
        self.result_tree.heading('location', text=self.i18n['location'])
        self.result_tree.column('type', width=100)
        self.result_tree.column('location', width=200)
        
        # 详情面板
        self.detail_text = tk.Text(
            self.frame,
            wrap='word',
            height=10,
            state='disabled'
        )
        self.detail_scroll = ttk.Scrollbar(
            self.frame,
            command=self.detail_text.yview
        )
        self.detail_text.configure(yscrollcommand=self.detail_scroll.set)

    def setup_layout(self):
        """布局组件"""
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        
        # 搜索区域布局
        self.search_frame.grid(row=0, column=0, sticky='ew', padx=5, pady=5)
        self.search_entry.grid(row=0, column=0, padx=5)
        self.search_button.grid(row=0, column=1, padx=5)
        self.text_search_radio.grid(row=1, column=0, sticky='w')
        self.semantic_search_radio.grid(row=1, column=1, sticky='w')
        
        # 结果和详情布局
        self.result_tree.grid(row=1, column=0, sticky='nsew', padx=5)
        self.detail_text.grid(row=2, column=0, sticky='ew', padx=5, pady=5)
        self.detail_scroll.grid(row=2, column=1, sticky='ns')

    def do_search(self):
        """执行搜索操作"""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning(
                self.i18n['prompt'], 
                self.i18n['empty_query']
            )
            return
        
        try:
            if self.search_type.get() == "text":
                # 文本搜索（支持模糊匹配）
                self.current_results = self.db.search_symbols_by_name(query)
            else:
                # 语义向量搜索
                self.current_results = query_symbols(query, top_k=10)
            
            self.display_results()
        except Exception as e:
            messagebox.showerror(
                self.i18n['error'], 
                self.i18n['search_error'].format(error=str(e))
            )

    def display_results(self):
        """显示搜索结果"""
        self.result_tree.delete(*self.result_tree.get_children())
        
        # 收集所有可能的字段名（按字母排序保证列顺序一致）
        all_keys = sorted({key for symbol in self.current_results for key in symbol.keys()})

        # 配置Treeview列（假设第一个字段是symbol_name作为主列）
        self.result_tree["columns"] = all_keys[:]  # 排除主列
        # self.result_tree.heading("#0", text=all_keys[0])  # 主列标题
        # self.result_tree.column("#0", width=150)  # 主列宽度

        # 添加其他列
        for col in all_keys[:]:
            self.result_tree.heading(col, text=col)
            self.result_tree.column(col, width=100, stretch=True)  # 可拉伸列

        # 插入数据
        for i,symbol in enumerate(self.current_results):
            # 按all_keys顺序获取值，未找到字段则填空字符串
            row_values = [symbol.get(key, '') for key in all_keys[:]]
            
            self.result_tree.insert(
                '', 'end',
                text=str(i),  # 主列显示symbol_name
                values=tuple(row_values),  # 所有其他字段值
                # tags=(symbol.get('symbol_type', '')),
            )
                
        # 绑定选择事件
        self.result_tree.bind('<<TreeviewSelect>>', self.show_details)

    def show_details(self, event):
        """显示选中符号的详细信息"""
        selected = self.result_tree.focus()
        if not selected:
            return
            
        item = self.result_tree.item(selected)
        symbol_index = item['text']
        symbol_info = self.current_results[int(symbol_index)]
        if not symbol_info:
            return
            
        self.detail_text.config(state='normal')
        self.detail_text.delete(1.0, tk.END)
        
        # 生成详情信息
        details = [
            f"{self.i18n['details']['name']}: {symbol_info.get('symbol_name', 'N/A')}",
            f"{self.i18n['details']['type']}: {symbol_info.get('symbol_type', 'N/A')}",
            f"{self.i18n['details']['location']}: {symbol_info.get('file_path', 'N/A')}",
            f"{self.i18n['details']['line']}: {symbol_info.get('lineno', 'N/A')}",
            self.i18n['details']['documentation'],
            bytes(symbol_info.get('doc_text', self.i18n['details']['no_doc'])).decode() 
            if isinstance(symbol_info.get('doc_text'), bytes) 
            else symbol_info.get('doc_text', self.i18n['details']['no_doc'])
        ]

        # 自动添加其他字段
        details_auto = [
            f"{key}: {symbol_info.get(key, 'N/A')}" 
            for key in symbol_info.keys() 
            if key not in ['symbol_name', 'symbol_type', 'file_path', 'lineno', 'doc_text']
        ]
        details.extend(details_auto)

        # 特殊类型处理
        if symbol_info.get('symbol_type') == 'class':
            details.append(self.i18n['details']['members'])
            members = self.db.get_class_members(symbol_info.get('symbol_name', 'N/A'))
            for m in members:
                details.append(
                    f"- {self.i18n['messages']['class_members'].format(name=m['symbol_name'], type=m['symbol_type'])}"
                )
        
        self.detail_text.insert(tk.END, '\n'.join(details))
        self.detail_text.config(state='disabled')

    def _truncate_doc(self, doc: str, max_len: int = 50) -> str:
        """截断过长的文档字符串"""
        return (doc[:max_len] + '...') if len(doc) > max_len else doc

    def get_frame(self) -> tk.Widget:
        """实现IPanel接口，返回主框架"""
        return self.frame

    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'db'):
            self.db.close()