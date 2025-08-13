from typing import List, Dict, Optional
from db.config import EMBEDDING_MODEL, OPENAI_API_KEY, BASE_URL
from openai import OpenAI
import uuid
import chromadb
import chromadb.utils.embedding_functions as embedding_functions


class SymbolVectorStore:
    """
    符号向量存储类，封装ChromaDB操作
    """
    
    def __init__(
        self, 
        collection_name: str = "symbol_docs",
        persist_path: str = "symbol_store.db",
        embedding_model: str = EMBEDDING_MODEL,
        api_key: str = OPENAI_API_KEY,
        base_url: str = BASE_URL
    ):
        """
        初始化向量存储
        
        Args:
            collection_name: 集合名称
            persist_path: 持久化存储路径
            embedding_model: 嵌入模型名称
            api_key: OpenAI API密钥
            base_url: API基础URL
        """
        self.embedding_model = embedding_model
        self.api_key = api_key
        self.base_url = base_url
        
        # 初始化OpenAI客户端
        self.openai_client = OpenAI(api_key=api_key, base_url=base_url)
        
        # 初始化嵌入函数
        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name=embedding_model,
            api_base=base_url
        )
        
        # 初始化ChromaDB客户端
        self.chroma_client = chromadb.PersistentClient(path=persist_path)
        
        # 获取或创建集合
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )
    
    def embed_text(self, text: str) -> List[float]:
        """
        生成文本的嵌入向量
        
        Args:
            text: 要嵌入的文本
            
        Returns:
            文本的嵌入向量
        """
        response = self.openai_client.embeddings.create(
            model=self.embedding_model, 
            input=text
        )
        return response.data[0].embedding
    
    def insert_symbol(self, symbol: str, summary: str) -> str:
        """
        插入符号和摘要到向量存储
        
        Args:
            symbol: 符号名称
            summary: 符号摘要
            
        Returns:
            插入的文档ID
        """
        doc_id = str(uuid.uuid4())
        
        self.collection.add(
            ids=[doc_id],
            documents=[summary],
            metadatas=[{"symbol": symbol}]
        )
        
        return doc_id
    
    def batch_insert_symbols(self, symbol_summary_pairs: List[Dict[str, str]]) -> List[str]:
        """
        批量插入符号和摘要
        
        Args:
            symbol_summary_pairs: 符号和摘要的字典列表
            
        Returns:
            插入的文档ID列表
        """
        ids = [str(uuid.uuid4()) for _ in symbol_summary_pairs]
        documents = [pair["summary"] for pair in symbol_summary_pairs]
        metadatas = [{"symbol": pair["symbol"]} for pair in symbol_summary_pairs]
        
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        return ids
    
    def query_symbols(
        self, 
        query_text: str, 
        top_k: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """
        查询相似符号
        
        Args:
            query_text: 查询文本
            top_k: 返回结果数量
            where: 过滤条件
            
        Returns:
            相似符号列表，包含符号、摘要和相似度分数
        """
        results = self.collection.query(
            query_texts=[query_text],
            n_results=top_k,
            where=where,
            include=["documents", "metadatas", "distances"]
        )
        
        return [{
            "symbol": item["symbol"],
            "summary": doc,
            "score": 1 - distance  # 转换为相似度分数
        } for item, doc, distance in zip(
            results["metadatas"][0],
            results["documents"][0],
            results["distances"][0]
        )]
    
    def delete_symbol(self, doc_id: str) -> None:
        """
        删除符号
        
        Args:
            doc_id: 要删除的文档ID
        """
        self.collection.delete(ids=[doc_id])
    
    def update_symbol(self, doc_id: str, symbol: str, summary: str) -> None:
        """
        更新符号信息
        
        Args:
            doc_id: 要更新的文档ID
            symbol: 新的符号名称
            summary: 新的摘要
        """
        self.collection.update(
            ids=[doc_id],
            documents=[summary],
            metadatas=[{"symbol": symbol}]
        )
    
    def get_symbol_count(self) -> int:
        """
        获取集合中的符号数量
        
        Returns:
            符号数量
        """
        return self.collection.count()
    
    def clear_collection(self) -> None:
        """
        清空集合
        """
        self.collection.delete(where={})


# 使用示例
if __name__ == "__main__":
    # 初始化向量存储
    vector_store = SymbolVectorStore()
    
    # 插入符号
    doc_id = vector_store.insert_symbol("AAPL", "Apple Inc. is a technology company...")
    print(f"Inserted document with ID: {doc_id}")
    
    # 批量插入
    symbols = [
        {"symbol": "MSFT", "summary": "Microsoft Corporation is a tech company..."},
        {"symbol": "GOOGL", "summary": "Alphabet Inc. is the parent company of Google..."}
    ]
    ids = vector_store.batch_insert_symbols(symbols)
    print(f"Batch inserted documents with IDs: {ids}")
    
    # 查询
    results = vector_store.query_symbols("technology company", top_k=2)
    print("Query results:")
    for result in results:
        print(f"Symbol: {result['symbol']}, Score: {result['score']:.2f}")
    
    # 获取数量
    print(f"Total symbols in store: {vector_store.get_symbol_count()}")