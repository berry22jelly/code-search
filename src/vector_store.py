from src.config import EMBEDDING_MODEL,OPENAI_API_KEY,BASE_URL
from openai import OpenAI
import uuid

client = OpenAI(api_key=OPENAI_API_KEY,base_url=BASE_URL)
import chromadb
from chromadb.utils import embedding_functions
from src.config import EMBEDDING_MODEL, OPENAI_API_KEY, BASE_URL
import uuid
import chromadb.utils.embedding_functions as embedding_functions


openai_ef = embedding_functions.OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                model_name=EMBEDDING_MODEL,
                api_base=BASE_URL
            )
"""
OpenAIEmbeddingFunction
"""

# 初始化 ChromaDB 客户端 (本地持久化)
chroma_client = chromadb.PersistentClient(path="./symbol_store.db")

# 创建/获取集合 (相当于 Milvus 的 collection)
collection_name = "symbol_docs"
collection = chroma_client.get_or_create_collection(
    name=collection_name,
    embedding_function=openai_ef,
    metadata={"hnsw:space": "cosine"}

)

def embed_text(text):
    """使用 ChromaDB 内置的嵌入函数生成向量"""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding

def insert_symbol(symbol, summary):
    """插入数据到 ChromaDB 集合"""
    # 生成唯一 ID
    doc_id = str(uuid.uuid4())
    
    # 插入文档 (自动生成嵌入向量)
    collection.add(
        ids=[doc_id],
        documents=[summary],         # 作为主要文档内容
        metadatas=[{"symbol": symbol}],  # symbol 作为元数据
    )
    
    # 如果需要手动控制嵌入过程：
    # vec = embed_text(summary)
    # collection.add(
    #     ids=[doc_id],
    #     embeddings=[vec],
    #     metadatas=[{"symbol": symbol["name"], "summary": summary}]
    # )

def query_symbols(query_text, top_k=5):
    """查询相似符号"""
    results = collection.query(
        query_texts=[query_text],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )
    
    # 格式化返回结果
    return [{
        "symbol": item["symbol"],
        "summary": doc,
        "score": 1 - distance  # 转换为相似度分数
    } for item, doc, distance in zip(
        results["metadatas"][0],
        results["documents"][0],
        results["distances"][0]
    )]

# 示例用法
def test():
    # 插入数据
    insert_symbol({"name": "apple"}, "Fruit company based in Cupertino")
    insert_symbol({"name": "tesla"}, "Electric vehicle manufacturer")
    
    # 查询相似符号
    results = query_symbols("technology company", top_k=2)
    for res in results:
        print(f"Symbol: {res['symbol']}, Score: {res['score']:.3f}")
        print(f"Summary: {res['summary']}\n")