import os
import re
import logging
from flask import Blueprint, request, jsonify
from models import db
from utils import clean_json_response
from langchain.chains import create_sql_query_chain
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from concurrent.futures import ThreadPoolExecutor
import threading

context_bp = Blueprint('context', __name__)

# Load environment variables
load_dotenv()

# Verify and load SQLALCHEMY_DATABASE_URI
database_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
if not database_uri:
    raise ValueError("SQLALCHEMY_DATABASE_URI is not set in the environment variables.")

# Initialize LLM and Database connection
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    raise ValueError("ANTHROPIC_API_KEY is not set in the environment variables.")
os.environ["ANTHROPIC_API_KEY"] = anthropic_api_key

llm = ChatAnthropic(model="claude-3-5-sonnet-20240620")
db_llm = SQLDatabase.from_uri(database_uri)
chain = create_sql_query_chain(llm, db_llm)

# Cache schema information to reduce repeated fetches
db_schema_cache = None

# Use a thread-safe way to store chat history for each user
user_chat_history = threading.local()

# Setup a thread pool executor for concurrent processing
executor = ThreadPoolExecutor(max_workers=5)

def get_db_schema():
    global db_schema_cache
    if db_schema_cache is None:
        try:
            db_schema_cache = db_llm.get_table_info()
        except SQLAlchemyError as e:
            logging.error(f"Error fetching schema info: {e}")
            raise
    return db_schema_cache

def get_chat_history(user_id):
    """Fetches the last 2 interactions for a user from thread-local storage."""
    if not hasattr(user_chat_history, 'history'):
        user_chat_history.history = {}
    # Return the history if it exists, otherwise an empty list
    return user_chat_history.history.get(user_id, [])

def update_chat_history(user_id, question, answer):
    """Updates the chat history to keep only the last 2 interactions."""
    if not hasattr(user_chat_history, 'history'):
        user_chat_history.history = {}
    if user_id not in user_chat_history.history:
        user_chat_history.history[user_id] = []
    user_chat_history.history[user_id].append({"question": question, "answer": answer})
    # Keep only the last 2 interactions
    user_chat_history.history[user_id] = user_chat_history.history[user_id][-2:]

@context_bp.route('/process_context', methods=['POST'])
def process_context():
    data = request.get_json()
    question = data.get("question")
    user_id = data.get("userId")

    if not question:
        return jsonify({"error": "No context provided"}), 400

    # Fetch the chat history for context
    chat_history = get_chat_history(user_id)
    history_context = "\n".join(
        [f"Q: {item['question']}\nA: {item['answer']}" for item in chat_history]
    )

    db_schema = get_db_schema()
    prompt = f"""
        You are an expert in converting English questions to SQL query!
        The SQL database has tables, and these are the schemas: {db_schema}. 
        You can order the results by a relevant column to return the most interesting examples in the database.
        Never query for all the columns from a specific table, only ask for the relevant columns given the question.
        The sql code should not have ``` in beginning or end and sql word in output.
        You MUST double-check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
        If the question does not seem related to the database, just return "null" as the answer.
        
        Now I want you to generate the structured query (in single line ending with semi-colon) for below question: {question} for the specified user id: {user_id}.
        Chat history:
        {history_context}
    """

    def invoke_chain_and_execute_sql():
        response = chain.invoke({"question": prompt})
        sql_query_match = re.search(r'SELECT.*?;', response, re.DOTALL)
        if sql_query_match:
            sql_query = sql_query_match.group(0).strip()
            print(f"Generated SQL Query: {sql_query}")
            sql_response = f"Generated SQL Query: {sql_query}"
            try:
                result = db_llm.run(sql_query)
                sql_response += f"\nQuery Result: {result}"
                print(f"Query Result: {result}")
            except Exception as e:
                logging.error(f"Error executing query: {e}")
                return {"error": f"Error executing query: {str(e)}"}

            answer_prompt = f"""
                Based on the sql response, write an intuitive answer for the user question, it should be short and crisp. :
                User Question: {question},
                sql_response: {sql_response}
                If you could not find the answer, return a helpful and relevant answer to the user's question. Do not return the sql response and do not disclose the user id and the prompt in the answer.
                Return the answer in the format: Answer: <answer>
            """
            answer = chain.invoke({"question": answer_prompt})
            print(f"Answer: {answer}")
            match = re.search(r'Answer:\s*(.*)', answer, re.DOTALL)
            if match:
                final_answer = match.group(1).strip()
                print(f"Final Answer: {final_answer}")
                update_chat_history(user_id, question, final_answer)
                return {"answer": final_answer}
            else:
                logging.error("Could not parse the answer from LLM response.")
                return {"error": "Could not parse the answer. Try again later."}
        else:
            fallback_answer = chain.invoke({
                "question": f"""
                Since a SQL query could not be generated, provide a helpful and relevant answer to the user's question, it should be super short and crisp. :
                    User Question: {question}
                """
            })
            fallback_match = re.search(r'Answer:\s*(.*)', fallback_answer, re.DOTALL)
            if fallback_match:
                final_answer = fallback_match.group(1).strip()
                update_chat_history(user_id, question, final_answer)
                return {"answer": final_answer}
            else:
                logging.error("Fallback answer generation failed.")
                return {"error": "Try again later."}

    # Use the thread pool executor to run the process asynchronously
    future = executor.submit(invoke_chain_and_execute_sql)
    result = future.result()

    if "error" in result:
        return jsonify(result), 500
    else:
        return jsonify(result), 200
