from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from routes.auth import user_login_required
from database.db_connection import query_one, query_all, execute_db
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/dashboard')
@user_login_required
def dashboard():
    user_id = session['user_id']
    
    # 1. Total Calories Burned & Workouts
    workout_stats = query_one("""
        SELECT 
            COUNT(workout_id) as total_workouts,
            COALESCE(SUM(calories_burned), 0) as total_burned,
            COALESCE(AVG(calories_burned), 0) as avg_burned,
            COALESCE(SUM(duration), 0) as total_duration
        FROM workout_history
        WHERE user_id = %s
    """, (user_id,))
    
    # 2. Total Food Calories Consumed
    food_stats = query_one("""
        SELECT 
            COUNT(analysis_id) as total_meals,
            COALESCE(SUM(estimated_calories), 0) as total_consumed,
            COALESCE(AVG(estimated_calories), 0) as avg_consumed,
            COALESCE(SUM(protein), 0) as total_protein,
            COALESCE(SUM(carbohydrates), 0) as total_carbs,
            COALESCE(SUM(fat), 0) as total_fat
        FROM food_analysis_history
        WHERE user_id = %s
    """, (user_id,))

    # 3. Recent 5 workouts
    recent_workouts = query_all("""
        SELECT workout_id, exercise_type, duration, heart_rate, calories_burned, workout_date
        FROM workout_history
        WHERE user_id = %s
        ORDER BY workout_date DESC
        LIMIT 5
    """, (user_id,))

    # 4. Recent 5 food analyses
    recent_foods = query_all("""
        SELECT analysis_id, food_name, quantity, estimated_calories, protein, carbohydrates, fat, analysis_date, image_path
        FROM food_analysis_history
        WHERE user_id = %s
        ORDER BY analysis_date DESC
        LIMIT 5
    """, (user_id,))

    # 5. Last 7 days calories burned trend
    daily_burned_rows = query_all("""
        SELECT DATE(workout_date) as day_date, SUM(calories_burned) as daily_calories
        FROM workout_history
        WHERE user_id = %s AND workout_date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE(workout_date)
        ORDER BY day_date ASC
    """, (user_id,))

    # 6. Last 7 days calories consumed trend
    daily_consumed_rows = query_all("""
        SELECT DATE(analysis_date) as day_date, SUM(estimated_calories) as daily_consumed
        FROM food_analysis_history
        WHERE user_id = %s AND analysis_date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE(analysis_date)
        ORDER BY day_date ASC
    """, (user_id,))

    return render_template(
        'user_dashboard.html',
        user_name=session.get('user_name'),
        workout_stats=workout_stats or {'total_workouts': 0, 'total_burned': 0, 'avg_burned': 0, 'total_duration': 0},
        food_stats=food_stats or {'total_meals': 0, 'total_consumed': 0, 'avg_consumed': 0, 'total_protein': 0, 'total_carbs': 0, 'total_fat': 0},
        recent_workouts=recent_workouts,
        recent_foods=recent_foods,
        daily_burned_rows=daily_burned_rows,
        daily_consumed_rows=daily_consumed_rows
    )

@user_bp.route('/profile', methods=['GET', 'POST'])
@user_login_required
def profile():
    user_id = session['user_id']
    user = query_one("SELECT id, full_name, email, created_at FROM users WHERE id = %s", (user_id,))
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_info':
            full_name = request.form.get('full_name', '').strip()
            if full_name:
                execute_db("UPDATE users SET full_name = %s WHERE id = %s", (full_name, user_id))
                session['user_name'] = full_name
                flash('Profile updated successfully!', 'success')
            else:
                flash('Name cannot be empty.', 'danger')
        elif action == 'change_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new = request.form.get('confirm_new', '')
            
            db_user = query_one("SELECT password_hash FROM users WHERE id = %s", (user_id,))
            if not check_password_hash(db_user['password_hash'], old_password):
                flash('Current password is incorrect.', 'danger')
            elif new_password != confirm_new:
                flash('New passwords do not match.', 'danger')
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters.', 'danger')
            else:
                new_hash = generate_password_hash(new_password)
                execute_db("UPDATE users SET password_hash = %s WHERE id = %s", (new_hash, user_id))
                flash('Password changed successfully!', 'success')
        return redirect(url_for('user.profile'))

    # Profile statistics
    stats = query_one("""
        SELECT 
            (SELECT COUNT(*) FROM workout_history WHERE user_id = %s) as total_workouts,
            (SELECT COALESCE(SUM(calories_burned), 0) FROM workout_history WHERE user_id = %s) as total_calories_burned,
            (SELECT COUNT(*) FROM food_analysis_history WHERE user_id = %s) as total_food_scans
    """, (user_id, user_id, user_id))

    user_fallback = user or {
        'id': user_id,
        'full_name': session.get('user_name', 'Athlete'),
        'email': session.get('user_email', 'user@example.com'),
        'created_at': None
    }
    stats_fallback = stats or {
        'total_workouts': 0,
        'total_calories_burned': 0,
        'total_food_scans': 0
    }

    return render_template('profile.html', user=user_fallback, stats=stats_fallback)

@user_bp.route('/api/chart-data')
@user_login_required
def chart_data():
    """API returning formatted 7-day data for Chart.js"""
    user_id = session['user_id']
    
    today = datetime.date.today()
    date_labels = [(today - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in reversed(range(7))]
    
    burned_map = {d: 0.0 for d in date_labels}
    consumed_map = {d: 0.0 for d in date_labels}

    burned_rows = query_all("""
        SELECT DATE_FORMAT(workout_date, '%%Y-%%m-%%d') as d, SUM(calories_burned) as val
        FROM workout_history
        WHERE user_id = %s AND workout_date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE_FORMAT(workout_date, '%%Y-%%m-%%d')
    """, (user_id,))
    for row in burned_rows:
        if row['d'] in burned_map:
            burned_map[row['d']] = round(float(row['val']), 1)

    consumed_rows = query_all("""
        SELECT DATE_FORMAT(analysis_date, '%%Y-%%m-%%d') as d, SUM(estimated_calories) as val
        FROM food_analysis_history
        WHERE user_id = %s AND analysis_date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
        GROUP BY DATE_FORMAT(analysis_date, '%%Y-%%m-%%d')
    """, (user_id,))
    for row in consumed_rows:
        if row['d'] in consumed_map:
            consumed_map[row['d']] = round(float(row['val']), 1)

    return jsonify({
        'labels': [datetime.datetime.strptime(d, '%Y-%m-%d').strftime('%a (%b %d)') for d in date_labels],
        'calories_burned': [burned_map[d] for d in date_labels],
        'calories_consumed': [consumed_map[d] for d in date_labels]
    })
