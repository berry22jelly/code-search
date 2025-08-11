"""
本模块提供sqlite3符号存储对象
"""
import sqlite3
import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import zlib

class SymbolDatabase:
    """
    # 数据库表文档

    ## files 表 (文件信息表)

    ### 表结构
    | 字段名 | 数据类型 | 约束 | 描述 |
    |--------|----------|------|------|
    | id | INTEGER | PRIMARY KEY | 文件唯一标识符 |
    | file_path | TEXT | UNIQUE NOT NULL | 文件的绝对路径 |
    | relative_path | TEXT |  | 文件的相对路径 |
    | file_hash | TEXT | NOT NULL | 文件内容的哈希值 |
    | last_updated | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 最后更新时间 |

    ### 说明
    - 存储项目中的所有文件信息
    - `file_path` 是唯一键，确保不会重复记录同一文件
    - `file_hash` 用于检测文件内容是否变更
    - `last_updated` 自动记录最后更新时间

    ## symbols 表 (符号信息表)

    ### 表结构
    | 字段名 | 数据类型 | 约束 | 描述 |
    |--------|----------|------|------|
    | id | INTEGER | PRIMARY KEY | 符号唯一标识符 |
    | file_id | INTEGER | NOT NULL | 关联的文件ID |
    | symbol_name | TEXT | NOT NULL | 符号名称 |
    | symbol_type | TEXT | CHECK(IN ('function','class','variable','module_doc','method','attribute')) | 符号类型 |
    | lineno | INTEGER |  | 符号起始行号 |
    | end_lineno | INTEGER |  | 符号结束行号 |
    | doc_text | BLOB |  | 文档字符串内容 |
    | signature_json | TEXT |  | 函数/方法签名的JSON表示 |
    | bases_json | TEXT |  | 类基类的JSON表示 |
    | members_json | TEXT |  | 类成员的JSON表示 |
    | annotation | TEXT |  | 类型注解 |

    ### 外键约束
    - `file_id` 外键关联到 `files(id)`，并设置级联删除

    ### 唯一约束
    - `(file_id, symbol_name)` 组合唯一，确保同一文件中不会重复记录同一符号

    ### 说明
    - 存储代码中的所有符号信息（函数、类、变量等）
    - `symbol_type` 限制为预定义的几种类型
    - 存储符号的位置信息（起始行和结束行）
    - 文档字符串和结构化信息（签名、基类、成员）以JSON格式存储
    """
    def __init__(self, db_path: str = "symbols.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表结构"""
        cursor = self.conn.cursor()
        
        # 文件元数据表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY,
            file_path TEXT UNIQUE NOT NULL,
            relative_path TEXT,
            file_hash TEXT NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 符号存储表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS symbols (
            id INTEGER PRIMARY KEY,
            file_id INTEGER NOT NULL,
            symbol_name TEXT NOT NULL,
            symbol_type TEXT CHECK(symbol_type IN ('function', 'class', 'variable', 'module_doc', 'method','attribute')),
            lineno INTEGER,  
            end_lineno INTEGER,  
            doc_text BLOB,
            signature_json TEXT,
            bases_json TEXT,
            members_json TEXT,
            annotation TEXT,
            compressed BOOLEAN DEFAULT 0,
            FOREIGN KEY(file_id) REFERENCES files(id) on delete cascade,
            UNIQUE(file_id, symbol_name)
        )
        ''')
        
        # 创建索引加速查询
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_name ON symbols(symbol_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_symbol_type ON symbols(symbol_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON files(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_lineno ON symbols(lineno)')  # 添加行号索引
        
        self.conn.commit()
    
    def _compress_text(self, text: str) -> bytes:
        """压缩文本数据"""
        return zlib.compress(text.encode('utf-8'))
    
    def _decompress_text(self, data: bytes) -> str:
        """解压缩文本数据"""
        return zlib.decompress(data).decode('utf-8')
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件内容的哈希值"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def upsert_file_symbols(self, file_path: str, symbols_info: List[Tuple[str, Dict]],relative_path = None):
        """
        更新或插入文件的符号信息
        
        参数:
            file_path: 文件路径
            symbols_info: 符号信息列表，格式为 [(symbol_name, details_dict), ...]
        """
        file_path = str(Path(file_path).resolve())
        file_hash = 'self._calculate_file_hash()'
        
        cursor = self.conn.cursor()
        
        # 检查文件是否已存在
        cursor.execute('SELECT id, file_hash FROM files WHERE file_path = ?', (file_path,))
        file_record = cursor.fetchone()
        
        if file_record:
            file_id, old_hash = file_record
            # 文件未变更，跳过更新
            if old_hash == file_hash:
                pass
            # 删除旧的符号记录
            cursor.execute('DELETE FROM symbols WHERE file_id = ?', (file_id,))
        else:
            # 插入新文件记录
            cursor.execute(
                'INSERT INTO files (file_path, file_hash, relative_path) VALUES (?, ?, ?)',
                (file_path, file_hash, relative_path)
            )
            file_id = cursor.lastrowid
        
        # 插入符号数据
        for symbol_name, details in symbols_info:
            # 处理模块文档的特殊情况
            if symbol_name == "__module_doc__":
                symbol_type = "module_doc"
                doc_text = details.get("doc", "")
                lineno = details.get("lineno", None)
                end_lineno = details.get("end_lineno", None)
                # 其他字段留空
                signature_json = None
                bases_json = None
                members_json = None
                annotation = None
            else:
                symbol_type = details.get("type", "")
                doc_text = details.get("doc", "")
                lineno = details.get("lineno", None)
                end_lineno = details.get("end_lineno", None)
                signature = details.get("signature")
                bases = details.get("bases", [])
                members = details.get("members", {})
                annotation = details.get("annotation", "")
                
                # 序列化复杂结构
                signature_json = json.dumps(signature) if signature else None
                bases_json = json.dumps(bases) if bases else None
                members_json = json.dumps(members) if members else None
            
            # 压缩文档文本（如果超过阈值）
            doc_text = doc_text if doc_text else ""
            compressed = False#len(doc_text) > 1024  # 1KB阈值
            doc_data =  doc_text.encode('utf-8')
            #self._compress_text(doc_text) if compressed else
            cursor.execute('''
            INSERT INTO symbols (
                file_id, symbol_name, symbol_type, lineno, end_lineno,
                doc_text, signature_json, bases_json, members_json, 
                annotation, compressed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                file_id, symbol_name, symbol_type, lineno, end_lineno,
                doc_data, signature_json, bases_json, members_json,
                annotation, int(compressed)
            ))
        
        # 更新文件时间戳
        cursor.execute(
            'UPDATE files SET last_updated = ?, file_hash = ? WHERE id = ?',
            (datetime.now().isoformat(), file_hash, file_id)
        )
        cursor.close()
        self.conn.commit()
    
    def get_symbol_info(self, symbol_name: str, file_path: Optional[str] = None) -> List[Dict]:
        """
        查询符号信息
        
        参数:
            symbol_name: 符号名称
            file_path: 可选，指定文件路径
        
        返回:
            符号信息字典列表
        """
        cursor = self.conn.cursor()
        
        if file_path:
            file_path = str(Path(file_path).resolve())
            cursor.execute('''
            SELECT s.symbol_name, s.symbol_type, s.lineno, s.end_lineno,
                   s.doc_text, s.compressed, s.signature_json, 
                   s.bases_json, s.members_json, s.annotation,
                   f.file_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE s.symbol_name = ? AND f.file_path = ?
            ''', (symbol_name, file_path))
        else:
            cursor.execute('''
            SELECT s.symbol_name, s.symbol_type, s.lineno, s.end_lineno,
                   s.doc_text, s.compressed, s.signature_json, 
                   s.bases_json, s.members_json, s.annotation,
                   f.file_path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            WHERE s.symbol_name = ?
            ''', (symbol_name,))
        
        results = []
        for row in cursor.fetchall():
            (name, sym_type, lineno, end_lineno,
             doc_data, compressed, sig_json, bases_json, 
             members_json, annotation, file_path) = row
            
            # 处理文档文本
            if doc_data:
                if compressed:
                    doc_text = self._decompress_text(doc_data)
                else:
                    doc_text = doc_data.decode('utf-8')
            else:
                doc_text = ""
            
            # 构建结果字典
            symbol_info = {
                "symbol_name": name,
                "symbol_type": sym_type,
                "lineno": lineno,
                "end_lineno": end_lineno,
                "doc": doc_text,
                "file_path": file_path,
                "annotation": annotation
            }
            
            # 解析JSON数据
            if sig_json:
                symbol_info["signature"] = json.loads(sig_json)
            if bases_json:
                symbol_info["bases"] = json.loads(bases_json)
            if members_json:
                symbol_info["members"] = json.loads(members_json)
            
            results.append(symbol_info)
        
        return results
    
    def get_file_symbols(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件中的所有符号
        
        参数:
            file_path: 文件路径
        
        返回:
            文件符号信息字典
        """
        file_path = str(Path(file_path).resolve())
        cursor = self.conn.cursor()
        
        cursor.execute('''
        SELECT s.symbol_name, s.symbol_type, s.lineno, s.end_lineno,
               s.doc_text, s.compressed, s.signature_json, 
               s.bases_json, s.members_json, s.annotation
        FROM symbols s
        JOIN files f ON s.file_id = f.id
        WHERE f.file_path = ?
        ''', (file_path,))
        
        symbols = []
        for row in cursor.fetchall():
            (name, sym_type, lineno, end_lineno,
             doc_data, compressed, sig_json, bases_json, 
             members_json, annotation) = row
            
            # 处理文档文本
            if doc_data:
                if compressed:
                    doc_text = self._decompress_text(doc_data)
                else:
                    doc_text = doc_data.decode('utf-8')
            else:
                doc_text = ""
            
            # 构建符号信息
            symbol_info = {
                "name": name,
                "type": sym_type,
                "lineno": lineno,
                "end_lineno": end_lineno,
                "doc": doc_text,
                "annotation": annotation
            }
            
            # 解析JSON数据
            if sig_json:
                symbol_info["signature"] = json.loads(sig_json)
            if bases_json:
                symbol_info["bases"] = json.loads(bases_json)
            if members_json:
                symbol_info["members"] = json.loads(members_json)
            
            symbols.append(symbol_info)
        
        return {
            "file_path": file_path,
            "symbols": symbols
        }
    
    def find_symbols(self, search_term: str, limit: int = 20) -> List[Dict]:
        """
        搜索符号（使用SQLite全文搜索）
        
        参数:
            search_term: 搜索关键词
            limit: 返回结果数量限制
        
        返回:
            匹配的符号信息列表
        """
        cursor = self.conn.cursor()
        
        # 使用简单的LIKE搜索（实际应用中可用FTS5优化）
        cursor.execute('''
        SELECT s.symbol_name, s.symbol_type, f.file_path
        FROM symbols s
        JOIN files f ON s.file_id = f.id
        WHERE s.symbol_name LIKE ? OR s.doc_text LIKE ?
        LIMIT ?
        ''', (f'%{search_term}%', f'%{search_term}%', limit))
        
        return [
            {"symbol_name": row[0], "symbol_type": row[1], "file_path": row[2]}
            for row in cursor.fetchall()
        ]
    
    def remove_file(self, file_path: str):
        """
        从数据库中移除文件及其所有符号
        
        参数:
            file_path: 文件路径
        """
        file_path = str(Path(file_path).resolve())
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT id FROM files WHERE file_path = ?', (file_path,))
        file_record = cursor.fetchone()
        
        if file_record:
            file_id = file_record[0]
            cursor.execute('DELETE FROM symbols WHERE file_id = ?', (file_id,))
            cursor.execute('DELETE FROM files WHERE id = ?', (file_id,))
            self.conn.commit()
    from typing import List, Dict, Optional, Union


    # ========== 文件相关操作 ==========
    
    def get_file_by_path(self, file_path: str) -> Optional[Dict]:
        """根据文件路径获取文件信息
        
        Args:
            file_path: 文件的绝对路径
            
        Returns:
            文件信息的字典，如果不存在则返回None
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM files WHERE file_path = ?", (file_path,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_files(self) -> List[Dict]:
        """获取所有文件信息
        
        Returns:
            文件信息字典列表
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM files")
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns,row)) for row in cursor.fetchall()]
    
    def get_recently_updated_files(self, limit: int = 10) -> List[Dict]:
        """获取最近更新的文件
        
        Args:
            limit: 返回结果数量限制
            
        Returns:
            最近更新的文件信息列表
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT file_path, last_updated FROM files "
            "ORDER BY last_updated DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]


    def delete_file(self, file_path: str):
        """删除文件记录（级联删除相关符号）
        
        Args:
            file_path: 要删除的文件路径
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM files WHERE file_path = ?", (file_path,))
        self.conn.commit()

    def search_symbols_by_name(self, name: str, symbol_type: str = None) -> List[Dict]:
        """根据名称搜索符号
        
        Args:
            name: 要搜索的符号名称（支持模糊搜索）
            symbol_type: 可选，限制符号类型
            
        Returns:
            匹配的符号信息列表
        """
        cursor = self.conn.cursor()
        query = (
            "SELECT * "
            "FROM symbols s "
            "JOIN files f ON s.file_id = f.id "
            "WHERE s.symbol_name LIKE ?"
        )
        params = [f"%{name}%"]
        
        if symbol_type:
            query += " AND s.symbol_type = ?"
            params.append(symbol_type)
            
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns,row)) for row in cursor.fetchall()]
    
    def _get_stale_files(self) -> List[str]:
        """
        获取数据库中已不存在的文件
        
        返回:
            不存在的文件路径列表
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT file_path FROM files')
        db_files = [row[0] for row in cursor.fetchall()]
        
        return [path for path in db_files if not os.path.exists(path)]
    
    def vacuum(self):
        """优化数据库并清理已删除文件"""
        # 清理不存在的文件
        # stale_files = self.get_stale_files()
        # for file_path in stale_files:
        #     self.remove_file(file_path)
        
        # 执行SQLite的VACUUM命令
        self.conn.execute('VACUUM')
        self.conn.commit()
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def get_class_members(self, class_name: str) -> List[Dict]:
        """获取类的所有成员（方法和属性）
        
        Args:
            class_name: 类名
            
        Returns:
            类成员信息列表，每个成员包含符号信息和所在文件信息
        """
        cursor = self.conn.cursor()
        # 查找以"ClassName."开头的符号
        cursor.execute(
            "SELECT s.*, f.file_path FROM symbols s "
            "JOIN files f ON s.file_id = f.id "
            "WHERE s.symbol_name LIKE ? || '.%' "
            "ORDER BY s.lineno",
            (class_name,)
        )
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns,row)) for row in cursor.fetchall()]

    def get_class_methods(self, class_name: str) -> List[Dict]:
        """获取类的所有方法
        
        Args:
            class_name: 类名
            
        Returns:
            类方法信息列表
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT s.*, f.file_path FROM symbols s "
            "JOIN files f ON s.file_id = f.id "
            "WHERE s.symbol_name LIKE ? || '.%' "
            "AND s.symbol_type IN ('method', 'function') "
            "ORDER BY s.lineno",
            (class_name,)
        )
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns,row)) for row in cursor.fetchall()]

    def get_class_attributes(self, class_name: str) -> List[Dict]:
        """获取类的所有属性
        
        Args:
            class_name: 类名
            
        Returns:
            类属性信息列表
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT s.*, f.file_path FROM symbols s "
            "JOIN files f ON s.file_id = f.id "
            "WHERE s.symbol_name LIKE ? || '.%' "
            "AND s.symbol_type = 'attribute' "
            "ORDER BY s.lineno",
            (class_name,)
        )
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns,row)) for row in cursor.fetchall()]

    def get_class_and_members(self, class_name: str) -> Dict:
        """获取类定义及其所有成员信息
        
        Args:
            class_name: 类名
            
        Returns:
            包含类定义和成员信息的字典结构
            {
                "class": class_info_dict,
                "methods": [method_dict, ...],
                "attributes": [attribute_dict, ...]
            }
        """
        # 首先获取类本身的定义
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT s.*, f.file_path FROM symbols s "
            "JOIN files f ON s.file_id = f.id "
            "WHERE s.symbol_name = ? AND s.symbol_type = 'class'",
            (class_name,)
        )
        class_info = cursor.fetchone()
        
        if not class_info:
            return None
            
        result = {
            "class": dict(class_info),
            "methods": self.get_class_methods(class_name),
            "attributes": self.get_class_attributes(class_name)
        }
        
        # 尝试解析类的基类信息
        try:
            result["class"]["bases_json"] = json.loads(result["class"].get("bases_json", "[]"))
        except (json.JSONDecodeError, TypeError):
            result["class"]["bases_json"] = []
            
        return result
    
    def get_directory_structure(self, root_path: str = None) -> Dict:
        """获取目录树结构
        
        Args:
            root_path: 可选，指定根目录路径
            
        Returns:
            嵌套字典表示的目录结构
            {
                "path": "/absolute/path",
                "name": "dirname",
                "files": [file_dict, ...],
                "subdirectories": [
                    {subdir_structure},
                    ...
                ]
            }
        """
        # 获取所有文件
        all_files = self.get_all_files()
        
        # 构建目录树
        tree = {
            "path": root_path if root_path else "",
            "name": os.path.basename(root_path) if root_path else "root",
            "files": [],
            "subdirectories": {}
        }
        
        for file in all_files:
            path = file["file_path"]
            
            # 如果指定了根路径，且文件不在根路径下，则跳过
            if root_path and not path.startswith(root_path):
                continue
                
            # 获取相对于根目录的路径
            rel_path = os.path.relpath(path, root_path) if root_path else path
            parts = [p for p in os.path.normpath(rel_path).split(os.sep) if p]
            
            # 如果是根目录下的直接文件
            if len(parts) == 1:
                tree["files"].append(file)
                continue
                
            # 处理子目录中的文件
            current = tree["subdirectories"]
            dir_parts = parts[:-1]  # 去掉文件名部分
            
            # 构建目录层级
            full_path = root_path if root_path else ""
            for i, part in enumerate(dir_parts):
                full_path = os.path.join(full_path, part)
                
                if part not in current:
                    current[part] = {
                        "path": full_path,
                        "name": part,
                        "files": [],
                        "subdirectories": {}
                    }
                current = current[part]["subdirectories"]
            
            # 添加到对应目录的文件列表
            target_dir = tree["subdirectories"]
            for part in dir_parts[:-1]:
                target_dir = target_dir[part]["subdirectories"]
            target_dir[dir_parts[-1]]["files"].append(file)
        
        # 转换子目录为列表形式
        def convert_to_list_structure(node):
            node["subdirectories"] = [
                convert_to_list_structure(subdir) 
                for subdir in node["subdirectories"].values()
            ]
            return node
        
        return convert_to_list_structure(tree)
    
    def _flatten_directory_tree(self, tree: Dict) -> Dict:
        """将目录树结构转换为标准格式"""
        result = {
            "path": "",
            "name": "root",
            "files": [],
            "subdirectories": []
        }
        
        # 递归处理子目录
        def process_node(node, parent_path):
            dirs = []
            for name, data in node.items():
                dir_path = data["path"]
                dir_entry = {
                    "path": dir_path,
                    "name": name,
                    "files": data["files"],
                    "subdirectories": process_node(data["subdirectories"], dir_path)
                }
                dirs.append(dir_entry)
            return dirs
        
        result["subdirectories"] = process_node(tree, "")
        return result