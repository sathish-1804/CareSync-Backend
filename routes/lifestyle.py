from flask import Blueprint, request, jsonify
from models import db, LifestyleInformation, User

lifestyle_bp = Blueprint('lifestyle', __name__)

@lifestyle_bp.route('/lifestyle-information', methods=['POST'])
def add_lifestyle_information():
    data = request.get_json()
    user_id = data['user_id']
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
    user = User.query.filter_by(user_id=user_id).first()
    user.user_details = True

    db.session.add(lifestyle_info)
    db.session.commit()
    return jsonify({'message': 'Lifestyle information added successfully'}), 201
