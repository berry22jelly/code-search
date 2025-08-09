from pymilvus import Collection
from embedding_util.vector_store import embed_text, collection_name

def search_symbols(query_text, top_k=3):
    #vec = embed_text(query_text)
    collection = Collection(collection_name)
    collection.load()
    results = collection.search(
        data=[query_text],
        limit=top_k,
        output_fields=["symbol", "summary"]
    )

    for hits in results:
        for hit in hits:
            print(f"Symbol: {hit.entity.get('symbol')}")
            print(f"Summary: {hit.entity.get('summary')}")
            print(f"Score: {hit.distance:.4f}\n")
    return results