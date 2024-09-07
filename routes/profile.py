from flask import Blueprint, request, jsonify
from models import db, UserProfile
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/user-profile', methods=['POST'])
def add_user_profile():
    data = request.get_json()
    dob = data.get('dob')
    dob_converted = datetime.strptime(dob, "%Y-%m-%d").date()
    user_profile = UserProfile(
        user_id=data['user_id'],
        full_name=data['full_name'],
        DOB=dob_converted,
        age=data['age'],
        gender=data['gender'],
        phone_number=data['phone_number'],
        district=data['district'],
        state=data['state'],
        occupation=data['occupation'],
        annual_income=data['annual_income'],
        height=data['height'],
        weight=data['weight']
    )
    db.session.add(user_profile)
    db.session.commit()
    return jsonify({'message': 'User profile added successfully'}), 201
