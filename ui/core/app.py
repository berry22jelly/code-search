import tkinter as tk
from tkinter import ttk
from .panel_manager import PanelManager

class DynamicPanelApp(tk.Tk):
    def __init__(self, panel_dir="panels"):
        super().__init__()
        self.title("Dynamic Panel Loader")
        self.geometry("800x600")
        
        # 创建主容器
        self.main_container = ttk.Frame(self)
        self.main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # 创建控制面板
        self.control_panel = ttk.Frame(self, height=50)
        self.control_panel.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 创建面板容器
        self.panel_container = ttk.Frame(self.main_container)
        self.panel_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # 初始化面板管理器
        self.panel_manager = PanelManager(self.panel_container, panel_dir)
        
        # 添加控制按钮
        self.setup_control_buttons()
        
    def setup_control_buttons(self):
        """为每个面板创建切换按钮"""
        for panel_name in self.panel_manager.get_panel_names():
            btn = ttk.Button(
                self.control_panel,
                text=panel_name,
                command=lambda name=panel_name: self.show_panel(name)
            )
            btn.pack(side=tk.LEFT, padx=5, pady=5)
            
    def show_panel(self, panel_name):
        """显示指定的面板"""
        self.panel_manager.show_panel(panel_name)