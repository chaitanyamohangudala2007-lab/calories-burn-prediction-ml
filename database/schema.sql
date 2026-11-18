-- Database Schema for AI-Based Calories Burn Prediction and Food Nutrition Analysis System
-- Database name: calories_db

CREATE DATABASE IF NOT EXISTS calories_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE calories_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Gym Trainers Table
CREATE TABLE IF NOT EXISTS trainers (
    trainer_id INT AUTO_INCREMENT PRIMARY KEY,
    trainer_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. Trainer Clients Table
CREATE TABLE IF NOT EXISTS trainer_clients (
    client_id INT AUTO_INCREMENT PRIMARY KEY,
    trainer_id INT NOT NULL,
    client_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(20) NOT NULL,
    height FLOAT NOT NULL,
    weight FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trainer_id) REFERENCES trainers(trainer_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 4. Workout History Table
CREATE TABLE IF NOT EXISTS workout_history (
    workout_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    client_id INT NULL,
    exercise_type VARCHAR(100) NOT NULL,
    duration FLOAT NOT NULL,
    heart_rate FLOAT NOT NULL,
    body_temperature FLOAT NOT NULL,
    age INT NOT NULL,
    gender VARCHAR(20) NOT NULL,
    height FLOAT NOT NULL,
    weight FLOAT NOT NULL,
    calories_burned FLOAT NOT NULL,
    workout_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES trainer_clients(client_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- 5. Food Analysis History Table
CREATE TABLE IF NOT EXISTS food_analysis_history (
    analysis_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    client_id INT NULL,
    food_name VARCHAR(255) NOT NULL,
    quantity VARCHAR(100) NOT NULL,
    estimated_calories FLOAT NOT NULL,
    protein FLOAT DEFAULT 0,
    carbohydrates FLOAT DEFAULT 0,
    fat FLOAT DEFAULT 0,
    fiber FLOAT DEFAULT 0,
    image_path VARCHAR(255) NULL,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES trainer_clients(client_id) ON DELETE CASCADE
) ENGINE=InnoDB;
