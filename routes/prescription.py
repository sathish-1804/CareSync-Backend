from flask import Blueprint, request, jsonify
from models import db, Prescription
from utils import upload_file_and_get_url
from datetime import datetime

prescription_bp = Blueprint('prescription', __name__)

@prescription_bp.route('/upload_prescription', methods=['POST'])
def upload_prescription():
    try:
        user_id = request.form['user_id']
        clinic_name = request.form['clinic_name']
        description = request.form['description']
        date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        file = request.files['file']
        file_link = upload_file_and_get_url(file)

        new_prescription = Prescription(
            user_id=user_id,
            clinic_name=clinic_name,
            description=description,
            filename=file.filename,
            date=date,
            file_link=file_link
        )
        db.session.add(new_prescription)
        db.session.commit()

        response = {"message": "Prescription uploaded successfully", "file_link": file_link}
        return jsonify(response), 201
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@prescription_bp.route('/get_prescriptions/<user_id>', methods=['GET'])
def get_prescriptions(user_id):
    prescriptions = Prescription.query.filter_by(user_id=user_id).all()
    output = []
    for prescription in prescriptions:
        output.append({
            'prescription_id': prescription.prescription_id,
            'user_id': prescription.user_id,
            'clinic_name': prescription.clinic_name,
            'filename': prescription.filename,
            'description': prescription.description,
            'date': prescription.date.isoformat(),
            'file_link': prescription.file_link
        })
    return jsonify(output)
