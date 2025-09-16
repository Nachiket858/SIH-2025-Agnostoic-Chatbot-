# app.py
import os
from flask import Flask, render_template, request, redirect, session
from admin import admin_bp
from student import student_bp
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")  # move to .env for production

    # Upload folder
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register blueprints (they define routes like /admin, /student_chat, /reset_chat, /switch_thread/...)
    app.register_blueprint(admin_bp)     # admin route: /admin
    app.register_blueprint(student_bp)   # student routes: /student_chat, /switch_thread/<id>, /reset_chat

    # Index route (role selection)
    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            role = request.form.get("role")
            session["role"] = role
            # initialize thread for students
            if role == "student":
                # student blueprint will handle session initialization
                return redirect("/student_chat")
            else:
                return redirect("/admin")
        return render_template("index.html")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
