from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from database.db_connection import query_one, execute_db

auth_bp = Blueprint('auth', __name__)

def user_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'user':
            flash('Please log in as a user to access this page.', 'warning')
            return redirect(url_for('auth.user_login'))
        return f(*args, **kwargs)
    return decorated_function

def trainer_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'trainer_id' not in session or session.get('role') != 'trainer':
            flash('Please log in as a gym trainer to access this page.', 'warning')
            return redirect(url_for('auth.trainer_login'))
        return f(*args, **kwargs)
    return decorated_function

# ================= USER AUTH =================

@auth_bp.route('/register', methods=['GET', 'POST'])
def user_register():
    if 'user_id' in session and session.get('role') == 'user':
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not full_name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html', full_name=full_name, email=email)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html', full_name=full_name, email=email)

        # Check existing user
        existing = query_one("SELECT id FROM users WHERE email = %s", (email,))
        if existing:
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('auth.user_login'))

        password_hash = generate_password_hash(password)
        success = execute_db(
            "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
            (full_name, email, password_hash)
        )

        if success:
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.user_login'))
        else:
            flash('Failed to register. Please ensure database connection is active.', 'danger')

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def user_login():
    if 'user_id' in session and session.get('role') == 'user':
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('login.html', email=email)

        user = query_one("SELECT * FROM users WHERE email = %s", (email,))
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            session['role'] = 'user'
            flash(f"Welcome back, {user['full_name']}!", 'success')
            return redirect(url_for('user.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

# ================= TRAINER AUTH =================

@auth_bp.route('/trainer/register', methods=['GET', 'POST'])
def trainer_register():
    if 'trainer_id' in session and session.get('role') == 'trainer':
        return redirect(url_for('trainer.dashboard'))

    if request.method == 'POST':
        trainer_name = request.form.get('trainer_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not trainer_name or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('trainer_register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('trainer_register.html', trainer_name=trainer_name, email=email)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('trainer_register.html', trainer_name=trainer_name, email=email)

        existing = query_one("SELECT trainer_id FROM trainers WHERE email = %s", (email,))
        if existing:
            flash('Trainer email already registered. Please log in.', 'warning')
            return redirect(url_for('auth.trainer_login'))

        password_hash = generate_password_hash(password)
        success = execute_db(
            "INSERT INTO trainers (trainer_name, email, password_hash) VALUES (%s, %s, %s)",
            (trainer_name, email, password_hash)
        )

        if success:
            flash('Trainer registered successfully! You can now log in.', 'success')
            return redirect(url_for('auth.trainer_login'))
        else:
            flash('Failed to register trainer. Please check database connection.', 'danger')

    return render_template('trainer_register.html')

@auth_bp.route('/trainer/login', methods=['GET', 'POST'])
def trainer_login():
    if 'trainer_id' in session and session.get('role') == 'trainer':
        return redirect(url_for('trainer.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'danger')
            return render_template('trainer_login.html', email=email)

        trainer = query_one("SELECT * FROM trainers WHERE email = %s", (email,))
        if trainer and check_password_hash(trainer['password_hash'], password):
            session.clear()
            session['trainer_id'] = trainer['trainer_id']
            session['trainer_name'] = trainer['trainer_name']
            session['trainer_email'] = trainer['email']
            session['role'] = 'trainer'
            flash(f"Welcome back, Coach {trainer['trainer_name']}!", 'success')
            return redirect(url_for('trainer.dashboard'))
        else:
            flash('Invalid trainer email or password.', 'danger')

    return render_template('trainer_login.html')

# ================= LOGOUT =================

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('home'))
