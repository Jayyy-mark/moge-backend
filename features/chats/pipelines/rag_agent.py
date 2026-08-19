import re
from typing import Dict, Any, Tuple, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from features.chats.services.gemini_service import get_gemini_llm
from features.chats.tools.db_tool import query_database_tool
from features.chats.tools.doc_tool import search_documents


class RagAgentPipeline:
    database_keywords = {
        "database", "db", "sql", "table", "record", "records", "count",
        "how many", "list", "staff", "staffs", "user", "room", "rooms",
        "department", "departments", "category", "categories", "rank", "ranks",
        "role", "roles", "location", "locations", "building", "buildings",
        "email", "phone", "address", "tin dar",
    }

    document_keywords = {
        "document", "documents", "file", "files", "pdf", "docx", "summarize",
        "summary", "analyze", "extract", "find in", "according to", "uploaded",
        "content", "report", "paper", "tin dar document",
    }

    greeting_patterns = (r"^\s*(hi|hello|hey|mingalarbar|greetings)\s*[!.]*\s*$",)

    MODELS_TO_TRY = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-2.5-flash-lite",
        "gemini-pro",
    ]

    def _invoke_llm(self, messages: List[Any]) -> str:
        last_error = None
        for model_name in self.MODELS_TO_TRY:
            try:
                llm = get_gemini_llm(model=model_name)
                response = llm.invoke(messages)
                if response and response.content:
                    return response.content
            except Exception as e:
                print(f"Model {model_name} failed: {e}")
                last_error = e

        raise last_error or RuntimeError("All Gemini models failed to respond.")

    def _format_history_messages(self, history: List[Dict[str, str]] = None) -> List[Any]:
        msg_list = []
        if history:
            for item in history:
                role = item.get("role") or item.get("sender")
                content = item.get("content") or item.get("text") or ""
                if not content.strip():
                    continue
                if role in ["user", "human"]:
                    msg_list.append(HumanMessage(content=content))
                elif role in ["assistant", "admin", "ai"]:
                    msg_list.append(AIMessage(content=content))
        return msg_list

    def classify_route(self, question: str, has_file: bool = False) -> str:
        text = (question or "").lower()
        if has_file:
            return "DOCUMENT"

        if any(re.search(pattern, text, re.IGNORECASE) for pattern in self.greeting_patterns):
            return "GENERAL"

        has_doc_kw = any(kw in text for kw in self.document_keywords)
        has_db_kw = any(kw in text for kw in self.database_keywords)

        if has_doc_kw and not has_db_kw:
            return "DOCUMENT"
        elif has_db_kw:
            return "DATABASE"
        elif has_doc_kw:
            return "DOCUMENT"

        return "GENERAL"

    def pipe(
        self,
        question: str,
        document_id: Any = None,
        has_file: bool = False,
        history: List[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        route = self.classify_route(question, has_file=has_file)
        source_documents: List[Dict[str, Any]] = []
        response_text = ""

        history_msgs = self._format_history_messages(history)

        if route == "DATABASE":
            db_data = query_database_tool.invoke(question)
            source_documents = []

            system_prompt = f"""
You are an AI Assistant for MOGE (Myanmar Oil and Gas Enterprise).
Answer the user's question accurately using ONLY the provided Database Records below.
Consider the previous conversation history when answering context-dependent follow-up questions.
If the information is not in the records, state politely that it was not found in the database.

Reply in Burmese (Myanmar Language) by default, or English if asked. Technical terms or names can remain in English.

Database Records:
{db_data}
"""
            messages = [SystemMessage(content=system_prompt)]
            messages.extend(history_msgs)
            messages.append(HumanMessage(content=question))
            response_text = self._invoke_llm(messages)

        elif route == "DOCUMENT":
            formatted_context, source_docs = search_documents(question, top_k=5)
            source_documents = source_docs

            if formatted_context == "NO_RELEVANT_CONTEXT_FOUND":
                db_data = query_database_tool.invoke(question)
                system_prompt = f"""
You are an AI Assistant for MOGE.
The user is asking a document-related question, but no direct document content chunks were found in the vector store.
Below is the database record summary:
{db_data}

Answer politely in Burmese or English. If no information exists, state that no matching document content was found in the knowledge base.
"""
            else:
                system_prompt = f"""
You are an AI Assistant for MOGE.
Answer the user's question strictly based on the Document Context below and consider recent conversation history for follow-ups.
Include citations or references to the document names when answering.

Reply in Burmese (Myanmar Language) by default, using English for technical terms or names.

Document Context:
{formatted_context}
"""
            messages = [SystemMessage(content=system_prompt)]
            messages.extend(history_msgs)
            messages.append(HumanMessage(content=question))
            response_text = self._invoke_llm(messages)

        else:
            system_prompt = """
You are a helpful and polite AI Assistant for MOGE (Myanmar Oil and Gas Enterprise).
Answer the user's general questions clearly and helpfully.
Remember the context of previous messages in the conversation.
Reply in Burmese (Myanmar Language) by default, or English if requested.
"""
            messages = [SystemMessage(content=system_prompt)]
            messages.extend(history_msgs)
            messages.append(HumanMessage(content=question))
            response_text = self._invoke_llm(messages)

        return {
            "response": response_text,
            "source": route.lower(),
            "route": route,
            "source_documents": source_documents,
        }
