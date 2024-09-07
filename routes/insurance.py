from flask import Blueprint, jsonify
from models import db, UserProfile, HealthInformation, LifestyleInformation, MLModelData, PredictionResults, InsurancePlans, CoverageDetails, Copayments, AdditionalBenefits, PolicyExclusions
from datetime import date, timedelta
import random
from utils import upload_insurance
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Initialize blueprint
insurance_bp = Blueprint('insurance', __name__)

# Insurance Plan Generator
class InsurancePlanGenerator:
    def __init__(self):
        self.companies = ["LIC Health", "Star Health", "Bajaj Allianz", "ICICI Lombard", "Apollo Munich"]
        self.plan_types = ["Individual",  "Senior Citizen", "Critical Illness"]
        self.network_types = ["HMO", "PPO", "EPO"]

    def generate_plan(self, user_profile, health_info, lifestyle_info, ml_model_data, risk_predictions):
        plan = self._generate_fallback_plan(user_profile, health_info, lifestyle_info, ml_model_data, risk_predictions)
        return plan

    def _generate_fallback_plan(self, user_profile, health_info, lifestyle_info, ml_model_data, risk_predictions):
        risk_score = self._calculate_risk_score(user_profile, health_info, lifestyle_info, ml_model_data, risk_predictions)
        coverage_type = self._determine_coverage_type(risk_score, user_profile.annual_income)
        network_type = random.choice(self.network_types)

        plan = {
            "company": random.choice(self.companies),
            "plan_name": f"{coverage_type} {network_type} Health Shield",
            "plan_type": self._determine_plan_type(user_profile, risk_predictions),
            "network_type": network_type,
            "monthly_premium": self._calculate_premium(risk_score, coverage_type, user_profile, risk_predictions),
            "sum_insured": self._calculate_sum_insured(coverage_type, user_profile.annual_income, risk_predictions),
            "deductible": self._calculate_deductible(coverage_type, risk_score),
            "out_of_pocket_max": self._calculate_out_of_pocket_max(coverage_type, risk_score),
            "copayments": self._generate_copayments(coverage_type, risk_score),
            "coverage_details": self._generate_coverage_details(coverage_type, network_type, risk_predictions),
            "additional_benefits": self._determine_benefits(coverage_type, risk_score, risk_predictions),
            "policy_number": self._generate_policy_number(),
            "effective_date": date.today(),
            "expiration_date": date.today() + timedelta(days=365),
            "general_exclusions": self._generate_general_exclusions(),
            "waiting_periods": self._generate_waiting_periods(risk_predictions)
        }
        plan["annual_premium"] = plan["monthly_premium"] * 12
        return plan

    def _calculate_risk_score(self, user_profile, health_info, lifestyle_info, ml_model_data, risk_predictions):
        base_score = 0.5
        high_risk_count = sum(1 for risk in risk_predictions if risk.risk_level == 'High')
        medium_risk_count = sum(1 for risk in risk_predictions if risk.risk_level == 'Medium')
        risk_score = base_score + (high_risk_count * 0.1) + (medium_risk_count * 0.05)
        if lifestyle_info.smoking_status != "Never":
            risk_score += 0.1
        if lifestyle_info.alcohol_consumption in ["Moderate", "Heavy"]:
            risk_score += 0.05
        if ml_model_data.BMI > 30 or ml_model_data.BMI < 18.5:
            risk_score += 0.05
        if ml_model_data.Systolic_BP > 140 or ml_model_data.Diastolic_BP > 90:
            risk_score += 0.05
        if user_profile.age > 50:
            risk_score += 0.1
        elif user_profile.age > 40:
            risk_score += 0.05
        if health_info.medical_history != "No major issues":
            risk_score += 0.1
        return min(risk_score, 1.0)

    def _determine_coverage_type(self, risk_score, annual_income):
        if risk_score < 0.3 and annual_income > 1500000:
            return "Platinum"
        elif risk_score < 0.5 and annual_income > 1000000:
            return "Gold"
        elif risk_score < 0.7 and annual_income > 500000:
            return "Silver"
        else:
            return "Bronze"

    def _determine_plan_type(self, user_profile, risk_predictions):
        if user_profile.age >= 60:
            return "Senior Citizen"
        if any(risk.risk_level == 'High' for risk in risk_predictions):
            return "Critical Illness"
        return "Individual"

    def _calculate_premium(self, risk_score, coverage_type, user_profile, risk_predictions):
        base_premium = {"Bronze": 1000, "Silver": 2000, "Gold": 3500, "Platinum": 5000}[coverage_type]
        age_factor = 1 + (user_profile.age - 18) * 0.02
        risk_factor = 1 + (risk_score * 0.5)
        premium = base_premium * age_factor * risk_factor
        return round(max(500, min(20000, premium)), 2)

    def _calculate_sum_insured(self, coverage_type, annual_income, risk_predictions):
        base_multiplier = {"Bronze": 3, "Silver": 4, "Gold": 5, "Platinum": 6}[coverage_type]
        risk_factor = 1.0
        high_risk_count = sum(1 for risk in risk_predictions if risk.risk_level == 'High')
        risk_factor += (high_risk_count * 0.1)
        
        sum_insured = min(float(annual_income) * base_multiplier * risk_factor, 50000000)
        return round(sum_insured, -5)


    def _calculate_deductible(self, coverage_type, risk_score):
        base_deductible = {"Bronze": 50000, "Silver": 25000, "Gold": 15000, "Platinum": 10000}[coverage_type]
        risk_adjusted_deductible = base_deductible * (1 + risk_score)
        return f"₹{int(risk_adjusted_deductible)}"

    def _calculate_out_of_pocket_max(self, coverage_type, risk_score):
        base_oop = {"Bronze": 300000, "Silver": 200000, "Gold": 150000, "Platinum": 100000}[coverage_type]
        risk_adjusted_oop = base_oop * (1 + (risk_score * 0.5))
        return f"₹{int(risk_adjusted_oop)}"

    def _generate_copayments(self, coverage_type, risk_score):
        base_copay = {"Bronze": 500, "Silver": 400, "Gold": 300, "Platinum": 200}[coverage_type]
        risk_adjusted_copay = int(base_copay * (1 + (risk_score * 0.5)))
        return {
            "Primary Care Visit": f"₹{risk_adjusted_copay}",
            "Specialist Visit": f"₹{risk_adjusted_copay * 2}",
            "Emergency Room Visit": f"₹{risk_adjusted_copay * 5}",
            "Generic Prescription Drugs": f"₹{risk_adjusted_copay // 2}"
        }

    def _generate_coverage_details(self, coverage_type, network_type, risk_predictions):
        coverage = [
            "Inpatient Hospitalization",
            "Outpatient Procedures",
            "Emergency Services",
            "Preventive Care (100% covered)",
            "Prescription Drugs",
            "Mental Health Services",
            "Maternity and Newborn Care"
        ]
        if network_type == "PPO":
            coverage.append("Out-of-network Care (with higher costs)")
        if coverage_type in ["Gold", "Platinum"]:
            coverage.extend(["Dental Check-ups", "Vision Care"])
        for risk in risk_predictions:
            if risk.risk_level == 'High':
                coverage.append(f"Enhanced coverage for {risk.condition_name.replace('_', ' ')}")
        return coverage

    def _determine_benefits(self, coverage_type, risk_score, risk_predictions):
        all_benefits = [
            "Telemedicine Services",
            "Wellness Programs",
            "Health Coaching",
            "Gym Membership Discounts",
            "Alternative Medicine Coverage",
            "International Emergency Coverage",
            "Second Opinion Services",
            "Chronic Disease Management Programs"
        ]
        num_benefits = {"Bronze": 2, "Silver": 3, "Gold": 4, "Platinum": 5}[coverage_type]
        benefits = random.sample(all_benefits, num_benefits)
        if any(risk.condition_name == 'Heart_Disease_Risk' and risk.risk_level == 'High' for risk in risk_predictions):
            benefits.append("Cardiovascular Health Program")
        if any(risk.condition_name == 'Diabetes' and risk.risk_level == 'High' for risk in risk_predictions):
            benefits.append("Diabetes Management Program")
        if any(risk.condition_name == 'Cancer_Risk' and risk.risk_level == 'High' for risk in risk_predictions):
            benefits.append("Cancer Screening Program")
        return benefits

    def _generate_policy_number(self):
        return f"POL-{random.randint(100000, 999999)}"

    def _generate_general_exclusions(self):
        exclusions = [
            "Pre-existing conditions not disclosed at the time of policy purchase",
            "Cosmetic treatments",
            "Self-inflicted injuries",
            "Injuries resulting from war or terrorist activities",
            "Experimental treatments",
            "Injuries from hazardous sports without prior approval"
        ]
        return random.sample(exclusions, 3)

    def _generate_waiting_periods(self, risk_predictions):
        waiting_periods = {
            "General Waiting Period": 30,
            "Pre-existing Diseases": 48 if any(risk.risk_level == 'High' for risk in risk_predictions) else 36,
            "Specific Procedures": 24
        }
        return waiting_periods


    def generate_plan_pdf(self, plan, user_profile):
        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle(f"{plan['plan_name']} - Insurance Plan")

        # Adding CareSync header
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(200, 750, "CareSync Insurance Plan")

        # Add user profile details
        pdf.setFont("Helvetica-Bold", 14)
        y = 720
        pdf.drawString(50, y, "User Profile Details:")
        pdf.setFont("Helvetica", 12)
        y -= 20
        pdf.drawString(50, y, f"Full Name: {user_profile.full_name}")
        y -= 20
        pdf.drawString(50, y, f"DOB: {user_profile.DOB}")
        y -= 20
        pdf.drawString(50, y, f"Age: {user_profile.age}")
        y -= 20
        pdf.drawString(50, y, f"Gender: {user_profile.gender}")
        y -= 20
        pdf.drawString(50, y, f"Phone Number: {user_profile.phone_number}")
        y -= 20
        pdf.drawString(50, y, f"District: {user_profile.district}")
        y -= 20
        pdf.drawString(50, y, f"State: {user_profile.state}")
        y -= 20
        pdf.drawString(50, y, f"Occupation: {user_profile.occupation}")
        y -= 40  # Add extra space before the plan details

        # Add insurance plan details
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Insurance Plan Details:")
        pdf.setFont("Helvetica", 12)
        y -= 20
        pdf.drawString(50, y, f"Company: {plan['company']}")
        y -= 20
        pdf.drawString(50, y, f"Plan Name: {plan['plan_name']}")
        y -= 20
        pdf.drawString(50, y, f"Plan Type: {plan['plan_type']}")
        y -= 20
        pdf.drawString(50, y, f"Network Type: {plan['network_type']}")
        y -= 20
        pdf.drawString(50, y, f"Monthly Premium: ₹{plan['monthly_premium']}")
        y -= 20
        pdf.drawString(50, y, f"Annual Premium: ₹{plan['annual_premium']}")
        y -= 20
        pdf.drawString(50, y, f"Sum Insured: ₹{plan['sum_insured']}")
        y -= 20
        pdf.drawString(50, y, f"Deductible: {plan['deductible']}")
        y -= 20
        pdf.drawString(50, y, f"Out of Pocket Max: {plan['out_of_pocket_max']}")
        y -= 20
        pdf.drawString(50, y, f"Policy Number: {plan['policy_number']}")
        y -= 20
        pdf.drawString(50, y, f"Effective Date: {plan['effective_date']}")
        y -= 20
        pdf.drawString(50, y, f"Expiration Date: {plan['expiration_date']}")
        y -= 20

        # Coverage Details
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Coverage Details:")
        pdf.setFont("Helvetica", 12)
        y -= 20
        for item in plan['coverage_details']:
            pdf.drawString(70, y, f"- {item}")
            y -= 15

        # Additional Benefits
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Additional Benefits:")
        pdf.setFont("Helvetica", 12)
        y -= 20
        for benefit in plan['additional_benefits']:
            pdf.drawString(70, y, f"- {benefit}")
            y -= 15

        # Co-payments
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Co-payments:")
        pdf.setFont("Helvetica", 12)
        y -= 20
        for service, amount in plan['copayments'].items():
            pdf.drawString(70, y, f"- {service}: {amount}")
            y -= 15

        # General Exclusions
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "General Exclusions:")
        pdf.setFont("Helvetica", 12)
        y -= 20
        for exclusion in plan['general_exclusions']:
            pdf.drawString(70, y, f"- {exclusion}")
            y -= 15

        # Waiting Periods
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Waiting Periods:")
        pdf.setFont("Helvetica", 12)
        y -= 20
        for k, v in plan['waiting_periods'].items():
            pdf.drawString(70, y, f"- {k}: {v} months")
            y -= 15

        pdf.save()
        buffer.seek(0)

        return buffer, f"{plan['plan_name'].replace(' ', '_')}_insurance_plan.pdf"


@insurance_bp.route('/generate_plan/<int:user_id>', methods=['GET'])
def generate_plan(user_id):
    # Retrieve user details from the database
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    health_info = HealthInformation.query.filter_by(user_id=user_id).first()
    lifestyle_info = LifestyleInformation.query.filter_by(user_id=user_id).first()
    ml_model_data = MLModelData.query.filter_by(user_id=user_id).first()
    risk_predictions = PredictionResults.query.filter_by(user_id=user_id).all()

    if not user_profile or not health_info or not lifestyle_info or not ml_model_data or not risk_predictions:
        return jsonify({"error": "User data is incomplete"}), 400

    # Generate insurance plan
    generator = InsurancePlanGenerator()
    plan = generator.generate_plan(user_profile, health_info, lifestyle_info, ml_model_data, risk_predictions)

    # Generate the PDF for the plan
    pdf_buffer, pdf_filename = generator.generate_plan_pdf(plan, user_profile)
    
    # Upload the PDF to Azure Cloud and get the file link
    file_link = upload_insurance(pdf_buffer, pdf_filename)
    
    # Insert generated plan into the database
    insurance_plan = InsurancePlans(
        user_id=user_id,
        company=plan['company'],
        plan_name=plan['plan_name'],
        plan_type=plan['plan_type'],
        network_type=plan['network_type'],
        monthly_premium=plan['monthly_premium'],
        annual_premium=plan['annual_premium'],
        sum_insured=plan['sum_insured'],
        deductible=plan['deductible'],
        out_of_pocket_max=plan['out_of_pocket_max'],
        policy_number=plan['policy_number'],
        effective_date=plan['effective_date'],
        expiration_date=plan['expiration_date'],
        file_link=file_link  # Store the file link
    )
    db.session.add(insurance_plan)
    db.session.commit()

    # Insert related details
    for item in plan['coverage_details']:
        coverage_detail = CoverageDetails(plan_id=insurance_plan.plan_id, coverage_item=item)
        db.session.add(coverage_detail)

    for service, amount in plan['copayments'].items():
        copayment = Copayments(plan_id=insurance_plan.plan_id, service=service, amount=amount)
        db.session.add(copayment)

    for benefit in plan['additional_benefits']:
        additional_benefit = AdditionalBenefits(plan_id=insurance_plan.plan_id, benefit_description=benefit)
        db.session.add(additional_benefit)

    policy_exclusion = PolicyExclusions(
        plan_id=insurance_plan.plan_id,
        general_exclusions=', '.join(plan['general_exclusions']),
        waiting_periods=', '.join([f"{k}: {v} months" for k, v in plan['waiting_periods'].items()])
    )
    db.session.add(policy_exclusion)
    db.session.commit()

    # Return generated plan details as JSON
    plan['file_link'] = file_link  # Include the file link in the response
    return jsonify({'message': 'Insurance plan generated successfully', 'file_link': file_link}), 200