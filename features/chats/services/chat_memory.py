import uuid
from .embeddings import get_embedding
from .chroma_db import chat_collection

def save_to_chroma(user_id, role, content):
    if not content:
        return

    chat_collection.add(
        ids=[str(uuid.uuid4())],
        embeddings=[get_embedding(content)],
        documents=[content],
        metadatas=[{
            "user_id": user_id,
            "role": role
        }]
    )

def retrieve_memory(user_id, query, k=5):
    if not query:
        return []

    results = chat_collection.query(
        query_embeddings=[get_embedding(query, task_type="RETRIEVAL_QUERY")],
        n_results=k,
        where={"user_id": user_id}
    )

    return [
        {
            "role": results["metadatas"][0][i]["role"],
            "content": results["documents"][0][i]
        }
        for i in range(len(results["documents"][0]))
    ]
