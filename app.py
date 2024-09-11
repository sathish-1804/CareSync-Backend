from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from models import db  # Ensure this imports the single SQLAlchemy instance
from routes.auth import auth_bp
from routes.profile import profile_bp
from routes.health import health_bp
from routes.lifestyle import lifestyle_bp
from routes.insurance import insurance_bp
from routes.prescription import prescription_bp
from routes.context import context_bp
from ocr import ocr_bp
from routes.claim import claim_bp
from routes.dashboard import dashboard_bp
from database import init_db, shutdown_session

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and migration
init_db(app)  # This should call db.init_app(app) internally
migrate = Migrate(app, db)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(health_bp)
app.register_blueprint(lifestyle_bp)
app.register_blueprint(prescription_bp)
app.register_blueprint(context_bp)
app.register_blueprint(insurance_bp, url_prefix='/insurance')
app.register_blueprint(ocr_bp, url_prefix='/ocr')
app.register_blueprint(claim_bp, url_prefix='/claim')
app.register_blueprint(dashboard_bp)

@app.route('/')
def home():
    return jsonify(message="API Working"), 200

# Cleanup database sessions after each request
@app.teardown_appcontext
def shutdown_session_on_teardown(exception=None):
    shutdown_session(exception)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
