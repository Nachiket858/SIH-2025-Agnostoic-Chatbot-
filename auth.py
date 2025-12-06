from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_user_by_email, create_user, User

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_data = get_user_by_email(email)
        
        if user_data and check_password_hash(user_data['password'], password):
            user = User(user_data['id'], user_data['email'], user_data['role'])
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin.admin'))
            else:
                return redirect(url_for('student.student_chat'))
        else:
            flash('Please check your login details and try again.')
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = 'student' # Default role for all new registrations
        
        user_data = get_user_by_email(email)
        
        if user_data:
            flash('Email address already exists')
            return redirect(url_for('auth.register'))
        
        new_password_hash = generate_password_hash(password, method='scrypt')
        
        if create_user(email, new_password_hash, role):
            flash('Account created! Please log in.')
            return redirect(url_for('auth.login'))
        else:
            flash('Error creating account.')
            
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
