import os
from dotenv import load_dotenv

load_dotenv()

SYMBOLS_DB_FILE_PATH= os.getenv("SYMBOLS_DB_FILE_PATH", "symbols.db")
VECTOR_STORE_PATH= os.getenv("VECTOR_STORE_PATH", "symbol_store_db")