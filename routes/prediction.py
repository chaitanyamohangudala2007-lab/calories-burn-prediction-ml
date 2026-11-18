from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from routes.auth import user_login_required
from services.ml_service import ml_service
from database.db_connection import query_one, query_all, execute_db
import datetime

prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.route('/predict', methods=['GET', 'POST'])
def predict_calories():
    # Can be accessed by logged in users, or logged in trainers for clients
    user_id = session.get('user_id')
    trainer_id = session.get('trainer_id')
    role = session.get('role')

    # If neither user nor trainer, redirect to user login
    if not user_id and not trainer_id:
        flash('Please log in to use the Calories Burn Prediction tool.', 'warning')
        return redirect(url_for('auth.user_login'))

    prediction_result = None
    form_data = {}
    clients = []

    if trainer_id:
        # Load trainer's clients for selection dropdown
        clients = query_all("SELECT client_id, client_name, email, age, gender, height, weight FROM trainer_clients WHERE trainer_id = %s", (trainer_id,))

    if request.method == 'POST':
        try:
            exercise_type = request.form.get('exercise_type', 'General Exercise').strip()
            gender = request.form.get('gender', '').strip().lower()
            age = float(request.form.get('age', 0))
            height = float(request.form.get('height', 0))
            weight = float(request.form.get('weight', 0))
            duration = float(request.form.get('duration', 0))
            heart_rate = float(request.form.get('heart_rate', 0))
            body_temp = float(request.form.get('body_temp', 0))
            
            selected_client_id = request.form.get('client_id') if trainer_id else None

            form_data = {
                'exercise_type': exercise_type,
                'gender': gender,
                'age': int(age),
                'height': height,
                'weight': weight,
                'duration': duration,
                'heart_rate': heart_rate,
                'body_temp': body_temp,
                'client_id': selected_client_id
            }

            # Validation
            if not gender or gender not in ['male', 'female']:
                flash('Please select a valid gender.', 'danger')
                return render_template('prediction.html', form_data=form_data, clients=clients)

            if age < 10 or age > 100:
                flash('Please enter a valid age between 10 and 100.', 'danger')
                return render_template('prediction.html', form_data=form_data, clients=clients)

            if height < 50 or height > 250:
                flash('Please enter a valid height in cm (e.g. 140 - 220).', 'danger')
                return render_template('prediction.html', form_data=form_data, clients=clients)

            if weight < 20 or weight > 300:
                flash('Please enter a valid weight in kg (e.g. 30 - 200).', 'danger')
                return render_template('prediction.html', form_data=form_data, clients=clients)

            if duration <= 0 or duration > 300:
                flash('Please enter a duration between 1 and 300 minutes.', 'danger')
                return render_template('prediction.html', form_data=form_data, clients=clients)

            if heart_rate < 40 or heart_rate > 220:
                flash('Please enter a valid heart rate between 40 and 220 bpm.', 'danger')
                return render_template('prediction.html', form_data=form_data, clients=clients)

            if body_temp < 35.0 or body_temp > 43.0:
                flash('Please enter a realistic body temperature in Celsius (e.g. 36.5 - 41.5).', 'danger')
                return render_template('prediction.html', form_data=form_data, clients=clients)

            # Perform prediction using trained XGBoost model
            predicted_cals = ml_service.predict(
                age=age,
                gender=gender,
                height=height,
                weight=weight,
                duration=duration,
                heart_rate=heart_rate,
                body_temp=body_temp
            )

            # Calorie burn intensity classification
            intensity = "Moderate"
            if predicted_cals / duration > 10:
                intensity = "High Intensity"
            elif predicted_cals / duration < 5:
                intensity = "Low Intensity"

            prediction_result = {
                'calories': predicted_cals,
                'intensity': intensity,
                'cal_per_min': round(predicted_cals / duration, 2),
                'exercise_type': exercise_type,
                'duration': duration,
                'heart_rate': heart_rate
            }

            # Save in MySQL workout_history
            target_user_id = user_id if role == 'user' else None
            target_client_id = selected_client_id if (role == 'trainer' and selected_client_id) else None

            saved = execute_db("""
                INSERT INTO workout_history (
                    user_id, client_id, exercise_type, duration, heart_rate, body_temperature,
                    age, gender, height, weight, calories_burned, workout_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (
                target_user_id, target_client_id, exercise_type, duration, heart_rate,
                body_temp, int(age), gender, height, weight, predicted_cals
            ))

            if saved:
                flash('Workout predicted and saved to your history successfully!', 'success')
            else:
                flash('Prediction calculated, but saving to database failed. Check DB connection.', 'warning')

        except Exception as e:
            flash(f'Error calculating prediction: {str(e)}', 'danger')

    return render_template('prediction.html', prediction_result=prediction_result, form_data=form_data, clients=clients)

@prediction_bp.route('/workouts')
@user_login_required
def workout_history():
    user_id = session['user_id']
    time_filter = request.args.get('filter', 'all')
    exercise_filter = request.args.get('exercise', 'all')

    sql = "SELECT * FROM workout_history WHERE user_id = %s"
    params = [user_id]

    # Time filter
    if time_filter == 'daily':
        sql += " AND DATE(workout_date) = CURDATE()"
    elif time_filter == 'weekly':
        sql += " AND workout_date >= DATE_SUB(NOW(), INTERVAL 7 DAY)"
    elif time_filter == 'monthly':
        sql += " AND workout_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)"

    # Exercise filter
    if exercise_filter != 'all':
        sql += " AND exercise_type = %s"
        params.append(exercise_filter)

    sql += " ORDER BY workout_date DESC"
    workouts = query_all(sql, tuple(params))

    # Available exercise types for filter dropdown
    exercise_types = query_all("SELECT DISTINCT exercise_type FROM workout_history WHERE user_id = %s", (user_id,))

    # Summary statistics for this filter view
    total_workouts = len(workouts)
    total_calories = sum(w['calories_burned'] for w in workouts)
    total_duration = sum(w['duration'] for w in workouts)
    avg_hr = round(sum(w['heart_rate'] for w in workouts) / total_workouts, 1) if total_workouts > 0 else 0

    return render_template(
        'workout_history.html',
        workouts=workouts,
        time_filter=time_filter,
        exercise_filter=exercise_filter,
        exercise_types=[e['exercise_type'] for e in exercise_types if e['exercise_type']],
        total_workouts=total_workouts,
        total_calories=round(total_calories, 1),
        total_duration=round(total_duration, 1),
        avg_hr=avg_hr
    )
