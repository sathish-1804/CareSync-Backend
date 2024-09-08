from flask import Blueprint, request, jsonify
from models import db, HealthInformation

health_bp = Blueprint('health', __name__)

@health_bp.route('/health-information', methods=['POST'])
def add_health_information():
    data = request.get_json()
    user_id = data.get('user_id')

    # Check if the user already has health information
    health_info = HealthInformation.query.filter_by(user_id=user_id).first()

    if health_info:
        # Update existing health information
        health_info.medical_history = data['medical_history']
        health_info.allergies = data['allergies']
        health_info.family_medical_history = data['family_medical_history']
        health_info.current_medications = data['current_medications']
        message = 'Health information updated successfully'
    else:
        # Create new health information record
        health_info = HealthInformation(
            user_id=user_id,
            medical_history=data['medical_history'],
            allergies=data['allergies'],
            family_medical_history=data['family_medical_history'],
            current_medications=data['current_medications']
        )
        db.session.add(health_info)
        message = 'Health information added successfully'

    db.session.commit()
    return jsonify({'message': message}), 201
