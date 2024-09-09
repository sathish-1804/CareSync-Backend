from flask import Blueprint, request, jsonify
from PIL import Image
from models import db, User, ClaimStatus
from sqlalchemy import text, func
import logging
import os
import base64
from io import BytesIO
import dotenv
import re
import google.generativeai as genai  # Import Google Gemini API

# Load environment variables
dotenv.load_dotenv()

# Initialize blueprint
claim_bp = Blueprint('claim', __name__)

# Configure Generative AI API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash-latest')

@claim_bp.route('/process_claim', methods=['POST'])
def process_claim_api():
    try:
        bill_file = request.files.get('bill_file')
        reason_for_treatment = request.form.get('reason_for_treatment')
        user_id = request.form.get('user_id')

        if not bill_file or not reason_for_treatment or not user_id:
            return jsonify({"error": "Missing required inputs"}), 400

        bill_name = bill_file.filename
        file_extension = bill_name.lower().split('.')[-1]

        # Determine the file type and convert to base64
        if file_extension in ['jpg', 'jpeg', 'png']:
            # Process image files
            bill_image = Image.open(bill_file)
            buffered = BytesIO()
            bill_image.save(buffered, format="JPEG")
            bill_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            mime_type = "image/jpeg"
        elif file_extension == 'pdf':
            # Process PDF files
            bill_base64 = base64.b64encode(bill_file.read()).decode('utf-8')
            mime_type = "application/pdf"
        else:
            return jsonify({"error": "Unsupported file format. Please upload a JPEG, PNG, or PDF file."}), 400

        # Call the process_claim function
        result = process_claim(bill_base64, mime_type, reason_for_treatment, user_id)

        # Insert the decision, reason, and bill name into the ClaimStatus table
        if 'decision' in result and 'reason' in result:
            new_claim_status = ClaimStatus(
                user_id=user_id,
                decision=result['decision'],
                reason=result['reason'],
                bill_name=bill_name
            )
            db.session.add(new_claim_status)
            db.session.commit()

        return jsonify({"message": "Claim processed successfully"}), 200

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "An internal error occurred"}), 500


def process_claim(bill_base64, mime_type, reason_for_treatment, user_id):
    """Processes the insurance claim by extracting text from the bill and verifying the treatment."""
    try:
        # Extract text from the bill using Gemini API
        prompt = """
        Extract the exact text content from the hospital bill. Do not alter or interpret the content.
        Provide the extracted text as is.
        """
        genai_response = model.generate_content([prompt, {"mime_type": mime_type, "data": bill_base64}])

        if not genai_response or not genai_response.text:
            logging.error("No response from Gemini API or response is empty.")
            return {"error": "No response from Gemini API or response is empty."}

        bill_text = genai_response.text.strip()
        logging.info(f"Extracted bill text: {bill_text}")

    except Exception as e:
        logging.error(f"Error processing hospital bill: {str(e)}")
        return {"error": f"Error processing hospital bill: {str(e)}"}

    try:
        # Execute the constant SQL query with the provided user_id
        CONSTANT_SQL_QUERY = text("""
        SELECT
            ip.plan_id,
            ip.company,
            ip.plan_name,
            ip.plan_type,
            ip.network_type,
            ip.sum_insured,
            ip.deductible,
            ip.out_of_pocket_max,
            ip.policy_number,
            ip.effective_date,
            ip.expiration_date,
            (SELECT GROUP_CONCAT(DISTINCT cd.coverage_item SEPARATOR ', ')
             FROM coveragedetails cd
             WHERE cd.plan_id = ip.plan_id) AS coverage_items,
            (SELECT GROUP_CONCAT(DISTINCT CONCAT(cp.service, ': ', cp.amount) SEPARATOR ', ')
             FROM copayments cp
             WHERE cp.plan_id = ip.plan_id) AS copayments,
            (SELECT GROUP_CONCAT(DISTINCT ab.benefit_description SEPARATOR ', ')
             FROM additionalbenefits ab
             WHERE ab.plan_id = ip.plan_id) AS additional_benefits,
            (SELECT GROUP_CONCAT(DISTINCT pe.general_exclusions SEPARATOR ', ')
             FROM policyexclusions pe
             WHERE pe.plan_id = ip.plan_id) AS general_exclusions,
            (SELECT GROUP_CONCAT(DISTINCT pe.waiting_periods SEPARATOR ', ')
             FROM policyexclusions pe
             WHERE pe.plan_id = ip.plan_id) AS waiting_periods,
            (SELECT p.description
             FROM prescriptions p
             WHERE p.user_id = ip.user_id
             ORDER BY p.date DESC
             LIMIT 1) AS latest_prescription,
            hi.medical_history,
            hi.current_medications
        FROM
            insuranceplans ip
        LEFT JOIN healthinformation hi ON ip.user_id = hi.user_id
        WHERE
            ip.user_id = :user_id;
        """)
        
        medical_details = db.session.execute(CONSTANT_SQL_QUERY, {'user_id': user_id}).fetchall()
        logging.info(f"Fetched medical details: {medical_details}")

    except Exception as e:
        logging.error(f"Error fetching data from the database: {str(e)}")
        return {"error": f"Error fetching data from the database: {str(e)}"}

    # Use Gemini API to verify the treatment and generate a decision
    decision, reason = verify_treatment(reason_for_treatment, medical_details, bill_text, CONSTANT_SQL_QUERY)
    return {"decision": decision, "reason": reason}


def verify_treatment(reason, medical_details, bill_text, query):
    """Verifies if the treatment in the bill is covered based on the provided details."""
    prompt = f"""
    Please evaluate the following case:

    - Hospital bill text: '{bill_text}'
    - Reason for treatment: '{reason}'
    - User's medical details: '{medical_details}'
    - Query used to retrieve details from the database: '{query}'

    Based on the provided information and policy details:
    1. Does the treatment mentioned in the hospital bill fall under the user's insurance coverage?
    2. Is the reason for treatment consistent with the user's medical history and current condition?

    Your task:
    - If everything aligns and the treatment is covered, respond with 'Answer: Claim Approved' followed by a brief 2-3 line reason.
    - If the treatment is not covered under the policy, respond with 'Answer: Claim Cancelled' followed by a brief 2-3 line reason.
    - If you're unsure and a manual review is needed, respond with 'Answer: Claim in review' followed by a brief 2-3 line reason.

    Ensure you to replace user with you. Should be like conveying this message to user. and the reason should be less than 100 characters.
    Return format: 'Answer: Claim Approved/Claim Cancelled/Claim in review. Reason: <reason>'
    """
    
    response = model.generate_content(prompt)
    response_text = response.text.strip()
    logging.info(f"Response from Gemini: {response_text}")
    
    match = re.search(r'Answer:\s*(Claim Approved|Claim Cancelled|Claim in review)', response_text, re.IGNORECASE)
    reason_match = re.search(r'(?:Reason:)\s*(.*)', response_text, re.IGNORECASE)
    if match:
        decision = match.group(1).strip()
        reason = reason_match.group(1).strip() if reason_match else "No reason provided."
        return decision, reason
    else:
        logging.error("Unable to determine the claim status from the Gemini response.")
        return "Error: Unable to determine the claim status from the Gemini response."


@claim_bp.route('/retrieve_claims/<int:user_id>', methods=['GET'])
def retrieve_claims(user_id):
    try:
        # Fetch claim statuses for the given user_id with required details
        claims = ClaimStatus.query.filter_by(user_id=user_id).with_entities(
            ClaimStatus.bill_name,
            ClaimStatus.decision,
            ClaimStatus.reason,
            func.date(ClaimStatus.processed_at).label('date')
        ).all()

        # Format the result as a list of dictionaries
        claims_list = [
            {
                'bill_name': claim.bill_name,
                'status': claim.decision,
                'reason': claim.reason,
                'date': claim.date.strftime('%Y-%m-%d')  # Format date as 'YYYY-MM-DD'
            }
            for claim in claims
        ]

        return jsonify(claims_list), 200

    except Exception as e:
        logging.error(f"Error retrieving claims: {str(e)}")
        return jsonify({"error": "Failed to retrieve claims"}), 500
