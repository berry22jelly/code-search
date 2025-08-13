from pathlib import Path
from db.Sqlite import SymbolDatabase
from symbol.file_utils import scan_directory
from symbol.symbols import format_signature
from ui.functions.config import SYMBOLS_DB_FILE_PATH

def analyze_and_export_symbols(directory_path: str,glob:str="*.py") -> str:
    """
    分析指定目录下的Python文件符号信息并返回格式化字符串
    
    Args:
        directory_path: 要分析的目录路径
        
    Returns:
        包含所有符号详细信息的字符串
    """
    files = scan_directory(directory_path, glob)
    result = []
    
    for name in files:
        with SymbolDatabase(SYMBOLS_DB_FILE_PATH) as symdb:
            doc = symdb.get_file_symbols(name)
        
        relative_path = Path(name).relative_to(directory_path)
        result.append(f"{relative_path} 导出符号详细信息:")
        
        for i, details in enumerate(doc.get("symbols", [])):
            if details.get('is-member') or details.get("type") in ("method", "attribute"):
                continue
                
            symbol = details.get("name")
            entry = [f"\n{i+1}. {symbol} [{details['type']}]:"]

            if symbol == '__module_doc__':
                entry.append("[模块级文档字符串]")
                entry.append(details.get('doc', ''))
                result.append("\n".join(entry))
                continue
            
            # 输出文档字符串
            if details.get('doc'):
                entry.append("文档字符串:")
                entry.append(details['doc'])
            
            # 输出函数签名
            if details['type'] == 'function' and details.get('signature'):
                entry.append("\n函数签名:")
                entry.append(f"def {symbol}({format_signature(details['signature'])})")
            
            # 输出类基类
            if details['type'] == 'class':
                if details.get('bases'):
                    bases = ", ".join(details['bases'])
                    entry.append(f"\n基类: {bases}")
                
                # 输出类成员
                if details.get('members'):
                    entry.append("\n类成员:")
                    for member_name, member_info in details['members'].items():
                        member_type = member_info['type']
                        
                        if member_type == 'method':
                            # 处理方法签名
                            signature = member_info.get('signature')
                            sig_str = f"({format_signature(signature)})" if signature else "()"
                            member_entry = f"  - 方法: {member_name}{sig_str}"
                            
                            # 输出方法文档字符串
                            if member_info.get('doc'):
                                member_entry += f"\n      文档: {member_info['doc']}"
                            entry.append(member_entry)
                        
                        elif member_type == 'attribute':
                            # 处理属性
                            annotation = member_info.get('annotation', '')
                            anno_str = f": {annotation}" if annotation else ""
                            member_entry = f"  - 属性: {member_name}{anno_str}"
                            
                            # 输出属性文档字符串
                            if member_info.get('doc'):
                                member_entry += f"\n      文档: {member_info['doc'].splitlines()[0].strip()}"
                            entry.append(member_entry)
                        
                        # 添加空行分隔成员
                        entry.append("")
            
            # 输出变量类型注解
            if details['type'] == 'variable' and details.get('annotation'):
                entry.append(f"\n类型注解: {details['annotation']}")
            
            if not details.get('doc') and details['type'] not in ('function', 'class'):
                entry.append("<无附加信息>")
            
            result.append("\n".join(entry))
    
    return "\n".join(result)


