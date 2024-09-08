from flask import Blueprint, request, jsonify
from models import db, UserProfile
from datetime import datetime

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/user-profile', methods=['POST'])
def add_user_profile():
    data = request.get_json()
    user_id = data.get('user_id')

    # Convert DOB
    dob = data.get('dob')
    dob_converted = datetime.strptime(dob, "%Y-%m-%d").date()

    # Check if the user already has a profile
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()

    if user_profile:
        # Update existing user profile
        user_profile.full_name = data['full_name']
        user_profile.DOB = dob_converted
        user_profile.age = data['age']
        user_profile.gender = data['gender']
        user_profile.phone_number = data['phone_number']
        user_profile.district = data['district']
        user_profile.state = data['state']
        user_profile.occupation = data['occupation']
        user_profile.annual_income = data['annual_income']
        user_profile.height = data['height']
        user_profile.weight = data['weight']
        message = 'User profile updated successfully'
    else:
        # Create new user profile
        user_profile = UserProfile(
            user_id=user_id,
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
        message = 'User profile added successfully'

    db.session.commit()
    return jsonify({'message': message}), 201
