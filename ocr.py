from flask import Blueprint, request, jsonify
from PIL import Image
from io import BytesIO
import base64
import os
import google.generativeai as genai
from models import db, MLModelData, fetch_user_data, map_tests_to_mlmodeldata
from utils import safe_float, safe_int, clean_json_response
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Initialize blueprint
ocr_bp = Blueprint('ocr', __name__)

# Configure Generative AI API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash-latest')

@ocr_bp.route('/process_report', methods=['POST'])
def process_report():
    try:
        user_id = request.form.get('user_id')
        file = request.files.get('file')

        if not user_id or not file:
            return jsonify({"error": "Missing user_id or file"}), 400

        pdf_data = file.read()
        pdf_base64 = base64.b64encode(BytesIO(pdf_data).getvalue()).decode('utf-8')

        prompt = """
        Perform optical character recognition on the input PDF and extract relevant medical test results.
        Provide the output in JSON format, matching the field names exactly as listed.
        """

        genai_response = model.generate_content([prompt, {"mime_type": "application/pdf", "data": pdf_base64}])

        if not genai_response or not genai_response.text:
            return jsonify({"error": "No response from Gemini API or response is empty."}), 500

        extracted_fields = clean_json_response(genai_response.text.strip())
        if extracted_fields is None:
            return jsonify({"error": "Failed to parse the API response."}), 500

        user_profile, lifestyle_info = fetch_user_data(int(user_id))
        test_data = map_tests_to_mlmodeldata(extracted_fields)

        ml_model_data = MLModelData(
            user_id=user_id,
            Age=safe_int(user_profile.age),
            Gender=user_profile.gender,
            Height=safe_float(user_profile.height),
            Weight=safe_float(user_profile.weight),
            BMI=safe_float(test_data.get("BMI", user_profile.weight / ((user_profile.height / 100) ** 2) if user_profile.height else 1)),
            Systolic_BP=safe_int(test_data.get("Systolic_BP", 120)),
            Diastolic_BP=safe_int(test_data.get("Diastolic_BP", 80)),
            Cholesterol_Total=safe_int(test_data.get("Cholesterol_Total", 200)),
            Cholesterol_HDL=safe_int(test_data.get("Cholesterol_HDL", 50)),
            Cholesterol_LDL=safe_int(test_data.get("Cholesterol_LDL", 130)),
            Triglycerides=safe_int(test_data.get("Triglycerides", 150)),
            Blood_Glucose_Fasting=safe_int(test_data.get("Blood_Glucose_Fasting", 90)),
            HbA1c=safe_float(test_data.get("HbA1c", 5.5)),
            Smoking_Status=lifestyle_info.smoking_status,
            Alcohol_Consumption=lifestyle_info.alcohol_consumption,
            Physical_Activity=lifestyle_info.physical_activity,
            Family_History_CVD=lifestyle_info.family_history_CVD,
            Family_History_Diabetes=lifestyle_info.family_history_diabetes,
            Family_History_Cancer=lifestyle_info.family_history_cancer,
            Stress_Level=lifestyle_info.stress_level,
            Sleep_Hours=safe_int(lifestyle_info.sleep_hours),
            Fruits_Veggies_Daily=safe_int(test_data.get("Fruits_Veggies_Daily", 3)),
            Creatinine=safe_float(test_data.get("Creatinine", 1.0)),
            eGFR=safe_int(test_data.get("eGFR", 90)),
            ALT=safe_int(test_data.get("ALT", 25)),
            AST=safe_int(test_data.get("AST", 25)),
            TSH=safe_float(test_data.get("TSH", 2.0)),
            T4=safe_float(test_data.get("T4", 1.2)),
            Vitamin_D=safe_float(test_data.get("Vitamin_D", 30.0)),
            Calcium=safe_float(test_data.get("Calcium", 9.5)),
            Hemoglobin=safe_float(test_data.get("Hemoglobin", 16.3)),
            White_Blood_Cell_Count=safe_float(test_data.get("White_Blood_Cell_Count", 5.2)),
            Platelet_Count=safe_int(test_data.get("Platelet_Count", 321)),
            C_Reactive_Protein=safe_int(test_data.get("C_Reactive_Protein", 2)),
            Vitamin_B12=safe_int(test_data.get("Vitamin_B12", 400)),
            Folate=safe_float(test_data.get("Folate", 10.0)),
            Ferritin=safe_int(test_data.get("Ferritin", 100)),
            Uric_Acid=safe_float(test_data.get("Uric_Acid", 5.0)),
            PSA=safe_float(test_data.get("PSA", 1.0)),
            Bone_Density_T_Score=safe_float(test_data.get("Bone_Density_T_Score", 0.0))
        )

        db.session.add(ml_model_data)
        db.session.commit()

        return jsonify({"message": "Data Processed Successfully and Uploaded"}), 200

    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500
