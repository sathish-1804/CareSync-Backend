from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import os

# Create a single SQLAlchemy instance
db = SQLAlchemy()

# Configure the SQLAlchemy engine
engine = create_engine(
    os.getenv('SQLALCHEMY_DATABASE_URI'),  # Fetching from environment variables
    pool_size=10,  # Adjust pool size based on your application's needs
    max_overflow=20,  # Allow some overflow connections
    pool_timeout=30,  # Increase timeout if necessary
    pool_recycle=3600,  # Recycle connections after an hour
    pool_pre_ping=True  # Check connections are alive before using them
)

# Create a configured "Session" class
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

def init_db(app):
    # Correctly initialize the app with the db instance
    db.init_app(app)
    with app.app_context():
        db.create_all()

def shutdown_session(exception=None):
    SessionLocal.remove()
