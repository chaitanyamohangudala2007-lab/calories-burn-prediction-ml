import os
from flask import Flask, render_template, send_from_directory, session
from config import Config
from routes.auth import auth_bp
from routes.user import user_bp
from routes.trainer import trainer_bp
from routes.prediction import prediction_bp
from routes.food_analysis import food_bp
from database.db_connection import test_db_connection

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(trainer_bp)
app.register_blueprint(prediction_bp)
app.register_blueprint(food_bp)

# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

# Context processor for navigation & session variables
@app.context_processor
def inject_user_context():
    return {
        'logged_in_user_id': session.get('user_id'),
        'logged_in_trainer_id': session.get('trainer_id'),
        'current_user_name': session.get('user_name'),
        'current_trainer_name': session.get('trainer_name'),
        'user_role': session.get('role')
    }

# Public Pages
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/features')
def features():
    return render_template('features.html')

# Health / DB & AI Status API
@app.route('/api/status')
def api_status():
    db_ok, msg = test_db_connection()
    return {
        'status': 'online',
        'database_connected': db_ok,
        'database_message': msg,
        'model_loaded': os.path.exists(Config.MODEL_PATH),
        'ai_provider': 'Experiential Labs',
        'explabs_configured': bool(Config.EXPLABS_API_KEY),
        'explabs_model': Config.EXPLABS_MODEL,
        'explabs_base_url': Config.EXPLABS_API_BASE_URL
    }

# Error Handlers
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == '__main__':
    print("Starting AI Calories & Nutrition Web Application...")
    db_ok, msg = test_db_connection()
    if db_ok:
        print("[SUCCESS] Connected to MySQL database.")
    else:
        print(f"[NOTICE] Database connection note: {msg}")
    app.run(debug=True, host='127.0.0.1', port=5000)
