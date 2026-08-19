import os
from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.embeddings import Embeddings
from typing import List


def get_gemini_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GEMIN_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not configured in backend environment (.env)"
        )
    return api_key


class FallbackEmbeddings(Embeddings):
    """Fallback embedding generator using hash/simple vector when API quota is exhausted."""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed(text)

    def _embed(self, text: str) -> List[float]:
        import hashlib

        vec = [0.0] * 384
        words = text.lower().split()
        for idx, word in enumerate(words):
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            vec[h % 384] += 1.0 / (idx + 1)
        # Normalize
        norm = sum(x * x for x in vec) ** 0.5
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


def get_gemini_llm(
    temperature: float = 0.2, model: str = "gemini-3.1-flash-lite"
) -> ChatGoogleGenerativeAI:
    api_key = get_gemini_api_key()
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=temperature,
        max_retries=2,
    )


def get_gemini_embeddings(model: str = "models/gemini-embedding-2") -> Embeddings:
    try:
        api_key = get_gemini_api_key()
        return GoogleGenerativeAIEmbeddings(
            model=model,
            google_api_key=api_key,
        )
    except Exception as e:
        print(f"Using FallbackEmbeddings due to: {e}")
        return FallbackEmbeddings()
