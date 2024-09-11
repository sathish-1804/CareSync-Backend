from flask import Blueprint, request, jsonify
from models import db, User, UserProfile, InsurancePlans
from utils import hash_password, check_password

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User already exists'}), 409

    hashed_password = hash_password(password)
    new_user = User(email=email, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'UserID': new_user.user_id, 'message': 'User registered successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    user = User.query.filter_by(email=email).first()

    if user and check_password(user.password_hash, password):
        return jsonify({'UserID': user.user_id, 'message': 'Login successful', 'user_details': user.user_details}), 200
    else:
        return jsonify({'message': 'Invalid email or password'}), 401

@auth_bp.route('/user-details-status/<int:user_id>', methods=['GET'])
def get_user_details_status(user_id):
    # Query User and UserProfile using correct joins, without including InsurancePlans
    user_data = db.session.query(User, UserProfile).join(
        UserProfile, User.user_id == UserProfile.user_id
    ).filter(User.user_id == user_id).first()
    
    if not user_data:
        return jsonify({'message': 'User not found'}), 404
    
    user, user_profile = user_data

    return jsonify({
        'UserID': user.user_id,
        'UserDetails': user.user_details,
        'FullName': user_profile.full_name
    }), 200
