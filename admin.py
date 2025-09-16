# admin.py
import os
from flask import Blueprint, request, jsonify, render_template, current_app
from werkzeug.utils import secure_filename
from utilities import allowed_file, upload_to_qdrant

admin_bp = Blueprint("admin", __name__, template_folder="templates")

# Route: GET -> render upload page, POST -> accept file and upload to qdrant
@admin_bp.route("/admin", methods=["GET", "POST"])
def admin():
    # Use current_app config for upload folder
    upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)

    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return jsonify({"status": "error", "message": "No file uploaded"})

        if not allowed_file(file.filename):
            return jsonify({"status": "error", "message": "Invalid file type. Only pdf, docx, txt allowed."})

        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        try:
            chunks_count = upload_to_qdrant(filepath)
        except Exception as e:
            # Catch unexpected errors but return safe message
            return jsonify({"status": "error", "message": f"Upload failed: {str(e)}"})

        if chunks_count == 0:
            return jsonify({"status": "error", "message": "No text extracted from the file."})

        return jsonify({"status": "success", "message": f"File uploaded successfully with {chunks_count} chunks."})

    return render_template("admin.html")
