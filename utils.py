import bcrypt
import os
import re
import json
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
import urllib
import dotenv

dotenv.load_dotenv()

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(hashed_password, password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def upload_file_and_get_url(file):
    connection_str = os.getenv("AZURE_CONNECTION_STR")
    container_name = 'storage-container'
    blob_service_client = BlobServiceClient.from_connection_string(conn_str=connection_str)
    
    try:
        filename = file.filename
        encoded_filename = urllib.parse.quote(filename)
        container_client = blob_service_client.get_container_client(container=container_name)

        container_client.upload_blob(name=filename, data=file, overwrite=True)
        start_time = datetime.utcnow()
        expiry_time = start_time + timedelta(hours=1)
        sas_token = generate_blob_sas(
            account_name=blob_service_client.account_name,
            container_name=container_name,
            blob_name=filename,
            account_key=blob_service_client.credential.account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
            start=start_time
        )

        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{encoded_filename}?{sas_token}"
        return blob_url
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise

def safe_float(value, default=None):
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default
    
def safe_int(value, default=None):
    # Safely convert a value to int, returning default if conversion fails
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default

def clean_json_response(response_text):
    try:
        cleaned_response = re.sub(r'[^\x20-\x7E]+', '', response_text)
        cleaned_response = cleaned_response.replace('“', '"').replace('”', '"')
        cleaned_response = cleaned_response.replace("```json", "").replace("```", "")
        cleaned_response = cleaned_response.strip()
        return json.loads(cleaned_response)
    except json.JSONDecodeError as json_err:
        print(f"Error decoding JSON after cleaning: {json_err}")
        return None
