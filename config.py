import os
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URI = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('HOST_NAME')}/{os.getenv('DB_NAME')}"
DEBUG = os.getenv('DEBUG', 'True') == 'True'
