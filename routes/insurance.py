from flask import Blueprint, jsonify
from models import db, User, UserProfile, HealthInformation, LifestyleInformation, MLModelData, PredictionResults, InsurancePlans, CoverageDetails, Copayments, AdditionalBenefits, PolicyExclusions
from datetime import date, timedelta
import random
import yaml

# Load YAML configuration
with open('config.yml', 'r') as file:
    insurance_config = yaml.safe_load(file)['insurance']

# Initialize blueprint
insurance_bp = Blueprint('insurance', __name__)

# Insurance Plan Generator
class InsurancePlanGenerator:
    def __init__(self):
        self.companies = insurance_config['companies']
        self.plan_types = insurance_config['plan_types']
        self.network_types = insurance_config['network_types']

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
        base_premium = insurance_config['base_premium'][coverage_type]
        age_factor = 1 + (user_profile.age - 18) * 0.02
        risk_factor = 1 + (risk_score * 0.5)
        premium = base_premium * age_factor * risk_factor
        return round(max(500, min(20000, premium)), 2)

    def _calculate_sum_insured(self, coverage_type, annual_income, risk_predictions):
        base_multiplier = insurance_config['base_multiplier'][coverage_type]
        risk_factor = 1.0
        high_risk_count = sum(1 for risk in risk_predictions if risk.risk_level == 'High')
        risk_factor += (high_risk_count * 0.1)
        
        sum_insured = min(float(annual_income) * base_multiplier * risk_factor, 50000000)
        return round(sum_insured, -5)

    def _calculate_deductible(self, coverage_type, risk_score):
        base_deductible = insurance_config['base_deductible'][coverage_type]
        risk_adjusted_deductible = base_deductible * (1 + risk_score)
        return f"₹{int(risk_adjusted_deductible)}"

    def _calculate_out_of_pocket_max(self, coverage_type, risk_score):
        base_oop = insurance_config['base_out_of_pocket_max'][coverage_type]
        risk_adjusted_oop = base_oop * (1 + (risk_score * 0.5))
        return f"₹{int(risk_adjusted_oop)}"

    def _generate_copayments(self, coverage_type, risk_score):
        base_copay = insurance_config['base_copay'][coverage_type]
        risk_adjusted_copay = int(base_copay * (1 + (risk_score * 0.5)))
        return {
            "Primary Care Visit": f"₹{risk_adjusted_copay}",
            "Specialist Visit": f"₹{risk_adjusted_copay * 2}",
            "Emergency Room Visit": f"₹{risk_adjusted_copay * 5}",
            "Generic Prescription Drugs": f"₹{risk_adjusted_copay // 2}"
        }

    def _generate_coverage_details(self, coverage_type, network_type, risk_predictions):
        coverage = insurance_config['coverage']['basic']
        if network_type == "PPO":
            coverage.extend(insurance_config['coverage']['additional'])
        if coverage_type in ["Gold", "Platinum"]:
            coverage.extend(insurance_config['coverage']['gold_platinum'])
        for risk in risk_predictions:
            if risk.risk_level == 'High':
                coverage.append(f"Enhanced coverage for {risk.condition_name.replace('_', ' ')}")
        return coverage

    def _determine_benefits(self, coverage_type, risk_score, risk_predictions):
        all_benefits = insurance_config['benefits']
        num_benefits = {"Bronze": 2, "Silver": 3, "Gold": 4, "Platinum": 5}[coverage_type]
        benefits = random.sample(all_benefits, num_benefits)
        if any(risk.condition_name == 'Heart_Disease_Risk' and risk.risk_level == 'High' for risk in risk_predictions):
            benefits.append("Cardiovascular Health Program")
        if any(risk.condition_name == 'Diabetes' and risk.risk_level == 'High' for risk in risk_predictions):
            benefits.append("Diabetes Management Program")
        if any(risk.condition_name == 'Cancer_Risk' and risk.risk_level == 'High' for risk in risk_predictions):
            benefits.append("Cancer Screening Program")
        return benefits

    def _generate_general_exclusions(self):
        exclusions = insurance_config['exclusions']
        return random.sample(exclusions, 3)

    def _generate_waiting_periods(self, risk_predictions):
        waiting_periods = {
            "General Waiting Period": insurance_config['waiting_periods']['general'],
            "Pre-existing Diseases": insurance_config['waiting_periods']['pre_existing_high'] if any(risk.risk_level == 'High' for risk in risk_predictions) else insurance_config['waiting_periods']['pre_existing_low'],
            "Specific Procedures": insurance_config['waiting_periods']['specific_procedures']
        }
        return waiting_periods

@insurance_bp.route('/generate_plan/<int:user_id>', methods=['GET'])
def generate_plan(user_id):
    # Retrieve user details from the database
    user = User.query.filter_by(user_id=user_id).first()
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()
    health_info = HealthInformation.query.filter_by(user_id=user_id).first()
    lifestyle_info = LifestyleInformation.query.filter_by(user_id=user_id).first()
    ml_model_data = MLModelData.query.filter_by(user_id=user_id).first()
    risk_predictions = PredictionResults.query.filter_by(user_id=user_id).all()

    if not user_profile or not health_info or not lifestyle_info or not ml_model_data or not risk_predictions:
        return jsonify({"error": "User data is incomplete"}), 400

    # Check if an existing insurance plan exists for the user
    existing_plan = InsurancePlans.query.filter_by(user_id=user_id).first()

    # Generate insurance plan
    try:
        generator = InsurancePlanGenerator()
        plan = generator.generate_plan(user_profile, health_info, lifestyle_info, ml_model_data, risk_predictions)

        if existing_plan:
            # Update the existing insurance plan
            existing_plan.company = plan['company']
            existing_plan.plan_name = plan['plan_name']
            existing_plan.plan_type = plan['plan_type']
            existing_plan.network_type = plan['network_type']
            existing_plan.monthly_premium = plan['monthly_premium']
            existing_plan.annual_premium = plan['annual_premium']
            existing_plan.sum_insured = plan['sum_insured']
            existing_plan.deductible = plan['deductible']
            existing_plan.out_of_pocket_max = plan['out_of_pocket_max']
            existing_plan.effective_date = plan['effective_date']
            existing_plan.expiration_date = plan['expiration_date']
            db.session.commit()

            # Clear and update related details
            CoverageDetails.query.filter_by(plan_id=existing_plan.plan_id).delete()
            Copayments.query.filter_by(plan_id=existing_plan.plan_id).delete()
            AdditionalBenefits.query.filter_by(plan_id=existing_plan.plan_id).delete()
            PolicyExclusions.query.filter_by(plan_id=existing_plan.plan_id).delete()

        else:
            # Create a new insurance plan
            existing_plan = InsurancePlans(
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
                effective_date=plan['effective_date'],
                expiration_date=plan['expiration_date']
            )
            db.session.add(existing_plan)
            db.session.commit()

        # Insert related details
        coverage_details_list = []
        for item in plan['coverage_details']:
            coverage_detail = CoverageDetails(plan_id=existing_plan.plan_id, coverage_item=item)
            db.session.add(coverage_detail)
            coverage_details_list.append(item)

        copayments_list = []
        for service, amount in plan['copayments'].items():
            copayment = Copayments(plan_id=existing_plan.plan_id, service=service, amount=amount)
            db.session.add(copayment)
            copayments_list.append({'service': service, 'amount': amount})

        additional_benefits_list = []
        for benefit in plan['additional_benefits']:
            additional_benefit = AdditionalBenefits(plan_id=existing_plan.plan_id, benefit_description=benefit)
            db.session.add(additional_benefit)
            additional_benefits_list.append(benefit)

        policy_exclusion = PolicyExclusions(
            plan_id=existing_plan.plan_id,
            general_exclusions=', '.join(plan['general_exclusions']),
            waiting_periods=', '.join([f"{k}: {v} months" for k, v in plan['waiting_periods'].items()])
        )
        db.session.add(policy_exclusion)
        db.session.commit()

        user.user_details = True
        db.session.commit()

        # Prepare the JSON response with all insurance details
        response = {
            'message': 'Insurance plan generated successfully',
            'insurance_details': {
                'company': plan['company'],
                'plan_name': plan['plan_name'],
                'plan_type': plan['plan_type'],
                'network_type': plan['network_type'],
                'monthly_premium': plan['monthly_premium'],
                'annual_premium': plan['annual_premium'],
                'sum_insured': plan['sum_insured'],
                'deductible': plan['deductible'],
                'out_of_pocket_max': plan['out_of_pocket_max'],
                'effective_date': plan['effective_date'].strftime('%Y-%m-%d'),
                'expiration_date': plan['expiration_date'].strftime('%Y-%m-%d'),
                'coverage_details': coverage_details_list,
                'copayments': copayments_list,
                'additional_benefits': additional_benefits_list,
                'general_exclusions': plan['general_exclusions'],
                'waiting_periods': plan['waiting_periods']
            }
        }
        
        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred while generating the insurance plan: {str(e)}"}), 500