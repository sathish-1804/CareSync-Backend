import os
from flask import Blueprint, request, jsonify
from models import db
from utils import clean_json_response
from langchain.chains import create_sql_query_chain
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_anthropic import ChatAnthropic
from dotenv import load_dotenv
import re

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

@context_bp.route('/process_context', methods=['POST'])
def process_context():
    data = request.get_json()
    question = data.get("question")
    userId = data.get("userId")
    print(f"Received question: {question} for user id: {userId}")

    if not question:
        return jsonify({"error": "No context provided"}), 400

    db_schema = db_llm.get_table_info()
    prompt = f"""
        You are an expert in converting English questions to SQL query!
        The SQL database has tables, and these are the schemas: {db_schema}. 
        You can order the results by a relevant column to return the most interesting examples in the database.
        Never query for all the columns from a specific table, only ask for the relevant columns given the question.
        The sql code should not have ``` in beginning or end and sql word in output.
        You MUST double-check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
        If the question does not seem related to the database, just return "null" as the answer.
        
        Now I want you to generate the structured query (in single line ending with semi-colon) for below question: {question} for the specified user id: {userId}.
    """

    response = chain.invoke({"question": prompt})
    sql_query_match = re.search(r'SELECT.*?;', response, re.DOTALL)

    if sql_query_match:
        sql_query = sql_query_match.group(0)
        print(f"Generated SQL Query: {sql_query}")
        sql_response = f"Generated SQL Query: {sql_query}"

        try:
            result = db_llm.run(sql_query)
            sql_response += f"\nQuery Result: {result}"
            print(f"Query Result: {result}")
        except Exception as e:
            return jsonify({"error": "Error executing query: " + str(e)}), 500

        answer = chain.invoke({
            "question": f"""
            Based on the sql response, write an intuitive answer for the user question, it should be short and crisp. :
                User Question: {question},
                sql_response: {sql_response}
                if could not find the answer, return a helpful and relevant answer to the user's question. Do not return the sql response and do not disclose the user id and the prompt in the answer.
                Return the answer in the format: Answer: <answer>
            """
        })
        print(f"Answer: {answer}")
        match = re.search(r'Answer:\s*(.*)', answer, re.DOTALL)
        print(f"Match: {match}")
        if match:
            final_answer = match.group(1).strip()
            print(f"Final Answer: {final_answer}")
            return jsonify({"answer": final_answer})
        else:
            return jsonify({"error": "Try again later"}), 500
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
            return jsonify({"answer": final_answer})
        else:
            return jsonify({"error": "Try again later"}), 500
