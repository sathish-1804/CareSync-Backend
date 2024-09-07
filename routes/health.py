from flask import Blueprint, request, jsonify
from models import db, HealthInformation

health_bp = Blueprint('health', __name__)

@health_bp.route('/health-information', methods=['POST'])
def add_health_information():
    data = request.get_json()
    health_info = HealthInformation(
        user_id=data['user_id'],
        medical_history=data['medical_history'],
        allergies=data['allergies'],
        family_medical_history=data['family_medical_history'],
        current_medications=data['current_medications']
    )
    db.session.add(health_info)
    db.session.commit()
    return jsonify({'message': 'Health information added successfully'}), 201
