import mysql.connector
from mysql.connector import Error, pooling
import logging
import os
from config import Config

logger = logging.getLogger(__name__)

def get_db_connection():
    """Establish and return a MySQL connection."""
    try:
        connection = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci',
            autocommit=False
        )
        return connection
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def test_db_connection():
    """Test if database is reachable."""
    conn = get_db_connection()
    if conn and conn.is_connected():
        conn.close()
        return True, "Database connected successfully"
    return False, "Could not connect to MySQL. Please check DB credentials in .env file."

def query_one(sql, params=None):
    """Execute a SELECT query and return a single row as a dictionary."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result
    except Error as e:
        logger.error(f"Error executing query_one: {e}")
        if conn:
            conn.close()
        return None

def query_all(sql, params=None):
    """Execute a SELECT query and return all rows as a list of dictionaries."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params or ())
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results
    except Error as e:
        logger.error(f"Error executing query_all: {e}")
        if conn:
            conn.close()
        return []

def execute_db(sql, params=None, return_lastrowid=False):
    """Execute an INSERT, UPDATE, or DELETE query and commit."""
    conn = get_db_connection()
    if not conn:
        return False if not return_lastrowid else None
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params or ())
        conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        conn.close()
        if return_lastrowid:
            return last_id
        return True
    except Error as e:
        logger.error(f"Error executing execute_db: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return None if return_lastrowid else False

def init_db():
    """Initialize database tables if they do not exist."""
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.exists(schema_path):
        return False, "schema.sql not found"
        
    try:
        # First ensure database exists
        admin_conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        admin_cursor = admin_conn.cursor()
        admin_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        admin_cursor.close()
        admin_conn.close()

        # Execute schema statements
        conn = get_db_connection()
        if not conn:
            return False, "Failed to connect to database"
            
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        cursor = conn.cursor()
        statements = sql_script.split(';')
        for statement in statements:
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
        conn.commit()
        cursor.close()
        conn.close()
        return True, "Database initialized successfully"
    except Error as e:
        logger.error(f"Database initialization error: {e}")
        return False, str(e)
