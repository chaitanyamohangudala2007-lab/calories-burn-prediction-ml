from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, jsonify
from routes.auth import trainer_login_required
from database.db_connection import query_one, query_all, execute_db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

trainer_bp = Blueprint('trainer', __name__, url_prefix='/trainer')

@trainer_bp.route('/dashboard')
@trainer_login_required
def dashboard():
    trainer_id = session['trainer_id']

    # Overview Cards
    total_clients_row = query_one(
        "SELECT COUNT(*) as count FROM trainer_clients WHERE trainer_id = %s",
        (trainer_id,)
    )
    total_clients = total_clients_row['count'] if total_clients_row else 0

    client_workout_stats = query_one("""
        SELECT 
            COUNT(w.workout_id) as total_workouts,
            COALESCE(SUM(w.calories_burned), 0) as total_calories_burned,
            COALESCE(AVG(w.calories_burned), 0) as avg_calories_burned,
            COALESCE(SUM(w.duration), 0) as total_duration
        FROM workout_history w
        JOIN trainer_clients c ON w.client_id = c.client_id
        WHERE c.trainer_id = %s
    """, (trainer_id,))

    # Clients list
    clients = query_all("""
        SELECT 
            c.*,
            (SELECT COUNT(*) FROM workout_history WHERE client_id = c.client_id) as workout_count,
            (SELECT COALESCE(SUM(calories_burned), 0) FROM workout_history WHERE client_id = c.client_id) as total_calories
        FROM trainer_clients c
        WHERE c.trainer_id = %s
        ORDER BY c.created_at DESC
    """, (trainer_id,))

    # Recent client workouts
    recent_workouts = query_all("""
        SELECT 
            w.workout_id, w.exercise_type, w.duration, w.heart_rate, w.calories_burned, w.workout_date,
            c.client_name, c.client_id
        FROM workout_history w
        JOIN trainer_clients c ON w.client_id = c.client_id
        WHERE c.trainer_id = %s
        ORDER BY w.workout_date DESC
        LIMIT 6
    """, (trainer_id,))

    return render_template(
        'trainer_dashboard.html',
        trainer_name=session.get('trainer_name'),
        total_clients=total_clients,
        stats=client_workout_stats or {'total_workouts': 0, 'total_calories_burned': 0, 'avg_calories_burned': 0, 'total_duration': 0},
        clients=clients,
        recent_workouts=recent_workouts
    )

@trainer_bp.route('/clients')
@trainer_login_required
def manage_clients():
    trainer_id = session['trainer_id']
    clients = query_all("""
        SELECT 
            c.*,
            (SELECT COUNT(*) FROM workout_history WHERE client_id = c.client_id) as workout_count,
            (SELECT COALESCE(SUM(calories_burned), 0) FROM workout_history WHERE client_id = c.client_id) as total_calories,
            (SELECT COALESCE(SUM(estimated_calories), 0) FROM food_analysis_history WHERE client_id = c.client_id) as total_consumed
        FROM trainer_clients c
        WHERE c.trainer_id = %s
        ORDER BY c.client_name ASC
    """, (trainer_id,))
    
    # Calculate BMI for each client
    for client in clients:
        h_m = (client['height'] or 170) / 100.0
        w_kg = client['weight'] or 70
        client['bmi'] = round(w_kg / (h_m * h_m), 1) if h_m > 0 else 0

    return render_template('trainer_clients.html', clients=clients)

@trainer_bp.route('/add-client', methods=['GET', 'POST'])
@trainer_login_required
def add_client():
    trainer_id = session['trainer_id']

    if request.method == 'POST':
        client_name = request.form.get('client_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        age = request.form.get('age', 0)
        gender = request.form.get('gender', '').strip().lower()
        height = request.form.get('height', 0)
        weight = request.form.get('weight', 0)

        # Validation
        if not client_name or not email or not gender:
            flash('Please fill in all required client details.', 'danger')
            return render_template('add_client.html', form=request.form)

        try:
            age = int(age)
            height = float(height)
            weight = float(weight)
        except ValueError:
            flash('Please enter valid numeric values for age, height, and weight.', 'danger')
            return render_template('add_client.html', form=request.form)

        if age < 5 or age > 110 or height < 50 or height > 260 or weight < 20 or weight > 300:
            flash('Please enter realistic measurements for client.', 'danger')
            return render_template('add_client.html', form=request.form)

        success = execute_db("""
            INSERT INTO trainer_clients (trainer_id, client_name, email, age, gender, height, weight, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, (trainer_id, client_name, email, age, gender, height, weight))

        if success:
            flash(f'Client {client_name} added successfully!', 'success')
            return redirect(url_for('trainer.manage_clients'))
        else:
            flash('Failed to add client. Please check database connection.', 'danger')

    return render_template('add_client.html')

@trainer_bp.route('/client/<int:client_id>')
@trainer_login_required
def client_details(client_id):
    trainer_id = session['trainer_id']

    # Security check: client must belong to logged-in trainer
    client = query_one(
        "SELECT * FROM trainer_clients WHERE client_id = %s AND trainer_id = %s",
        (client_id, trainer_id)
    )
    if not client:
        flash('Client not found or you are not authorized to view this client.', 'danger')
        return redirect(url_for('trainer.manage_clients'))

    # Calculate BMI
    h_m = (client['height'] or 170) / 100.0
    client['bmi'] = round(client['weight'] / (h_m * h_m), 1) if h_m > 0 else 0

    # Client workout statistics
    stats = query_one("""
        SELECT 
            COUNT(workout_id) as total_workouts,
            COALESCE(SUM(calories_burned), 0) as total_burned,
            COALESCE(AVG(calories_burned), 0) as avg_burned,
            COALESCE(SUM(duration), 0) as total_duration,
            COALESCE(AVG(heart_rate), 0) as avg_heart_rate
        FROM workout_history
        WHERE client_id = %s
    """, (client_id,))

    # Client food statistics
    food_stats = query_one("""
        SELECT 
            COUNT(analysis_id) as total_meals,
            COALESCE(SUM(estimated_calories), 0) as total_consumed,
            COALESCE(SUM(protein), 0) as total_protein,
            COALESCE(SUM(carbohydrates), 0) as total_carbs,
            COALESCE(SUM(fat), 0) as total_fat
        FROM food_analysis_history
        WHERE client_id = %s
    """, (client_id,))

    # Workouts list
    workouts = query_all("""
        SELECT * FROM workout_history
        WHERE client_id = %s
        ORDER BY workout_date DESC
        LIMIT 10
    """, (client_id,))

    # Food analysis list
    foods = query_all("""
        SELECT * FROM food_analysis_history
        WHERE client_id = %s
        ORDER BY analysis_date DESC
        LIMIT 10
    """, (client_id,))

    # Daily, weekly, monthly stats
    daily_burned = query_one("SELECT COALESCE(SUM(calories_burned), 0) as val FROM workout_history WHERE client_id = %s AND DATE(workout_date) = CURDATE()", (client_id,))
    weekly_burned = query_one("SELECT COALESCE(SUM(calories_burned), 0) as val FROM workout_history WHERE client_id = %s AND workout_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)", (client_id,))
    monthly_burned = query_one("SELECT COALESCE(SUM(calories_burned), 0) as val FROM workout_history WHERE client_id = %s AND workout_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)", (client_id,))

    return render_template(
        'client_details.html',
        client=client,
        stats=stats or {'total_workouts': 0, 'total_burned': 0, 'avg_burned': 0, 'total_duration': 0, 'avg_heart_rate': 0},
        food_stats=food_stats or {'total_meals': 0, 'total_consumed': 0, 'total_protein': 0, 'total_carbs': 0, 'total_fat': 0},
        workouts=workouts,
        foods=foods,
        daily_burned=round(daily_burned['val'] if daily_burned else 0, 1),
        weekly_burned=round(weekly_burned['val'] if weekly_burned else 0, 1),
        monthly_burned=round(monthly_burned['val'] if monthly_burned else 0, 1)
    )

@trainer_bp.route('/client/<int:client_id>/workouts')
@trainer_login_required
def client_workout_history(client_id):
    trainer_id = session['trainer_id']
    client = query_one("SELECT * FROM trainer_clients WHERE client_id = %s AND trainer_id = %s", (client_id, trainer_id))
    if not client:
        flash('Unauthorized client access.', 'danger')
        return redirect(url_for('trainer.manage_clients'))

    workouts = query_all("SELECT * FROM workout_history WHERE client_id = %s ORDER BY workout_date DESC", (client_id,))
    return render_template('client_workout_history.html', client=client, workouts=workouts)

@trainer_bp.route('/client/<int:client_id>/nutrition')
@trainer_login_required
def client_nutrition_history(client_id):
    trainer_id = session['trainer_id']
    client = query_one("SELECT * FROM trainer_clients WHERE client_id = %s AND trainer_id = %s", (client_id, trainer_id))
    if not client:
        flash('Unauthorized client access.', 'danger')
        return redirect(url_for('trainer.manage_clients'))

    foods = query_all("SELECT * FROM food_analysis_history WHERE client_id = %s ORDER BY analysis_date DESC", (client_id,))
    return render_template('client_nutrition_history.html', client=client, foods=foods)

@trainer_bp.route('/client/<int:client_id>/api/chart-data')
@trainer_login_required
def client_chart_data(client_id):
    trainer_id = session['trainer_id']
    client = query_one("SELECT client_id FROM trainer_clients WHERE client_id = %s AND trainer_id = %s", (client_id, trainer_id))
    if not client:
        return jsonify({'error': 'Unauthorized'}), 403

    today = datetime.date.today()
    date_labels = [(today - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in reversed(range(7))]
    
    burned_map = {d: 0.0 for d in date_labels}
    consumed_map = {d: 0.0 for d in date_labels}
    duration_map = {d: 0.0 for d in date_labels}

    burned_rows = query_all("""
        SELECT DATE_FORMAT(workout_date, '%%Y-%%m-%%d') as d, SUM(calories_burned) as val, SUM(duration) as dur
        FROM workout_history
        WHERE client_id = %s AND workout_date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE_FORMAT(workout_date, '%%Y-%%m-%%d')
    """, (client_id,))
    for row in burned_rows:
        if row['d'] in burned_map:
            burned_map[row['d']] = round(float(row['val']), 1)
            duration_map[row['d']] = round(float(row['dur']), 1)

    consumed_rows = query_all("""
        SELECT DATE_FORMAT(analysis_date, '%%Y-%%m-%%d') as d, SUM(estimated_calories) as val
        FROM food_analysis_history
        WHERE client_id = %s AND analysis_date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE_FORMAT(analysis_date, '%%Y-%%m-%%d')
    """, (client_id,))
    for row in consumed_rows:
        if row['d'] in consumed_map:
            consumed_map[row['d']] = round(float(row['val']), 1)

    return jsonify({
        'labels': [datetime.datetime.strptime(d, '%Y-%m-%d').strftime('%a (%b %d)') for d in date_labels],
        'calories_burned': [burned_map[d] for d in date_labels],
        'calories_consumed': [consumed_map[d] for d in date_labels],
        'duration': [duration_map[d] for d in date_labels]
    })

@trainer_bp.route('/profile', methods=['GET', 'POST'])
@trainer_login_required
def profile():
    trainer_id = session['trainer_id']
    trainer = query_one("SELECT trainer_id, trainer_name, email, created_at FROM trainers WHERE trainer_id = %s", (trainer_id,))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_info':
            trainer_name = request.form.get('trainer_name', '').strip()
            if trainer_name:
                execute_db("UPDATE trainers SET trainer_name = %s WHERE trainer_id = %s", (trainer_name, trainer_id))
                session['trainer_name'] = trainer_name
                flash('Trainer profile updated successfully!', 'success')
        elif action == 'change_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new = request.form.get('confirm_new', '')

            db_trainer = query_one("SELECT password_hash FROM trainers WHERE trainer_id = %s", (trainer_id,))
            if not check_password_hash(db_trainer['password_hash'], old_password):
                flash('Current password is incorrect.', 'danger')
            elif new_password != confirm_new:
                flash('New passwords do not match.', 'danger')
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters.', 'danger')
            else:
                new_hash = generate_password_hash(new_password)
                execute_db("UPDATE trainers SET password_hash = %s WHERE trainer_id = %s", (new_hash, trainer_id))
                flash('Password changed successfully!', 'success')
        return redirect(url_for('trainer.profile'))

    stats = query_one("""
        SELECT 
            (SELECT COUNT(*) FROM trainer_clients WHERE trainer_id = %s) as total_clients,
            (SELECT COUNT(*) FROM workout_history w JOIN trainer_clients c ON w.client_id = c.client_id WHERE c.trainer_id = %s) as total_client_workouts
    """, (trainer_id, trainer_id))

    trainer_fallback = trainer or {
        'trainer_id': trainer_id,
        'trainer_name': session.get('trainer_name', 'Coach'),
        'email': session.get('trainer_email', 'coach@gym.com'),
        'created_at': None
    }
    stats_fallback = stats or {
        'total_clients': 0,
        'total_client_workouts': 0
    }

    return render_template('trainer_profile.html', trainer=trainer_fallback, stats=stats_fallback)
