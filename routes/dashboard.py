from flask import Blueprint, jsonify, request
from models import db, UserProfile, HealthInformation, LifestyleInformation, MLModelData, Prescription, ClaimStatus, InsurancePlans
from datetime import datetime, date
from sqlalchemy import func
import google.generativeai as genai
import os

# Load environment variables for AI API keys
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash-latest')

dashboard_bp = Blueprint('dashboard', __name__)

def generate_health_tip(user_profile, lifestyle_info):
    prompt = f"""
    Based on the following user profile and lifestyle data, generate a personalized health improvement tip.
    User Profile:
    - Age: {user_profile.age}
    - Gender: {user_profile.gender}
    - Height: {user_profile.height} cm
    - Weight: {user_profile.weight} kg

    Lifestyle Information:
    - Smoking Status: {lifestyle_info.smoking_status}
    - Alcohol Consumption: {lifestyle_info.alcohol_consumption}
    - Physical Activity: {lifestyle_info.physical_activity}
    - Stress Level: {lifestyle_info.stress_level}
    - Sleep Hours: {lifestyle_info.sleep_hours}

    Provide a concise and actionable health tip for the user. Below 200 characters
    """
    try:
        response = model.generate_content(prompt)

        return response.text.strip()
    except Exception as e:
        print(f"AI error: {e}")
        return "Stay active and maintain a balanced diet for optimal health."

@dashboard_bp.route('/dashboard/<int:user_id>', methods=['GET'])
def get_dashboard_data(user_id):
    try:
        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        lifestyle_info = LifestyleInformation.query.filter_by(user_id=user_id).first()
        ml_model_data = MLModelData.query.filter_by(user_id=user_id).first()
        prescriptions = Prescription.query.filter_by(user_id=user_id).order_by(Prescription.date.desc()).first()
        claims = ClaimStatus.query.filter_by(user_id=user_id).all()
        insurance = InsurancePlans.query.filter_by(user_id=user_id).all()

        if not user_profile or not lifestyle_info or not ml_model_data:
            return jsonify({"error": "User data is incomplete"}), 400

        # Insurance count and expiration date
        insurance_count = len(insurance)
        active_insurance = max(insurance, key=lambda x: x.expiration_date) if insurance else None
        insurance_expiration = active_insurance.expiration_date.strftime('%Y-%m-%d') if active_insurance else None

        # Claims status counts
        claims_approved = len([claim for claim in claims if claim.decision == 'Claim Approved'])
        claims_in_review = len([claim for claim in claims if claim.decision == 'Claim in review'])
        claims_rejected = len([claim for claim in claims if claim.decision == 'Claim Cancelled'])

        # Last uploaded prescription date
        last_prescription_date = prescriptions.date.strftime('%Y-%m-%d') if prescriptions else None

        # Calculate overall health percentage
        health_percentage = calculate_health_percentage(ml_model_data)

        # Determine health status
        health_status = determine_health_status(health_percentage)

        # Generate AI-based health tip
        health_tip = generate_health_tip(user_profile, lifestyle_info)

        # Identify risk contributors
        risk_contributors = identify_risk_contributors(ml_model_data, lifestyle_info)

        return jsonify({
            "insurance_count": insurance_count,
            "insurance_expiration": insurance_expiration,
            "claims": {
                "approved": claims_approved,
                "in_review": claims_in_review,
                "rejected": claims_rejected
            },
            "last_prescription_date": last_prescription_date,
            "health_profile": {
                "percentage": health_percentage,
                "status": health_status
            },
            "tip": health_tip,
            "risk_contributors": risk_contributors
        }), 200

    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        return jsonify({"error": str(e)}), 500

def calculate_health_percentage(ml_model_data):
    # A simplified way to calculate health percentage
    # Modify as needed based on specific health metrics from ml_model_data
    try:
        bmi = float(ml_model_data.BMI) if ml_model_data.BMI else 24.22
        systolic_bp = float(ml_model_data.Systolic_BP) if ml_model_data.Systolic_BP else 120
        diastolic_bp = float(ml_model_data.Diastolic_BP) if ml_model_data.Diastolic_BP else 80
        cholesterol_total = float(ml_model_data.Cholesterol_Total) if ml_model_data.Cholesterol_Total else 200

        # Simple scoring based on common health metrics
        health_score = 100

        if bmi < 18.5 or bmi > 24.9:
            health_score -= 10
        if systolic_bp > 130 or diastolic_bp > 85:
            health_score -= 10
        if cholesterol_total > 240:
            health_score -= 10

        return max(min(health_score, 100), 0)  # Clamp between 0 and 100

    except Exception as e:
        print(f"Error calculating health percentage: {e}")
        return 50  # Default percentage

def determine_health_status(health_percentage):
    if health_percentage >= 80:
        return "Optimal"
    elif health_percentage >= 50:
        return "Moderate"
    else:
        return "Needs Attention"

def identify_risk_contributors(ml_model_data, lifestyle_info):
    contributors = []

    if ml_model_data.BMI and (ml_model_data.BMI < 18.5 or ml_model_data.BMI > 24.9):
        contributors.append("BMI out of normal range")

    if ml_model_data.Systolic_BP and ml_model_data.Systolic_BP > 130:
        contributors.append("High Blood Pressure")

    if lifestyle_info.smoking_status != 'Never':
        contributors.append("Smoking")

    if lifestyle_info.alcohol_consumption in ['Moderate', 'Heavy']:
        contributors.append("High Alcohol Consumption")

    if lifestyle_info.physical_activity in ['None', 'Light']:
        contributors.append("Low Physical Activity")

    return contributors if contributors else ["No significant risk contributors identified"]
