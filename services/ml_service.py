import os
import joblib
import pandas as pd
import numpy as np
import logging
from config import Config

logger = logging.getLogger(__name__)

class CaloriesPredictionService:
    def __init__(self):
        self.model = None
        self.feature_columns = [
            'Age', 'Height', 'Weight', 'Duration', 
            'Heart_Rate', 'Body_Temp', 'Gender_0', 'Gender_1'
        ]
        self._load_model()

    def _load_model(self):
        """Load the trained machine learning model from disk."""
        candidate_paths = [
            Config.MODEL_PATH,
            os.path.join(os.path.dirname(Config.MODEL_PATH), 'calories_model.joblib'),
            os.path.join(os.path.dirname(Config.MODEL_PATH), 'calories_model.pkl'),
        ]
        
        for path in candidate_paths:
            if os.path.exists(path):
                try:
                    self.model = joblib.load(path)
                    logger.info(f"Loaded trained calories model from {path}")
                    return
                except Exception as e:
                    logger.error(f"Failed loading model from {path}: {e}")
        
        logger.warning("Calories model not found or could not be loaded!")

    def predict(self, age, gender, height, weight, duration, heart_rate, body_temp):
        """
        Predict calories burned based on user/client features.
        
        Parameters:
            age (int/float): Age in years
            gender (str): 'male' or 'female'
            height (float): Height in cm
            weight (float): Weight in kg
            duration (float): Exercise duration in minutes
            heart_rate (float): Heart rate in bpm
            body_temp (float): Body temperature in Celsius (e.g. 37.0 - 41.5)
            
        Returns:
            float: Predicted calories burned (kcal)
        """
        if self.model is None:
            self._load_model()
            if self.model is None:
                raise RuntimeError("Calories prediction model is not available.")

        # Preprocessing matching the trained XGBRegressor:
        # Male -> Gender_0 = 1, Gender_1 = 0
        # Female -> Gender_0 = 0, Gender_1 = 1
        gender_str = str(gender).strip().lower()
        if gender_str in ['male', 'm', '0']:
            g_0, g_1 = 1, 0
        else:
            g_0, g_1 = 0, 1

        input_df = pd.DataFrame([{
            'Age': float(age),
            'Height': float(height),
            'Weight': float(weight),
            'Duration': float(duration),
            'Heart_Rate': float(heart_rate),
            'Body_Temp': float(body_temp),
            'Gender_0': int(g_0),
            'Gender_1': int(g_1)
        }], columns=self.feature_columns)

        prediction = self.model.predict(input_df)
        predicted_calories = float(prediction[0])
        # Calories burned cannot be negative
        return max(0.0, round(predicted_calories, 2))

# Global service instance
ml_service = CaloriesPredictionService()
