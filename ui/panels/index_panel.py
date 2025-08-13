import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from ui.functions.vector_store import store_symbol
from db.Sqlite import SymbolDatabase
from symbol.file_utils import scan_directory
from symbol.symbols import find_exported_symbols_with_doc, flatten_class_symbols
import ui.core.i18n as i18n
from ui.functions.config import SYMBOLS_DB_FILE_PATH 

locale=i18n.display_dict.get("INDEXING_PANEL")
class IndexingPanel:
    def __init__(self, master):
        global locale
        locale=i18n.display_dict.get("INDEXING_PANEL")
        self.master = master
        self.frame = ttk.Frame(self.master)
        
        # 标题
        self.title_label = ttk.Label(
            self.frame, 
            text=locale["TITLE_MAIN"], 
            font=('Helvetica', 14, 'bold')
        )
        self.title_label.pack(pady=10)
        
        # 目录选择部分
        self.dir_frame = ttk.LabelFrame(
            self.frame, 
            text=locale["LABEL_DIR_SETTINGS"], 
            padding=10
        )
        self.dir_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.dir_label = ttk.Label(
            self.dir_frame, 
            text=locale["LABEL_CODE_DIRECTORY"]
        )
        self.dir_label.grid(row=0, column=0, sticky=tk.W)
        
        self.dir_entry = ttk.Entry(self.dir_frame, width=50)
        self.dir_entry.grid(row=1, column=0, sticky=tk.EW)
        
        self.browse_button = ttk.Button(
            self.dir_frame, 
            text=locale["BUTTON_BROWSE"], 
            command=self.browse_directory
        )
        self.browse_button.grid(row=1, column=1, padx=5)
        
        # 文件过滤部分
        self.filter_frame = ttk.LabelFrame(
            self.frame, 
            text=locale["LABEL_FILE_FILTER"], 
            padding=10
        )
        self.filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.filter_label = ttk.Label(
            self.filter_frame, 
            text=locale["LABEL_FILE_EXTENSIONS"]
        )
        self.filter_label.grid(row=0, column=0, sticky=tk.W)
        
        self.filter_entry = ttk.Entry(self.filter_frame, width=50)
        self.filter_entry.insert(0, locale["DEFAULT_FILE_EXTENSION"])
        self.filter_entry.grid(row=1, column=0, sticky=tk.EW)
        
        # 索引选项
        self.options_frame = ttk.LabelFrame(
            self.frame, 
            text=locale["LABEL_INDEX_OPTIONS"], 
            padding=10
        )
        self.options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.include_docs = tk.BooleanVar(value=True)
        self.docs_check = ttk.Checkbutton(
            self.options_frame, 
            text=locale["CHECKBOX_INCLUDE_DOCSTRINGS"],
            variable=self.include_docs
        )
        self.docs_check.grid(row=0, column=0, sticky=tk.W)
        
        # 进度条
        self.progress_frame = ttk.Frame(self.frame)
        self.progress_frame.pack(fill=tk.X, padx=5, pady=10)
        
        self.progress = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X)
        
        self.status_label = ttk.Label(
            self.progress_frame, 
            text=locale["STATUS_READY"]
        )
        self.status_label.pack()
        
        # 操作按钮
        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.pack(pady=10)
        
        self.index_button = ttk.Button(
            self.button_frame, 
            text=locale["BUTTON_START_INDEXING"], 
            command=self.start_indexing
        )
        self.index_button.pack(side=tk.LEFT, padx=5)
        
        self.cancel_button = ttk.Button(
            self.button_frame, 
            text=locale["BUTTON_CANCEL"], 
            command=self.cancel_indexing
        )
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # 配置网格权重
        self.dir_frame.columnconfigure(0, weight=1)
        self.filter_frame.columnconfigure(0, weight=1)
        
        # 初始化状态
        self.is_indexing = False
        
    def browse_directory(self):
        """打开目录选择对话框"""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, dir_path)
    
    def start_indexing(self):
        """开始索引过程"""
        if self.is_indexing:
            return
            
        dir_path = self.dir_entry.get()
        file_filter = self.filter_entry.get()
        
        if not dir_path:
            messagebox.showerror(
                locale["TITLE_ERROR"],
                locale["MESSAGE_NO_DIRECTORY_SELECTED"]
            )
            return
            
        try:
            self.is_indexing = True
            self.index_button.config(state=tk.DISABLED)
            self.status_label.config(text=locale["STATUS_SCANNING_DIRECTORY"])
            self.master.update()
            
            # 扫描目录
            files = scan_directory(dir_path, file_filter)
            total_files = len(files)
            
            if not total_files:
                messagebox.showinfo(
                    locale["TITLE_INFO"],
                    locale["MESSAGE_NO_MATCHING_FILES"]
                )
                return
                
            self.progress["maximum"] = total_files
            self.progress["value"] = 0
            
            # 处理每个文件
            for i, file_path in enumerate(files):
                if not self.is_indexing:
                    break
                    
                # 更新状态文本
                status_text = locale["STATUS_PROCESSING_FILE"].format(
                    filename=Path(file_path).name,
                    current=i+1,
                    total=total_files
                )
                self.status_label.config(text=status_text)
                self.progress["value"] = i + 1
                self.master.update()
                
                try:
                    # 提取符号
                    symbols = find_exported_symbols_with_doc(file_path, self.include_docs.get())
                    flatten_class_symbols(symbols)
                    
                    vector_ids=[]
                    # 存储到向量数据库
                    for name, detail in symbols:
                        result = store_symbol(detail, name)
                        if result.get("status") == "success":
                            # 将存储的符号信息添加到向量ID列表
                            vector_ids.append((name, result["id"]))
                        else:
                            print(locale["ERROR_PROCESSING_FILE"].format(
                                file=file_path, 
                                error= name
                            ))

                    # 存储到数据库
                    relative_path = Path(file_path).relative_to(dir_path).as_posix()
                    with SymbolDatabase(SYMBOLS_DB_FILE_PATH) as db:
                        db.upsert_file_symbols(file_path, symbols,vector_ids, relative_path)
                        
                except Exception as e:
                    # 记录错误但不中断整个索引过程
                    print(locale["ERROR_PROCESSING_FILE"].format(
                        file=file_path, 
                        error=str(e.with_traceback(e.args)))
                    )
            
            if self.is_indexing:
                messagebox.showinfo(
                    locale["TITLE_COMPLETE"],
                    locale["MESSAGE_INDEXING_SUCCESS"].format(count=total_files)
                )
                self.status_label.config(text=locale["STATUS_INDEXING_COMPLETE"])
            
        except Exception as e:
            messagebox.showerror(
                locale["TITLE_ERROR"],
                locale["ERROR_INDEXING_FAILED"].format(error=str(e))
            )
            self.status_label.config(text=locale["STATUS_INDEXING_ERROR"])
            
        finally:
            self.is_indexing = False
            self.index_button.config(state=tk.NORMAL)
    
    def cancel_indexing(self):
        """取消索引过程"""
        if self.is_indexing:
            self.is_indexing = False
            self.status_label.config(text=locale["STATUS_INDEXING_CANCELED"])
    
    def get_frame(self):
        """返回面板框架"""
        return self.frame