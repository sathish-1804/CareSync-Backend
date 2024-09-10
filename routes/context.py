import os
import re
import logging
from flask import Blueprint, request, jsonify
from models import db
from utils import clean_json_response
from langchain_community.utilities.sql_database import SQLDatabase
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
import google.generativeai as genai  # Import Google Gemini API

context_bp = Blueprint('context', __name__)

# Load environment variables
load_dotenv()

# Verify and load SQLALCHEMY_DATABASE_URI
database_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
if not database_uri:
    raise ValueError("SQLALCHEMY_DATABASE_URI is not set in the environment variables.")

# Initialize Gemini API
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
genai.configure(api_key=gemini_api_key)

# Initialize the SQL database connection
db_llm = SQLDatabase.from_uri(database_uri)

# Initialize the LLM (using Gemini as the model)
llm = genai.GenerativeModel('gemini-1.5-flash-latest')

# Cache schema information to reduce repeated fetches
db_schema_cache = None

# Dictionary to store chat history for each user
user_chat_history = {}

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
    """Fetches the last 2 interactions for a user."""
    return user_chat_history.get(user_id, [])

def update_chat_history(user_id, question, answer):
    """Updates the chat history to keep only the last 2 interactions."""
    if user_id not in user_chat_history:
        user_chat_history[user_id] = []
    user_chat_history[user_id].append({"question": question, "answer": answer})
    # Keep only the last 2 interactions
    user_chat_history[user_id] = user_chat_history[user_id][-2:]

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
        If relevant Consider the previous conversation:
        Chat history:
        {history_context}
    """

    # Enhanced error handling for blocked responses
    try:
        genai_response = llm.generate_content(prompt)
        response_text = genai_response.text.strip()
        if not response_text:
            # Log detailed information if response is blocked
            logging.error(f"Blocked response from Gemini API: {genai_response}")
            return jsonify({"error": "No valid response from Gemini API or response blocked. Check content moderation settings."}), 500
    except Exception as e:
        logging.error(f"Error calling Gemini API: {str(e)}")
        return jsonify({"error": f"Error calling Gemini API: {str(e)}"}), 500


    sql_query_match = re.search(r'SELECT.*?;', response_text, re.DOTALL)
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
            return jsonify({"error": f"Error executing query: {str(e)}"}), 500

        answer_prompt = f"""
            Based on the sql response, write an intuitive answer for the user question, it should be short and crisp. :
            User Question: {question},
            sql_response: {sql_response}
            if the question seems to be medical realted. Provide a medical related answer or advice carefully. For eg. Instead of telling 'I can't provide medical advice.', 'I can't provide personalized health plans'.  Provide something useful.
            If relevant Consider the previous conversation:
            Chat history: {history_context}
            If you could not find the answer, return a helpful and relevant answer to the user's question. Do not return the sql response and do not disclose the user id and the prompt in the answer, also talk like a chatbot.
            Return the answer in the format: Answer: <answer>
        """

        try:
            answer_response = llm.generate_content(answer_prompt)
            answer_text = answer_response.text.strip()
        except Exception as e:
            logging.error(f"Error calling Gemini API for answer generation: {str(e)}")
            return jsonify({"error": f"Error generating answer: {str(e)}"}), 500

        match = re.search(r'Answer:\s*(.*)', answer_text, re.DOTALL)
        if match:
            final_answer = match.group(1).strip()
            print(f"Final Answer: {final_answer}")
            update_chat_history(user_id, question, final_answer)
            return jsonify({"answer": final_answer}), 200
        else:
            logging.error("Could not parse the answer from Gemini response.")
            return jsonify({"error": "Could not parse the answer. Try again later."}), 500
    else:
        fallback_answer_prompt = f"""
        Since a SQL query could not be generated, provide a helpful and relevant answer to the user's question, it should be super short and crisp. :
        User Question: {question}
        Return the answer in the format: Answer: <answer>
        """

        try:
            fallback_response = llm.generate_content(fallback_answer_prompt)
            fallback_answer_text = fallback_response.text.strip()
        except Exception as e:
            logging.error(f"Error calling Gemini API for fallback answer: {str(e)}")
            return jsonify({"error": f"Error generating fallback answer: {str(e)}"}), 500

        fallback_match = re.search(r'Answer:\s*(.*)', fallback_answer_text, re.DOTALL)
        if fallback_match:
            final_answer = fallback_match.group(1).strip()
            update_chat_history(user_id, question, final_answer)
            return jsonify({"answer": final_answer}), 200
        else:
            logging.error("Fallback answer generation failed.")
            return jsonify({"error": "Try again later."}), 500
