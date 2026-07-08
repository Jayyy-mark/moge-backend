from ..services.embedding import EmbeddingService
from ..services.llm import LLMService

from ..resources.embedding import (
    model_all_miniLM_V2,
    sentence_splitter,
    doc_client,
    doc_collection,
    chat_client,
    chat_collection,
    embedding_model,
)

from ..resources.llm.tiny_aya import HF_MODEL, client


class RagAgentPipeline:

    def __init__(self):
        self.embedding_service = EmbeddingService(
            sentence_splitter=sentence_splitter,
            doc_client=doc_client,
            doc_collection=doc_collection,
            chat_client=chat_client,
            chat_collection=chat_collection,
            embedding_model=embedding_model,
        )
        self.llm = LLMService(client=client, model_name=HF_MODEL)
        self.question = ""
        self.results = None
        self.memory = None

    def systemPrompt(self):

        return f"""

        You are an AI assistant for the University of Computer Studies (Taungoo).

        General questions:
        - mathematics
        - technology
        - programming
        - science
        - general knowledge

        Answer normally.

        University questions:
        - Use ONLY the Document Context.
        - Never make up university information.

        If Document Context is:

        NO_RELEVANT_CONTEXT_FOUND

        reply:

        I'm sorry, but I don't have information about that in my knowledge base.

        Default Response language (Burmese / Myanmar)

        Document Context:
        {self.results}

        Question:
        {self.question}

        default language (Burmese)
        reply to user only use Myanmar Language (Burmese) but for some technical terms or specific words use English.

        """

    # <!--===========================================
    #   UCSTGO RAGAGENT PIPELINE
    # ============================================-->
    def pipe(self, question: str):

        self.question = question

        self.results = self.embedding_service.search_embeddings(query=self.question)
        print("Results : ", self.results)
        self.memory = self.embedding_service.get_memory(query=self.question)
        print("Memory : ", self.memory)
        prompt = self.systemPrompt()

        answer = self.llm.generate(
            system_prompt=prompt, user_prompt=self.question
        )

        self.embedding_service.save_chat(question=self.question, answer=answer)

        return answer

    def update_vector_db(self):

        # <!--=======================================
        #   DOCUMENT PATH
        # =======================================-->
        document_path = "documents/JITES-2020-part-1.pdf"

        self.embedding_service.open_document(document_path=document_path)

        self.embedding_service.prepare_documents()

        self.embedding_service.generate_nodes()

        self.embedding_service.generate_chunks_from_nodes()

        self.embedding_service.generate_embeddings()

        self.embedding_service.store_to_vector()
