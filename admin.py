import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from backend import allowed_file, upload_to_qdrant

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        file = request.files.get("file")
        if not file:
            return jsonify({"status": "error", "message": "No file uploaded"})

        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            chunks_count = upload_to_qdrant(filepath)
            if chunks_count == 0:
                return jsonify({"status": "error", "message": "No text extracted from the file."})

            return jsonify({"status": "success", "message": f"File uploaded successfully with {chunks_count} chunks."})
        else:
            return jsonify({"status": "error", "message": "Invalid file type. Only pdf, docx, txt allowed."})

    return render_template("admin.html")


if __name__ == "__main__":
    app.run(debug=True)
