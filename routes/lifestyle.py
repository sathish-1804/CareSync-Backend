from flask import Blueprint, request, jsonify
from models import db, LifestyleInformation, User

lifestyle_bp = Blueprint('lifestyle', __name__)

@lifestyle_bp.route('/lifestyle-information', methods=['POST'])
def add_lifestyle_information():
    data = request.get_json()
    user_id = data['user_id']

    # Check if the user already has lifestyle information
    lifestyle_info = LifestyleInformation.query.filter_by(user_id=user_id).first()

    if lifestyle_info:
        # Update existing lifestyle information
        lifestyle_info.smoking_status = data['smoking_status']
        lifestyle_info.alcohol_consumption = data['alcohol_consumption']
        lifestyle_info.physical_activity = data['physical_activity']
        lifestyle_info.family_history_CVD = data['family_history_CVD']
        lifestyle_info.family_history_diabetes = data['family_history_diabetes']
        lifestyle_info.family_history_cancer = data['family_history_cancer']
        lifestyle_info.stress_level = data['stress_level']
        lifestyle_info.sleep_hours = data['sleep_hours']
        message = 'Lifestyle information updated successfully'
    else:
        # Create new lifestyle information record
        lifestyle_info = LifestyleInformation(
            user_id=user_id,
            smoking_status=data['smoking_status'],
            alcohol_consumption=data['alcohol_consumption'],
            physical_activity=data['physical_activity'],
            family_history_CVD=data['family_history_CVD'],
            family_history_diabetes=data['family_history_diabetes'],
            family_history_cancer=data['family_history_cancer'],
            stress_level=data['stress_level'],
            sleep_hours=data['sleep_hours']
        )
        db.session.add(lifestyle_info)
        message = 'Lifestyle information added successfully'

    db.session.commit()
    return jsonify({'message': message}), 201
