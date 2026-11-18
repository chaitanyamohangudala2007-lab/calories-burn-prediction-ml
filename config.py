import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fitness-secret-key-2026-secure')
    
    # MySQL Database Config
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'calories_db')
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Experiential Labs API Config
    EXPLABS_API_BASE_URL = os.environ.get('EXPLABS_API_BASE_URL', 'https://api.experientiallabs.ai/v1')
    EXPLABS_API_KEY = os.environ.get('EXPLABS_API_KEY', os.environ.get('OPENAI_API_KEY', ''))
    EXPLABS_MODEL = os.environ.get('EXPLABS_MODEL', os.environ.get('OPENAI_MODEL', 'gpt-4o-mini'))

    # ML Model
    MODEL_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'models', 'calories_model.pkl')
