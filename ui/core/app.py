import tkinter as tk
from tkinter import ttk
from .panel_manager import PanelManager

import tkinter as tk
from tkinter import ttk
from .panel_manager import PanelManager

class DynamicPanelApp(tk.Tk):
    def __init__(self, panel_dir="panels"):
        super().__init__()
        from ui.core.i18n import init
        init(self,"zh-cn")
        self.title("Dynamic Panel Loader")
        self.geometry("800x600")
        
        # 创建菜单栏
        self.create_menu()
        self.panel_dir=panel_dir
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
        
        # 当前语言状态
        self.current_language = "en"  # 默认语言
        
    def create_menu(self):
        """创建菜单栏"""
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        
        # 创建"文件"菜单
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="退出", command=self.destroy)
        self.menu_bar.add_cascade(label="文件", menu=file_menu)
        
        # 创建"设置"菜单
        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="设置", menu=settings_menu)
        
        # 添加语言选择子菜单
        language_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="显示语言", menu=language_menu)
        from ui.core.i18n import available_languages
        # 添加语言选项
        languages = [
           (i,i) for i in available_languages
        ]
        
        for lang_name, lang_code in languages:
            language_menu.add_radiobutton(
                label=lang_name,
                command=lambda l=lang_code: self.set_language(l),
                
                value=lang_name
            )
        
        # 添加其他设置选项
        settings_menu.add_separator()
        settings_menu.add_command(label="主题设置", command=self.open_theme_settings)
        
    def set_language(self, language_code):
        """设置应用程序语言"""
        # 这里可以添加实际的语言切换逻辑
        print(f"切换语言到: {language_code}")
        self.current_language = language_code
        # 在实际应用中，这里会:
        # 1. 加载对应的语言文件
        # 2. 更新界面上的所有文本
        # 3. 可能需要重启应用或刷新界面
        import ui.core.i18n as i18n
        i18n.set_language(language_code)
        self.refresh()
        # 显示语言切换成功的消息
        self.show_language_change_message(language_code)
    
    def show_language_change_message(self, language_code):
        """显示语言切换成功的消息"""
        pass
    
    def open_theme_settings(self):
        """打开主题设置（占位函数）"""
        print("打开主题设置...")
        # 在实际应用中，这里会打开主题设置面板
        
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

    def refresh(self):
        
        
        # self.title("Dynamic Panel Loader")
        # self.geometry("800x600")
        
        # # 创建菜单栏
        # self.create_menu()
        self.panel_container.destroy()
        self.control_panel.destroy()
        self.main_container.destroy()
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
        self.panel_manager = PanelManager(self.panel_container, self.panel_dir)
        
        # 添加控制按钮
        self.setup_control_buttons()
        