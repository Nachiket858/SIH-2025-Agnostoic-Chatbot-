import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, redirect, session, url_for
from flask_login import LoginManager, current_user
from admin import admin_bp
from student import student_bp
from auth import auth_bp
from db import init_db, get_user_by_id

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "supersecretkey")

    # Initialize DB
    init_db()

    # Login Manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(user_id)

    # Upload folder
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(auth_bp)

    # Index route
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            if current_user.role == 'admin':
                return redirect(url_for('admin.admin'))
            else:
                return redirect(url_for('student.student_chat'))
        return redirect(url_for('auth.login'))

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
