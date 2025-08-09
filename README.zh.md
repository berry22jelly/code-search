# Code Symbol Analysis Toolkit

### 概述
本项目是一个Python代码符号分析工具包，提供全面的代码符号提取、分析和存储功能。它能够解析源代码，提取函数、类和变量等符号及其文档、签名和关系，并将它们存储在SQLite和向量数据库中以便高效查询。

### 核心功能
- **符号提取**：解析Python文件，提取函数、类、变量及其文档
- **结构化存储**：使用关系数据模型将符号元数据存储在SQLite中
- **向量嵌入**：为符号创建向量表示，支持语义搜索
- **综合查询**：支持精确和模糊符号搜索
- **类层次结构**：跟踪类继承和成员关系

### 主要组件
1. **符号提取** (`symbol/symbols.py`)
   - 基于AST的Python代码解析器
   - 处理函数、类、变量、导入语句
   - 提取文档字符串、函数签名、类型注解

2. **数据库存储** (`db/sqlite.py`)
   - 优化的SQLite后端存储
   - 全文搜索功能
   - 文件与符号的关系跟踪

3. **向量存储** (`db/ChromaDB.py`, `src/vector_store.py`)
   - ChromaDB集成实现向量搜索
   - 符号嵌入向量生成

4. **工具集** (`symbol/file_utils.py`)
   - 目录扫描
   - 文件内容处理

### 使用示例

启动GUI应用程序，请运行 `main.py`。

或者：

```python
from symbol.symbols import find_exported_symbols_with_doc
from db.sqlite import SymbolDatabase

# 从文件提取符号
symbols = find_exported_symbols_with_doc("example.py")

# 存储到数据库
with SymbolDatabase() as db:
    db.upsert_file_symbols("example.py", symbols)
    
# 查询符号
results = db.search_symbols_by_name("calculate")
```

### 安装
```bash
pip install -r requirements.txt
```

