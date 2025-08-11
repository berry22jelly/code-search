import os
import sys
import importlib.util
from pathlib import Path
from collections import defaultdict

def _collect_vars_from_dir(directory, target_vars=['ui']):
    """
    收集目录下所有Python文件中指定的变量
    
    参数:
        directory (str): 要扫描的目录路径
        target_vars (list): 要收集的变量名列表
        
    返回:
        dict: 包含 {name_value: {变量名: 值}} 的嵌套字典
        
    示例返回结构:
        {
            "Alice": {"name": "Alice", "age": 30, "city": "New York"},
            "Bob": {"name": "Bob", "age": 25}
        }
    """
    result_dict = {}
    dir_path = Path(directory)
    name_conflicts = defaultdict(list)
    
    if not dir_path.is_dir():
        raise ValueError(f"'{directory}' 不是一个有效目录")
    
    for file_path in dir_path.glob('*.py'):
        if file_path.name == '__init__.py':
            continue
            
        module_name = file_path.stem
        try:
            # 动态加载模块
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            # 检查必需的name变量
            if not hasattr(module, 'name'):
                print(f"跳过文件 '{file_path.name}': 未定义name变量")
                continue
                
            name_value = module.name
            collected_vars = {}
            
            # 收集目标变量
            for var in target_vars:
                if hasattr(module, var):
                    collected_vars[var] = getattr(module, var)
                else:
                    print(f"文件 '{file_path.name}' 中未找到变量: {var}")
            
            # 处理name冲突
            if name_value in result_dict:
                name_conflicts[name_value].append(file_path.name)
                
            result_dict[name_value] = collected_vars
            
        except Exception as e:
            print(f"处理文件 '{file_path.name}' 时出错: {str(e)}")
    
    # 报告name冲突
    for name, files in name_conflicts.items():
        print(f"警告: name值 '{name}' 在多个文件中使用: {', '.join(files)}")
    
    return result_dict

_lang=_collect_vars_from_dir("ui/i18n")
import tkinter


def _copy_structure(master,d):
    if not isinstance(d, dict):
        return None  # 或者你想要的默认值
    
    new_dict = {}
    for k, v in d.items():
        if isinstance(v, dict):
            new_dict[k] = _copy_structure(master,v)
        else:
            new_dict[k] = tkinter.StringVar(master,"")
    return new_dict

available_languages = (k for k in _lang.keys())
"""
可用语言列表
"""

display_dict=None
"""
UI显示文本字典
"""
def init(master,languageCode):
    global display_dict
    display_dict = _lang[languageCode]["ui"]
    #set_language(languageCode)
def set_language(languageCode):
    global display_dict
    display_dict = _lang[languageCode]["ui"]
#     def _copy(d,fromDict):
#         if not isinstance(d, dict):
#             return None  # 或者你想要的默认值
        
#         for k, v in d.items():
#             if isinstance(v, dict):
#                 _copy(v,fromDict.get(k))
#             else:
#                 string:tkinter.StringVar=d[k]
#                 string.set(fromDict.get(k))
#     _copy(display_dict,_lang[languageCode]["ui"])
# if __name__ == '__main__':
#     # 示例用法
#     target_dir = input("请输入要扫描的目录路径: ").strip()
#     variables = input("请输入要收集的变量名(用逗号分隔): ").strip().split(',')
#     variables = [v.strip() for v in variables if v.strip()]
    
#     # 确保name变量被包含
#     if 'name' not in variables:
#         print("注意: 自动添加'name'到收集变量列表")
#         variables.append('name')
    
#     result = collect_vars_from_dir(target_dir, variables)
    
#     print("\n扫描结果:")
#     for name_value, var_dict in result.items():
#         print(f"\n{name_value}:")
#         for var_name, var_value in var_dict.items():
#             print(f"  {var_name}: {var_value!r}")