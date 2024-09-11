from flask_sqlalchemy import SQLAlchemy
from utils import safe_float
from database import db


class User(db.Model):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    user_details = db.Column(db.Boolean, default=False)

    claim_statuses = db.relationship('ClaimStatus', back_populates='user', cascade="all, delete-orphan")
    user_profile = db.relationship('UserProfile', back_populates='user', uselist=False)
    insurance_plans = db.relationship('InsurancePlans', back_populates='user')

class UserProfile(db.Model):
    __tablename__ = 'UserProfile'
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), primary_key=True)
    full_name = db.Column(db.String(255))
    DOB = db.Column(db.Date)
    age = db.Column(db.Integer)
    gender = db.Column(db.Enum('Male', 'Female'))
    phone_number = db.Column(db.String(20))
    district = db.Column(db.String(100))
    state = db.Column(db.String(100))
    occupation = db.Column(db.String(100))
    annual_income = db.Column(db.Numeric(10, 2))
    height = db.Column(db.Numeric(5, 2))
    weight = db.Column(db.Numeric(5, 2))

    user = db.relationship('User', back_populates='user_profile')

class HealthInformation(db.Model):
    __tablename__ = 'HealthInformation'
    health_info_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
    medical_history = db.Column(db.Text)
    family_medical_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    current_medications = db.Column(db.Text)

class LifestyleInformation(db.Model):
    __tablename__ = 'LifestyleInformation'
    lifestyle_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
    smoking_status = db.Column(db.Enum('Never', 'Former', 'Current'))
    alcohol_consumption = db.Column(db.Enum('None', 'Light', 'Moderate', 'Heavy'))
    physical_activity = db.Column(db.Enum('None', 'Light', 'Moderate', 'High'))
    family_history_CVD = db.Column(db.Boolean)
    family_history_diabetes = db.Column(db.Boolean)
    family_history_cancer = db.Column(db.Boolean)
    stress_level = db.Column(db.Enum('Low', 'Medium', 'High'))
    sleep_hours = db.Column(db.Integer)

class Prescription(db.Model):
    __tablename__ = 'Prescriptions'
    prescription_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id', ondelete='CASCADE'), nullable=False)
    clinic_name = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)
    file_link = db.Column(db.Text, nullable=False)

class MLModelData(db.Model):
    __tablename__ = 'MLModelData'
    model_data_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    Age = db.Column(db.Integer)
    Gender = db.Column(db.Enum('Male', 'Female', 'Unknown'))
    Height = db.Column(db.Numeric(5, 2))
    Weight = db.Column(db.Numeric(5, 2))
    BMI = db.Column(db.Numeric(5, 2), default=24.22)
    Systolic_BP = db.Column(db.Integer, default=120)
    Diastolic_BP = db.Column(db.Integer, default=80)
    Cholesterol_Total = db.Column(db.Integer, default=200)
    Cholesterol_HDL = db.Column(db.Integer, default=50)
    Cholesterol_LDL = db.Column(db.Integer, default=130)
    Triglycerides = db.Column(db.Integer, default=150)
    Blood_Glucose_Fasting = db.Column(db.Integer, default=90)
    HbA1c = db.Column(db.Numeric(3, 1), default=5.5)
    Smoking_Status = db.Column(db.Enum('Never', 'Former', 'Current'))
    Alcohol_Consumption = db.Column(db.Enum('None', 'Light', 'Moderate', 'Heavy'))
    Physical_Activity = db.Column(db.Enum('None', 'Light', 'Moderate', 'High'))
    Family_History_CVD = db.Column(db.Boolean)
    Family_History_Diabetes = db.Column(db.Boolean)
    Family_History_Cancer = db.Column(db.Boolean)
    Stress_Level = db.Column(db.Enum('Low', 'Medium', 'High'))
    Sleep_Hours = db.Column(db.Integer)
    Fruits_Veggies_Daily = db.Column(db.Integer, default=3)
    Creatinine = db.Column(db.Numeric(3, 1), default=1.0)
    eGFR = db.Column(db.Integer, default=90)
    ALT = db.Column(db.Integer, default=25)
    AST = db.Column(db.Integer, default=25)
    TSH = db.Column(db.Numeric(3, 1), default=2.0)
    T4 = db.Column(db.Numeric(3, 1), default=1.2)
    Vitamin_D = db.Column(db.Numeric(4, 1), default=30)
    Calcium = db.Column(db.Numeric(3, 1), default=9.5)
    Hemoglobin = db.Column(db.Numeric(4, 1), default=14)
    White_Blood_Cell_Count = db.Column(db.Numeric(4, 1), default=7.0)
    Platelet_Count = db.Column(db.Integer, default=250)
    C_Reactive_Protein = db.Column(db.Integer, default=2)
    Vitamin_B12 = db.Column(db.Integer, default=400)
    Folate = db.Column(db.Numeric(4, 1), default=10)
    Ferritin = db.Column(db.Integer, default=100)
    Uric_Acid = db.Column(db.Numeric(3, 1), default=5.0)
    PSA = db.Column(db.Numeric(3, 1), default=1.0)
    Bone_Density_T_Score = db.Column(db.Numeric(3, 1), default=0.0)

class ClaimStatus(db.Model):
    __tablename__ = 'ClaimStatus'
    claim_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), nullable=False)
    decision = db.Column(db.Enum('Claim Approved', 'Claim Cancelled', 'Claim in review'), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    bill_name = db.Column(db.Text, nullable=False)
    processed_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    user = db.relationship('User', back_populates='claim_statuses')


class PredictionResults(db.Model):
    __tablename__ = 'PredictionResults'
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'), primary_key=True)
    condition_name = db.Column(db.String(50), primary_key=True)
    probability = db.Column(db.Numeric(4, 2))
    risk_level = db.Column(db.Enum('Low', 'Medium', 'High'))

class InsurancePlans(db.Model):
    __tablename__ = 'InsurancePlans'
    plan_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
    company = db.Column(db.String(100))
    plan_name = db.Column(db.String(100))
    plan_type = db.Column(db.String(50))
    network_type = db.Column(db.String(20))
    monthly_premium = db.Column(db.Numeric(10, 2))
    annual_premium = db.Column(db.Numeric(10, 2))
    sum_insured = db.Column(db.Numeric(15, 2))
    deductible = db.Column(db.String(20))
    out_of_pocket_max = db.Column(db.String(20))
    effective_date = db.Column(db.Date)
    expiration_date = db.Column(db.Date)

    user = db.relationship('User', back_populates='insurance_plans')

class CoverageDetails(db.Model):
    __tablename__ = 'CoverageDetails'
    coverage_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('InsurancePlans.plan_id'))
    coverage_item = db.Column(db.String(255))

class Copayments(db.Model):
    __tablename__ = 'Copayments'
    copayment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('InsurancePlans.plan_id'))
    service = db.Column(db.String(100))
    amount = db.Column(db.String(20))

class AdditionalBenefits(db.Model):
    __tablename__ = 'AdditionalBenefits'
    benefit_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('InsurancePlans.plan_id'))
    benefit_description = db.Column(db.String(255))

class PolicyExclusions(db.Model):
    __tablename__ = 'PolicyExclusions'
    exclusion_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('InsurancePlans.plan_id'))
    general_exclusions = db.Column(db.Text)
    waiting_periods = db.Column(db.Text)


def fetch_user_data(user_id):
    # Fetch user-related data from database
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    lifestyle_info = LifestyleInformation.query.filter_by(user_id=user_id).first()

    if not user_profile or not lifestyle_info:
        raise ValueError(f"Missing profile or lifestyle information for user_id {user_id}")

    return user_profile, lifestyle_info

def map_tests_to_mlmodeldata(tests):
    # Map test results to the corresponding MLModelData fields
    mapping = {
        "Hemoglobin": "Hemoglobin",
        "White Blood Cell Count": "White_Blood_Cell_Count",
        "Platelet Count": "Platelet_Count",
        "BMI": "BMI",
        "Systolic BP": "Systolic_BP",
        "Diastolic BP": "Diastolic_BP",
        "Cholesterol (Total)": "Cholesterol_Total",
        "HDL": "Cholesterol_HDL",
        "LDL": "Cholesterol_LDL",
        "Triglycerides": "Triglycerides",
        "Blood Glucose Fasting": "Blood_Glucose_Fasting",
        "HbA1c": "HbA1c",
        "Creatinine": "Creatinine",
        "eGFR": "eGFR",
        "ALT": "ALT",
        "AST": "AST",
        "TSH": "TSH",
        "T4": "T4",
        "Vitamin D": "Vitamin_D",
        "Calcium": "Calcium",
        "C Reactive Protein": "C_Reactive_Protein",
        "Vitamin B12": "Vitamin_B12",
        "Folate": "Folate",
        "Ferritin": "Ferritin",
        "Uric Acid": "Uric_Acid",
        "PSA": "PSA",
        "Bone Density T Score": "Bone_Density_T_Score"
    }
    result = {}
    for test_name, value in tests.items():
        field_name = mapping.get(test_name)
        if field_name:
            result[field_name] = safe_float(value)
    return result
