# from sentence_transformers import SentenceTransformer

# model = SentenceTransformer("all-MiniLM-L6-v2")


# def get_embedding(text):
#     return model.encode(text).tolist()

import requests

EMBEDDING_URL = "https://a198-35-247-164-35.ngrok-free.app/embedding/"


def get_embedding(text):
    response = requests.post(EMBEDDING_URL, json={"texts": text}, timeout=60)

    response.raise_for_status()

    return response.json()["embeddings"]


# <!--===================================
#   GEMINI EMBEDDING MODEL
# ====================================-->
# from google import genai
# from google.genai import types

# client = genai.Client()


# def get_embedding(text, task_type="RETRIEVAL_DOCUMENT"):
#     text = (text or "").strip()
#     if not text:
#         text = "empty"

#     # Use 'text-embedding-004' for standard text or 'gemini-embedding-2' for multimodal
#     response = client.models.embed_content(
#         model="gemini-embedding-2",
#         contents=text,
#         config=types.EmbedContentConfig(task_type=task_type),
#     )
#     # The API returns a list of embeddings; extract the values
#     return response.embeddings[0].values
