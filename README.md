# FitAI - Calories Burn Prediction and Food Nutrition Analysis System

An end-to-end AI-powered fitness management and nutritional tracking web application built with **Flask**, **XGBoost Machine Learning**, **Experiential Labs Multimodal Vision AI**, **MySQL**, and **Chart.js**.

---

## 🚀 Key Features

### 1. Dual Role Authentication
- **Normal User Portal:** Separate registration and login, password hashing (`werkzeug.security`), session management, and personal analytics.
- **Gym Trainer Portal:** Separate trainer registration and login. Coaches manage their own clients with strict role-based data isolation.

### 2. Machine Learning Calories Burn Prediction
- Trained on physiological biometric data (`exercise.csv` + `calories.csv`) using an **XGBoost Regressor** (Mean Absolute Error $\approx 1.48$ kcal).
- Features: `Age`, `Gender`, `Height`, `Weight`, `Duration`, `Heart Rate`, and `Body Temperature`.
- Automatically logs workouts to MySQL `workout_history` with intensity ratings.

### 3. AI Food Nutrition Analyzer (Experiential Labs Multimodal Vision)
- **Image Upload & Live Camera Snapshot:** Point the camera at any meal or upload a photo.
- Powered by **Experiential Labs API** (`https://api.experientiallabs.ai/v1`) using OpenAI-compatible SDK with custom base URL.
- Vision AI identifies food items, portion size, and extracts complete macronutrient breakdowns:
  - Estimated Calories (kcal)
  - Protein (g)
  - Carbohydrates (g)
  - Dietary Fat (g)
  - Dietary Fiber (g)
- Saved automatically to MySQL `food_analysis_history` with visual previews.
- Dedicated AI-generated fitness and nutrition recommendations.

### 4. Interactive Dashboards & Analytics (Chart.js)
- **User Dashboard:** 4 overview metric cards, 7-day energy expenditure vs consumption bar chart, and macronutrient doughnut chart.
- **Trainer Dashboard:** Overview of total clients, supervised workouts, total calories burned, and average client performance.
- **Individual Client Drill-Down:** Dedicated client view with 5 distinct Chart.js visualizations, automated BMI calculations, and history logs.

---

## 🛠️ Technology Stack

- **Backend:** Python 3, Flask
- **Frontend:** HTML5, CSS3, JavaScript (ES6), Bootstrap 5, Bootstrap Icons, Chart.js
- **Machine Learning:** XGBoost Regressor, Scikit-learn, Pandas, NumPy, Joblib
- **Multimodal AI Provider:** Experiential Labs API (`https://api.experientiallabs.ai/v1`)
- **Database:** MySQL 8.0 / MySQL Workbench

---

## 📂 Project Structure

```
final project/
│
├── app.py                     # Main Flask application entry point
├── config.py                  # Application configuration & environment settings
├── requirements.txt           # Python package dependencies
├── .env                       # Environment variables (DB credentials, Experiential Labs key)
├── .env.example               # Example environment template
├── README.md                  # Comprehensive setup & execution guide
│
├── models/
│   ├── calories_model.pkl     # Trained XGBoost ML model
│   └── calories_model.joblib  # Trained model export (joblib)
│
├── database/
│   ├── db_connection.py       # MySQL connection pool & query helpers
│   └── schema.sql             # SQL schema DDL for calories_db
│
├── routes/
│   ├── auth.py                # User & Trainer authentication routes
│   ├── user.py                # User dashboard & profile routes
│   ├── trainer.py             # Gym trainer & client management routes
│   ├── prediction.py          # ML calories prediction & workout history
│   └── food_analysis.py       # Experiential Labs food vision & nutrition history
│
├── services/
│   ├── ml_service.py          # Machine learning inference service
│   └── explabs_service.py     # Experiential Labs API integration service
│
├── templates/                 # Clean, modern SaaS Jinja2 HTML templates
│   ├── base.html              # Core navigation layout & alerts
│   ├── home.html              # Landing page
│   ├── about.html             # Academic project description
│   ├── features.html          # Feature overview
│   ├── login.html             # User login
│   ├── register.html          # User registration
│   ├── trainer_login.html     # Trainer login
│   ├── trainer_register.html  # Trainer registration
│   ├── user_dashboard.html    # User analytics dashboard
│   ├── trainer_dashboard.html # Trainer management dashboard
│   ├── prediction.html        # ML prediction form & results
│   ├── workout_history.html   # Workout history logs with filters
│   ├── food_analyzer.html     # AI food scanner (camera + upload)
│   ├── nutrition_history.html # Dietary history log
│   ├── profile.html           # User profile & settings
│   ├── trainer_clients.html   # Client management list & BMI
│   ├── add_client.html        # Add new client form
│   ├── client_details.html    # Individual client analytics & 5 charts
│   ├── client_workout_history.html
│   ├── client_nutrition_history.html
│   └── trainer_profile.html   # Trainer profile settings
│
├── static/
│   ├── css/style.css          # Modern SaaS fitness styling
│   └── js/
│       ├── main.js            # Alerts & instant image preview
│       └── camera.js          # Live webcam capture functionality
│
└── uploads/                   # Stored food images
```

---

## 💻 Step-by-Step Instructions to Run in VS Code

### Step 1: Open the Project in VS Code
1. Open **Visual Studio Code**.
2. Click **File** &rarr; **Open Folder...** and select `final project`.
3. Open a new terminal in VS Code: Press <kbd>Ctrl</kbd> + <kbd>`</kbd> (or go to **Terminal** &rarr; **New Terminal**).

### Step 2: Configure Environment Variables (`.env`)
Open the `.env` file in VS Code and verify your credentials:

```env
# Flask Configuration
SECRET_KEY=dev-fitness-secret-key-2026-secure
FLASK_APP=app.py
FLASK_ENV=development

# MySQL Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=sdsnkc123
DB_NAME=calories_db

# Experiential Labs API Configuration
EXPLABS_API_BASE_URL=https://api.experientiallabs.ai/v1
EXPLABS_API_KEY=xpl_7060f4e7253ef66678fb35bb4854176cf62c9958
EXPLABS_MODEL=gpt-4o-mini
```

### Step 3: Run Database Schema in MySQL Workbench
1. Open **MySQL Workbench**.
2. Connect to your local MySQL instance.
3. Open the file `database/schema.sql` in MySQL Workbench.
4. Execute the SQL script (click the lightning bolt icon ⚡) to create the `calories_db` database and its 5 tables:
   - `users`
   - `trainers`
   - `trainer_clients`
   - `workout_history`
   - `food_analysis_history`

### Step 4: Run the Application
In your VS Code terminal, run:
```bash
python app.py
```

### Step 5: Open in Your Web Browser
Open your browser and navigate to:
```
http://127.0.0.1:5000/
```
