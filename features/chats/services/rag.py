import uuid
import hashlib
from pathlib import Path
from pypdf import PdfReader
from .embeddings import get_embedding
from .chroma_db import doc_collection

def load_pdf(path):
    reader = PdfReader(path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def load_docx(path):
    try:
        from docx import Document
    except ImportError:
        return ""

    document = Document(path)
    return "\n".join(paragraph.text for paragraph in document.paragraphs)

def load_text(path):
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return load_pdf(path)
    if suffix == ".docx":
        return load_docx(path)
    if suffix in {".txt", ".md", ".csv"}:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    return ""

def chunk_text(text, size=500, overlap=100):
    chunks = []
    i = 0
    while i < len(text):
        chunk = text[i:i+size].strip()
        if chunk:
            chunks.append(chunk)
        i += size - overlap
    return chunks

def file_fingerprint(file_path):
    digest = hashlib.sha256()
    with open(file_path, "rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def document_exists(fingerprint, user_id=None):
    where = {"fingerprint": fingerprint}
    if user_id:
        where = {"$and": [{"fingerprint": fingerprint}, {"user_id": str(user_id)}]}

    result = doc_collection.get(where=where, limit=1)
    return bool(result.get("ids"))

def store_document(file_path, user_id=None):
    fingerprint = file_fingerprint(file_path)
    if document_exists(fingerprint, user_id=user_id):
        return {
            "status": "skipped",
            "fingerprint": fingerprint,
            "chunks": 0,
            "message": "Document already exists in vector memory.",
        }

    text = load_text(file_path)
    if not text.strip():
        return {
            "status": "empty",
            "fingerprint": fingerprint,
            "chunks": 0,
            "message": "No readable text found in document.",
        }

    chunks = chunk_text(text)

    for chunk in chunks:
        doc_collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[get_embedding(chunk)],
            documents=[chunk],
            metadatas=[{
                "source": file_path,
                "fingerprint": fingerprint,
                "user_id": str(user_id) if user_id else "",
            }]
        )

    return {
        "status": "stored",
        "fingerprint": fingerprint,
        "chunks": len(chunks),
        "message": "Document stored in vector memory.",
    }

def retrieve_docs(query, user_id=None, k=5):
    if not query:
        return []

    where = {"user_id": str(user_id)} if user_id else None
    query_kwargs = {
        "query_embeddings": [get_embedding(query, task_type="RETRIEVAL_QUERY")],
        "n_results": k,
    }
    if where:
        query_kwargs["where"] = where

    results = doc_collection.query(
        **query_kwargs
    )
    return results.get("documents", [[]])[0]
