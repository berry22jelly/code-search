from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk

class IPanel(ABC):
    """面板接口抽象基类，所有面板必须实现这些方法"""
    
    @abstractmethod
    def __init__(self, master: tk.Widget):
        """初始化面板
        
        参数:
            master (tk.Widget): 父容器部件
        """
        pass
    
    @abstractmethod
    def get_frame(self) -> tk.Widget:
        """获取面板的主框架
        
        返回:
            tk.Widget: 面板的主框架部件
        """
        pass
    
