import json
import re

from django.db import connection
from google import genai
from google.genai import types


GEMINI_MODEL = "gemma-4-31b-it"
client = genai.Client()


def gemini_generate(system_instruction, prompt, temperature=0.2):
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
        ),
    )
    return (response.text or "").strip()


def query_mysql_database(sql_query: str):
    sql_query = (sql_query or "").strip().rstrip(";")
    if not re.match(r"^(select|show|describe|desc|explain)\b", sql_query, re.IGNORECASE):
        return {"error": "Only read-only SELECT, SHOW, DESCRIBE, DESC, and EXPLAIN queries are allowed."}

    if re.search(r"\b(insert|update|delete|drop|alter|truncate|create|replace|grant|revoke)\b", sql_query, re.IGNORECASE):
        return {"error": "Unsafe SQL keyword detected. Query was not executed."}

    try:
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            columns = [column[0] for column in cursor.description] if cursor.description else []
            rows = cursor.fetchmany(100) if columns else []

        return {
            "sql": sql_query,
            "columns": columns,
            "rows": [dict(zip(columns, row)) for row in rows],
        }
    except Exception as error:
        return {"error": str(error), "sql": sql_query}


def get_database_schema():
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        table_rows = cursor.fetchall()

    tables = [row[0] for row in table_rows]
    schema = []
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f"DESCRIBE `{table}`")
            columns = cursor.fetchall()
            column_names = [column[0] for column in columns]
            schema.append(f"{table}({', '.join(column_names)})")

    return "\n".join(schema)


def extract_sql(text):
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:sql)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"(select|show|describe|desc|explain)\b[\s\S]*", cleaned, re.IGNORECASE)
    return match.group(0).strip().rstrip(";") if match else cleaned.rstrip(";")


def answer_database_question(question, context=""):
    schema = get_database_schema()
    system_prompt = """
    You are a careful database analyst for this Django/MySQL app.
    Generate exactly one read-only SQL query for the user's question.
    Allowed statements: SELECT, SHOW, DESCRIBE, DESC, EXPLAIN.
    Prefer SELECT queries with LIMIT 100 when returning rows.
    Output only SQL. Do not use markdown.
    """
    sql = extract_sql(gemini_generate(
        system_prompt,
        f"Schema:\n{schema}\n\nConversation context:\n{context}\n\nQuestion:\n{question}",
        temperature=0,
    ))
    result = query_mysql_database(sql)

    answer_prompt = """
    Answer the user's database question using only the SQL result.
    Mention if the query failed or returned no rows.
    Be concise and use Burmese when the user writes Burmese.
    """
    return gemini_generate(
        answer_prompt,
        f"Question: {question}\nSQL result JSON:\n{json.dumps(result, default=str)}",
        temperature=0.1,
    ), result


def answer_document_question(question, docs, context=""):
    system_prompt = """
    You are an AI document analyzer.
    Answer only from the retrieved document context.
    If the answer is missing, say the answer is not found in the analyzed documents.
    Be concise, structured, and helpful.
    """
    docs_text = "\n\n".join(f"[Document chunk {index + 1}]\n{doc}" for index, doc in enumerate(docs))
    return gemini_generate(
        system_prompt,
        f"Conversation context:\n{context}\n\nRetrieved document context:\n{docs_text}\n\nQuestion:\n{question}",
        temperature=0.1,
    )


def answer_general_question(question, context=""):
    system_prompt = """
    You are a friendly assistant for the MOGE document management app.
    Answer normal questions and greetings naturally.
    Use Burmese when the user writes Burmese; otherwise use the user's language.
    Keep answers concise.
    """
    return gemini_generate(
        system_prompt,
        f"Conversation context:\n{context}\n\nUser:\n{question}",
        temperature=0.4,
    )


def call_llm(_client, messages):
    user_message = messages[-1]["content"]
    context = "\n".join(f"{message['role']}: {message['content']}" for message in messages[:-1])
    return answer_general_question(user_message, context=context)
