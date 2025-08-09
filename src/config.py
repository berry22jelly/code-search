import os
from dotenv import load_dotenv

load_dotenv()

# MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
# MILVUS_PORT = os.getenv("MILVUS_PORT", "19530")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL= os.getenv("BASE_URL")
EMBEDDING_MODEL= os.getenv("EMBEDDING_MODEL")
MODEL_NAME= os.getenv("MODEL_NAME")