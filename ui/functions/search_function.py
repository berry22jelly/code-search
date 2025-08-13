from typing import Dict, List, Optional

from db.SymbolVectorStore import SymbolVectorStore
from ui.functions.config import VECTOR_STORE_PATH


def query_symbols(
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
        # with SymbolVectorStore(persist_path = VECTOR_STORE_PATH) as store:
        store = SymbolVectorStore(persist_path = VECTOR_STORE_PATH)
        results = store.query_symbols(query_text, top_k, where)
        return results