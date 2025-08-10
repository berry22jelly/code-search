# Code Symbol Analysis Toolkit

Enhance vibe coding by providing symbols.

### Overview
This toolkit provides comprehensive code symbol extraction, analysis, and storage capabilities for Python projects. It parses source code to extract symbols (functions, classes, variables) along with their documentation, signatures, and relationships, then stores them in both SQLite and vector databases for efficient querying.

### Key Features
- **Symbol Extraction**: Parse Python files to extract functions, classes, variables with their documentation
- **Structured Storage**: Store symbol metadata in SQLite with relational data model
- **Vector Embeddings**: Create vector representations of symbols for semantic search
- **Comprehensive Query**: Support both exact and fuzzy symbol searching
- **Class Hierarchy**: Track class inheritance and member relationships

### Components
1. **Symbol Extraction** (`symbol/symbols.py`)
   - AST-based parser for Python code
   - Handles functions, classes, variables, imports
   - Extracts docstrings, signatures, type annotations

2. **Database Storage** (`db/sqlite.py`)
   - SQLite backend with optimized schema
   - Full-text search capabilities
   - Relationship tracking (files ↔ symbols)

3. **Vector Storage** (`db/ChromaDB.py`, `src/vector_store.py`)
   - ChromaDB integration for vector search
   - Symbol embedding generation

4. **Utilities** (`symbol/file_utils.py`)
   - Directory scanning
   - File content processing

### Usage

run `main.py` to start the GUI application.

or:

```python
from symbol.symbols import find_exported_symbols_with_doc
from db.sqlite import SymbolDatabase

# Extract symbols from a file
symbols = find_exported_symbols_with_doc("example.py")

# Store in database
with SymbolDatabase() as db:
    db.upsert_file_symbols("example.py", symbols)
    
# Query symbols
results = db.search_symbols_by_name("calculate")
```

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
Set your OpenAI API key in `.env` for advanced processing, see example in `.env.sample`:
```
OPENAI_API_KEY = "your-api-key"
```
