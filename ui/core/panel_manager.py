import importlib
import os
import inspect
from tkinter import ttk
import tkinter as tk

from ui.core.IPanel import IPanel
class PanelManager:
    current_panel:IPanel
    def __init__(self, master, panel_dir):
        self.master = master
        self.panel_dir = panel_dir
        self.panels = {}
        self.current_panel:IPanel = None
        
        # 加载所有面板
        self.load_panels()
        
    def load_panels(self):
        """从指定目录加载所有面板"""
        # 获取目录下所有Python文件
        panel_files = [
            f for f in os.listdir(self.panel_dir.replace('.','/'))
            if f.endswith('.py') and f != '__init__.py'
        ]
        
        # 导入每个面板模块并实例化面板类
        for file in panel_files:
            module_name = file[:-3]  # 移除.py
            try:
                module = importlib.import_module(f"{self.panel_dir}.{module_name}")
                
                # 查找模块中的所有类
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # 确保类是在当前模块中定义的，而不是导入的
                    if obj.__module__ == f"{self.panel_dir}.{module_name}":
                        panel_instance = obj(self.master)
                        self.panels[module_name] = panel_instance
                        break
            except Exception as e:
                print(f"Error loading panel {module_name}: {e} \n {e.args}")
    
    def get_panel_names(self):
        """获取所有面板名称"""
        return list(self.panels.keys())
    
    def show_panel(self, panel_name):
        """显示指定的面板"""
        if panel_name not in self.panels:
            return
            
        # 隐藏当前面板
        if self.current_panel:
            self.current_panel.get_frame().pack_forget()
            
        # 显示新面板
        self.current_panel = self.panels[panel_name]
        self.current_panel.get_frame().pack(fill=tk.BOTH, expand=True)