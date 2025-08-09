import ast
import inspect
from typing import List, Dict, Any, Tuple, Optional, Union

def extract_target_names(target: ast.AST) -> List[str]:
    """递归提取赋值语句中的变量名"""
    if isinstance(target, ast.Name):
        return [target.id]
    elif isinstance(target, (ast.Tuple, ast.List)):
        names = []
        for elt in target.elts:
            names.extend(extract_target_names(elt))
        return names
    return []

def get_docstring(node: ast.AST) -> Optional[str]:
    """从AST节点提取文档字符串"""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
        return None
    
    # 检查函数/类/模块的第一个表达式是否是字符串
    if node.body and isinstance(node.body[0], ast.Expr):
        expr = node.body[0].value
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            return expr.value
        elif isinstance(expr, ast.Str):  # 兼容Python < 3.8
            return expr.s
    
    return None

def unparse_annotation(annotation: ast.AST) -> str:
    """将类型注解节点转换为字符串表示"""
    if annotation is None:
        return ""
    
    # 处理简单标识符
    if isinstance(annotation, ast.Name):
        return annotation.id
    
    # 处理属性访问 (如 np.ndarray)
    if isinstance(annotation, ast.Attribute):
        return f"{unparse_annotation(annotation.value)}.{annotation.attr}"
    
    # 处理下标 (如 List[str])
    if isinstance(annotation, ast.Subscript):
        value = unparse_annotation(annotation.value)
        slice_str = unparse_annotation(annotation.slice)
        return f"{value}[{slice_str}]"
    
    # 处理元组 (如 (int, str))
    if isinstance(annotation, ast.Tuple):
        elements = [unparse_annotation(elt) for elt in annotation.elts]
        return f"({', '.join(elements)})"
    
    # 处理常量 (如字符串字面值)
    if isinstance(annotation, ast.Constant):
        return str(annotation.value)
    
    # 处理字符串 (Python < 3.8)
    if isinstance(annotation, ast.Str):
        return annotation.s
    
    # 处理其他复杂类型
    try:
        # 尝试使用 ast.unparse (Python 3.9+)
        if hasattr(ast, 'unparse'):
            return ast.unparse(annotation)
    except:
        pass
    
    # 回退方案
    return f"<unparsable: {type(annotation).__name__}>"

def parse_function_signature(func_node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> Dict[str, Any]:
    """解析函数签名，包括参数和返回类型"""
    signature = {
        'args': [],
        'vararg': None,
        'kwarg': None,
        'returns': None
    }
    
    # 处理位置参数和关键字参数
    args = func_node.args
    for arg in args.posonlyargs:
        signature['args'].append({
            'name': arg.arg,
            'type': unparse_annotation(arg.annotation),
            'default': None,
            'kind': 'positional_only'
        })
    
    for arg in args.args:
        signature['args'].append({
            'name': arg.arg,
            'type': unparse_annotation(arg.annotation),
            'default': None,
            'kind': 'positional'
        })
    
    for arg in args.kwonlyargs:
        signature['args'].append({
            'name': arg.arg,
            'type': unparse_annotation(arg.annotation),
            'default': None,
            'kind': 'keyword_only'
        })
    
    # 处理默认值
    defaults = args.defaults
    for i, default in enumerate(defaults):
        idx = len(signature['args']) - len(defaults) + i
        if idx < len(signature['args']):
            signature['args'][idx]['default'] = ast.unparse(default) if hasattr(ast, 'unparse') else repr(default)
    
    kw_defaults = args.kw_defaults
    for i, default in enumerate(kw_defaults):
        if default is not None:
            idx = len(args.posonlyargs) + len(args.args) + i
            if idx < len(signature['args']):
                signature['args'][idx]['default'] = ast.unparse(default) if hasattr(ast, 'unparse') else repr(default)
    
    # 处理可变参数
    if args.vararg:
        signature['vararg'] = {
            'name': args.vararg.arg,
            'type': unparse_annotation(args.vararg.annotation),
            'kind': 'varargs'
        }
    
    if args.kwarg:
        signature['kwarg'] = {
            'name': args.kwarg.arg,
            'type': unparse_annotation(args.kwarg.annotation),
            'kind': 'keywords'
        }
    
    # 处理返回类型
    if func_node.returns:
        signature['returns'] = unparse_annotation(func_node.returns)
    
    return signature
class NodeHandler:
    """节点处理的基类"""
    def handle(self, node, symbol_metadata: dict, global_names: list, 
               all_assignments: list, imported_symbols: set, **kwargs):
        raise NotImplementedError

class FunctionHandler(NodeHandler):
    def handle(self, node, symbol_metadata: dict, global_names: list, 
               all_assignments: list, imported_symbols: set, **kwargs):
        include_signatures = kwargs.get('include_signatures', True)
        doc = get_docstring(node)
        signature = parse_function_signature(node) if include_signatures else None
        symbol_metadata[node.name] = {
            'type': 'function',
            'doc': doc,
            'signature': signature,
            'is_import': False,
            'lineno': node.lineno,  # 函数起始行号
            'end_lineno': getattr(node, 'end_lineno', None)
        }
        global_names.append(node.name)
class ClassHandler(NodeHandler):
    def handle(self, node, symbol_metadata: dict, global_names: list, 
               all_assignments: list, imported_symbols: set, **kwargs):
        include_signatures = kwargs.get('include_signatures', True)
        doc = get_docstring(node)
        bases = [unparse_annotation(base) for base in node.bases]
        
        # 收集类的成员
        members = {}
        for item in node.body:
            # 处理方法定义（普通方法和异步方法）
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not item.name.startswith('_') or (
                    item.name.startswith('__') and item.name.endswith('__')):
                    
                    member_doc = get_docstring(item)
                    signature = parse_function_signature(item) if include_signatures else None
                    
                    members[item.name] = {
                        'type': 'method',
                        'doc': member_doc,
                        'signature': signature,
                        'lineno': item.lineno,  # 函数起始行号
                        'end_lineno': getattr(item, 'end_lineno', None)
                    }
            
            # 处理嵌套类
            elif isinstance(item, ast.ClassDef):
                if not item.name.startswith('_'):
                    member_doc = get_docstring(item)
                    members[item.name] = {
                        'type': 'class',
                        'doc': member_doc,
                        'lineno': item.lineno,  # 函数起始行号
                        'end_lineno': getattr(item, 'end_lineno', None)
                    }
            
            # 处理普通赋值（类属性）
            elif isinstance(item, ast.Assign):
                names = extract_target_names(item.targets)
                for name in names:
                    if not name.startswith('_'):
                        members.setdefault(name, {
                            'type': 'attribute',
                            'doc': None,
                            'lineno': item.lineno,  # 函数起始行号
                            'end_lineno': getattr(item, 'end_lineno', None)
                        })
            
            # 处理带类型注解的赋值（类属性）
            elif isinstance(item, ast.AnnAssign):
                names = extract_target_names(item.target)
                type_annotation = unparse_annotation(item.annotation) if item.annotation else None
                for name in names:
                    if not name.startswith('_'):
                        members.setdefault(name, {
                            'type': 'attribute',
                            'doc': None,
                            'annotation': type_annotation,
                            'lineno': item.lineno,  # 函数起始行号
                            'end_lineno': getattr(item, 'end_lineno', None)
                        })
        
        # 注册类到全局元数据
        symbol_metadata[node.name] = {
            'type': 'class',
            'doc': doc,
            'bases': bases,
            'members': members,
            'is_import': False,
            'lineno': node.lineno,  # 函数起始行号
            'end_lineno': getattr(node, 'end_lineno', None)
        }
        global_names.append(node.name)

class AssignHandler(NodeHandler):
    def handle(self, node, symbol_metadata: dict, global_names: list, 
               all_assignments: list, imported_symbols: set, **kwargs):
        if any(isinstance(t, ast.Name) and t.id == '__all__' for t in node.targets):
            all_assignments.append(node)
            global_names.append('__all__')
            symbol_metadata['__all__'] = {
                'type': 'variable', 
                'doc': None, 
                'is_import': False,
                'lineno': node.lineno,  # 函数起始行号
                'end_lineno': getattr(node, 'end_lineno', None)
            }
        else:
            for target in node.targets:
                names = extract_target_names(target)
                for name in names:
                    symbol_metadata.setdefault(name, {
                        'type': 'variable',
                        'doc': None,
                        'is_import': False,
                        'lineno': node.lineno,  # 函数起始行号
                        'end_lineno': getattr(node, 'end_lineno', None)
                    })
                global_names.extend(names)

class AnnAssignHandler(NodeHandler):
    def handle(self, node, symbol_metadata: dict, global_names: list, 
               all_assignments: list, imported_symbols: set, **kwargs):
        names = extract_target_names(node.target)
        if names and names[0] == '__all__':
            all_assignments.append(node)
            symbol_metadata['__all__'] = {
                'type': 'variable', 
                'doc': None, 
                'is_import': False,
                'lineno': node.lineno,  # 函数起始行号
                'end_lineno': getattr(node, 'end_lineno', None)
            }
        for name in names:
            type_annotation = unparse_annotation(node.annotation) if node.annotation else None
            symbol_metadata.setdefault(name, {
                'type': 'variable',
                'doc': None,
                'annotation': type_annotation,
                'is_import': False,
                'lineno': node.lineno,  # 函数起始行号
                'end_lineno': getattr(node, 'end_lineno', None)
            })
        global_names.extend(names)

class ImportHandler(NodeHandler):
    def handle(self, node, symbol_metadata: dict, global_names: list, 
               all_assignments: list, imported_symbols: set, **kwargs):
        for alias in node.names:
            name = alias.asname or alias.name.split('.')[0]
            if name == '*':
                continue
            symbol_metadata[name] = {
                'type': 'import',
                'is_import': True,
                'lineno': node.lineno,  # 函数起始行号
                'end_lineno': getattr(node, 'end_lineno', None)
            }
            global_names.append(name)
            imported_symbols.add(name)

class ImportFromHandler(NodeHandler):
    def handle(self, node, symbol_metadata: dict, global_names: list, 
               all_assignments: list, imported_symbols: set, **kwargs):
        for alias in node.names:
            if alias.name == '*':
                continue
            name = alias.asname or alias.name
            symbol_metadata[name] = {
                'type': 'import',
                'is_import': True,
                'lineno': node.lineno,  # 函数起始行号
                'end_lineno': getattr(node, 'end_lineno', None)
            }
            global_names.append(name)
            imported_symbols.add(name)

# 节点处理器的映射字典
NODE_HANDLERS = {
    ast.FunctionDef: FunctionHandler(),
    ast.AsyncFunctionDef: FunctionHandler(),
    ast.ClassDef: ClassHandler(),
    ast.Assign: AssignHandler(),
    ast.AnnAssign: AnnAssignHandler(),
    ast.Import: ImportHandler(),
    ast.ImportFrom: ImportFromHandler(),
}

def find_exported_symbols_with_doc(file_path: str, 
                                  exclude_imports: bool = False,
                                  include_signatures: bool = True) -> List[Tuple[str, Union[str, Dict[str, Any]]]]:
    """
# 返回值说明：
`find_exported_symbols_with_doc` 返回一个列表，其中每个元素是一个元组 `(symbol, details)`，结构如下：

# 返回值结构
```python
[
  (symbol_name, {  # 每个导出的符号
    "type": str,           # 符号类型：'function'/'class'/'variable'
    "doc": str,            # 可选，文档字符串
    "signature": tuple,    # 仅函数/方法，函数参数信息
    "bases": list[str],    # 仅类，基类名称列表
    "members": dict,       # 仅类，成员字典（结构见下方）
    "annotation": str      # 仅变量/属性，类型注解
  }),
  ... 
]
```

## 特殊键说明
1. **`members` 字典**（仅类）  
   键为成员名，值为包含以下键的字典：
   ```python
   {
     "type": str,        # 'method'/'class'/'attribute'
     "doc": str,         # 可选，文档字符串
     "signature": tuple, # 仅方法，参数信息
     "annotation": str   # 仅属性，类型注解
   }
   ```

2. **特殊符号 `__module_doc__`**  
   表示模块级文档字符串，此时：
   - `symbol` 固定为 `"__module_doc__"`
   - `details` 必含 `"doc"` 键（模块文档内容）
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
    except Exception as e:
        raise RuntimeError(f"解析文件失败: {e}")

    symbol_metadata = {}
    global_names = []
    all_assignments = []
    module_doc = get_docstring(tree)
    imported_symbols = set()

    if module_doc:
        symbol_metadata['__module_doc__'] = {
            'type': 'module', 
            'doc': module_doc
        }

    # 使用策略模式处理每个节点
    for node in tree.body:
        handler = NODE_HANDLERS.get(type(node))
        if handler:
            handler.handle(
                node=node,
                symbol_metadata=symbol_metadata,
                global_names=global_names,
                all_assignments=all_assignments,
                imported_symbols=imported_symbols,
                include_signatures=include_signatures
            )

    # 后续处理保持不变
    exported_symbols = []
    found_all = False
    
    for node in reversed(all_assignments):
        if isinstance(node, ast.Assign):
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            value = node.value
        else:
            continue
            
        if isinstance(value, (ast.List, ast.Tuple)):
            symbols = []
            for element in value.elts:
                if isinstance(element, ast.Constant) and isinstance(element.value, str):
                    symbols.append(element.value)
                elif isinstance(element, ast.Str):
                    symbols.append(element.s)
            
            if symbols:
                found_all = True
                for symbol in symbols:
                    if exclude_imports and symbol in imported_symbols:
                        continue
                    
                    meta = symbol_metadata.get(symbol)
                    if meta:
                        exported_symbols.append((symbol, meta.copy()))
                break

    if not found_all:
        seen = set()
        for name in global_names:
            if name in seen or name.startswith('_') or name == '__all__':
                continue
                
            if exclude_imports:
                meta = symbol_metadata.get(name)
                if meta and meta.get('is_import'):
                    continue
            
            seen.add(name)
            meta = symbol_metadata.get(name)
            if meta:
                exported_symbols.append((name, meta.copy()))
    
    if module_doc:
        exported_symbols.insert(0, ('__module_doc__', symbol_metadata['__module_doc__']))
    
    return exported_symbols

def format_signature(signature: Dict[str, Any]) -> str:
    """格式化函数签名为可读字符串"""
    if not signature:
        return ""
    
    parts = []
    
    # 处理位置参数
    for arg in signature.get('args', []):
        arg_str = arg['name']
        if arg['type']:
            arg_str += f": {arg['type']}"
        if arg['default'] is not None:
            arg_str += f" = {arg['default']}"
        parts.append(arg_str)
    
    # 处理可变参数
    if signature.get('vararg'):
        vararg = signature['vararg']
        arg_str = f"*{vararg['name']}"
        if vararg['type']:
            arg_str += f": {vararg['type']}"
        parts.append(arg_str)
    
    # 处理关键字参数
    if signature.get('kwarg'):
        kwarg = signature['kwarg']
        arg_str = f"**{kwarg['name']}"
        if kwarg['type']:
            arg_str += f": {kwarg['type']}"
        parts.append(arg_str)
    
    # 构建完整签名
    sig_str = ", ".join(parts)
    
    # 添加返回类型
    if signature.get('returns'):
        sig_str += f" -> {signature['returns']}"
    
    return sig_str

def flatten_class_symbols(symbol_metadata: dict) -> None:
    """
    将类中的成员符号展平为 ClassName.member_name 的形式
    递归处理嵌套类，修改原始符号表
    """
    # 辅助函数：递归展平类及其嵌套类
    def _flatten_class(class_name: str, class_meta: dict, symbol_table: dict):
        # 1. 处理当前类的直接成员
        for member_name, member_meta in list(class_meta['members'].items()):
            full_member_name = f"{class_name}.{member_name}"
            
            # 如果是嵌套类，先递归处理
            if member_meta['type'] == 'class':
                _flatten_class(full_member_name, member_meta, symbol_table)
            
            # 2. 将成员添加到全局符号表（无论是否嵌套类）
            symbol_table.append((full_member_name,{
                'from-class':class_name,
                'is-member':True,
                'type': member_meta['type'],
                'doc': member_meta['doc'],
                'lineno': member_meta['lineno'],
                'end_lineno': member_meta.get('end_lineno'),
                # 保留原始类中的额外字段
                **{k: v for k, v in member_meta.items() 
                   if k not in ['type', 'doc', 'lineno', 'end_lineno', 'members']}
            }))
    
    # 收集所有要处理的类（避免在迭代时修改字典）
    classes_to_process = []
    for name, meta in symbol_metadata:
        if meta['type'] == 'class':
            classes_to_process.append((name, meta))
    
    # 处理每个类及其嵌套类
    for class_name, class_meta in classes_to_process:
        _flatten_class(class_name, class_meta, symbol_metadata)

# 使用示例
if __name__ == "__main__":
    # 获取所有导出符号的详细信息（包含函数签名）
    exported = find_exported_symbols_with_doc("file_tools.py", 
                                            exclude_imports=True, 
                                            include_signatures=True)
    
    print("导出符号详细信息:")
    for i, (symbol, details) in enumerate(exported):
        print(f"\n{i+1}. {symbol} [{details['type']}]:")
        
        if symbol == '__module_doc__':
            print("[模块级文档字符串]")
            print(details['doc'])
            continue
        
        # 输出文档字符串
        if details.get('doc'):
            print("文档字符串:")
            print(details['doc'])
        
        # 输出函数签名
        if details['type'] == 'function' and details.get('signature'):
            print("\n函数签名:")
            print(f"def {symbol}({format_signature(details['signature'])})")
        
        # 输出类基类
        if details['type'] == 'class' and details.get('bases'):
            bases = ", ".join(details['bases'])
            print(f"\n基类: {bases}")
        
        # 输出变量类型注解
        if details['type'] == 'variable' and details.get('annotation'):
            print(f"\n类型注解: {details['annotation']}")
        
        if not details.get('doc') and details['type'] not in ('function', 'class'):
            print("<无附加信息>")