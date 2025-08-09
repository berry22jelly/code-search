from symbol.symbols import format_signature
from embedding_util.vector_store import insert_symbol

def store_symbol(symbol_info: dict,symbol_name:str,):
    """
    存储符号及其详细信息到向量数据库
    
    参数:
        symbol_info: 符号信息字典，结构如下:
        {
            "name": str,           # 符号名称
            "type": str,           # 符号类型: 'function'/'class'/'variable'
            "doc": str,            # 可选，文档字符串
            "signature": tuple,    # 仅函数/方法，函数参数信息
            "bases": list[str],    # 仅类，基类名称列表
            "members": dict,       # 仅类，成员字典
            "annotation": str      # 仅变量/属性，类型注解
        }
    """
    if symbol_name:
        symbol_info["name"]=symbol_name
    # 构建符号的完整描述文本
    description = build_symbol_description(symbol_info)
    if not description:
        return {"status": "fail", "symbol": symbol_info["name"], "type": symbol_info["type"]}

    # 调用向量存储插入函数
    insert_symbol(symbol_info["name"], description)
    
    return {"status": "success", "symbol": symbol_info["name"], "type": symbol_info["type"]}

def build_symbol_description(symbol_info: dict) -> str:
    """将符号信息转换为描述文本，处理缺失字段"""
    name = symbol_info.get("name", "unnamed_symbol")
    sym_type = symbol_info.get("type", "unknown")
    
    # 基本描述模板
    parts = [
        f"符号名称: {name}",
        f"类型: {sym_type}"
    ]
    doc = symbol_info.get("doc")
    if not doc or len(doc) < 4:
        return
    # 添加类型特定信息
    if sym_type == "function":
        # 处理函数签名（可能为None）
        signature = symbol_info.get("signature")
        if signature:
            # 将元组转换为可读字符串
            params = format_signature(signature)  #", ".join([str(p) for p in signature])
            parts.append(f"签名: {params}")
        
        # 处理文档字符串（可能为空）
        doc = symbol_info.get("doc")
        if doc:
            parts.append(f"功能说明: {doc}")
        else:
            parts.append(f"功能说明: <无文档>")
    
    elif sym_type == "class":
        # 处理基类信息
        bases = symbol_info.get("bases", [])
        if bases:
            parts.append(f"基类: {', '.join(bases)}")
        
        # 处理类文档
        doc = symbol_info.get("doc")
        if doc:
            parts.append(f"类说明: {doc}")
        else:
            parts.append(f"类说明: <无文档>")
        
        # 处理成员信息
        members = symbol_info.get("members", {})
        if members:
            member_list = []
            for member_name, member_info in members.items():
                member_type = member_info.get("type", "unknown")
                member_doc = member_info.get("doc", "")
                
                # 简短的成员描述
                member_desc = f"{member_name}({member_type})"
                if member_doc:
                    # 只取文档的第一句话
                    short_doc = member_doc.split('.')[0] + '.' if '.' in member_doc else member_doc
                    member_desc += f": {short_doc}"
                
                member_list.append(member_desc)
            
            parts.append(f"类成员: {', '.join(member_list)}")
        else:
            parts.append(f"类成员: <无成员>")
    
    elif sym_type == "variable":
        # 处理类型注解
        annotation = symbol_info.get("annotation")
        if annotation:
            parts.append(f"类型注解: {annotation}")
        
        # 处理变量文档
        doc = symbol_info.get("doc")
        if doc:
            parts.append(f"变量说明: {doc}")
        else:
            parts.append(f"变量说明: <无文档>")
    
    else:  # 未知类型
        # 尝试使用通用文档字段
        doc = symbol_info.get("doc")
        if doc:
            parts.append(f"符号说明: {doc}")
        else:
            parts.append(f"符号说明: <无文档>")
    
    # 拼接为完整描述
    return "\n".join(parts)

# 使用示例
if __name__ == "__main__":
    # 示例函数符号
    function_symbol = {
        "name": "search_symbols",
        "type": "function",
        "doc": "在代码库中搜索相似符号",
        "signature": ("query_text", "top_k = 3")
    }
    
    # 示例类符号
    class_symbol = {
        "name": "VectorStore",
        "type": "class",
        "doc": "管理向量数据库操作的类",
        "bases": ["object"],
        "members": {
            "embed_text": {
                "type": "function",
                "doc": "使用 ChromaDB 内置的嵌入函数生成向量"
            },
            "client": {"type": "variable"}
        }
    }
    class_symbol1 = {
        
        "type": "class",
        "doc": "管理向量数据库操作的类",
        "bases": ["object"],
        "members": {
            "embed_text": {
                "type": "function",
                "doc": "使用 ChromaDB 内置的嵌入函数生成向量"
            },
            "client": {"type": "variable"}
        }
    }
    class_symbol1["name"]="ttt"
    print( build_symbol_description(function_symbol))

    print( build_symbol_description(class_symbol1))
    # 存储符号
    # store_symbol(function_symbol)
    # store_symbol(class_symbol)