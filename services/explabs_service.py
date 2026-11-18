import base64
import json
import os
import logging
from openai import OpenAI, APIStatusError, AuthenticationError, PermissionDeniedError, NotFoundError, RateLimitError, InternalServerError, APIConnectionError
from config import Config

logger = logging.getLogger(__name__)

def get_explabs_client():
    """Create and return an OpenAI-compatible client targeting Experiential Labs."""
    api_key = Config.EXPLABS_API_KEY or os.environ.get('EXPLABS_API_KEY', '')
    base_url = Config.EXPLABS_API_BASE_URL or 'https://api.experientiallabs.ai/v1'
    
    if not api_key:
        return None
        
    return OpenAI(api_key=api_key, base_url=base_url)

def test_explabs_connection():
    """
    Test connection to Experiential Labs API and check if model is accessible.
    Returns (success: bool, message: str, models: list)
    """
    client = get_explabs_client()
    if not client:
        return False, "Experiential Labs API key (EXPLABS_API_KEY) is missing in .env file.", []

    try:
        models_response = client.models.list()
        model_ids = [getattr(m, 'id', str(m)) for m in models_response]
        current_model = Config.EXPLABS_MODEL
        if current_model in model_ids:
            return True, f"Connected to Experiential Labs successfully. Model '{current_model}' is available.", model_ids
        else:
            return True, f"Connected to Experiential Labs, but model '{current_model}' is not in listed models.", model_ids
    except AuthenticationError:
        return False, "Experiential Labs authentication failed (401). Invalid EXPLABS_API_KEY.", []
    except PermissionDeniedError:
        return False, "Experiential Labs permission denied (403).", []
    except NotFoundError:
        return False, "Experiential Labs endpoint not found (404).", []
    except RateLimitError:
        return False, "Experiential Labs rate limit exceeded (429).", []
    except InternalServerError:
        return False, "Experiential Labs internal server error (500).", []
    except APIStatusError as e:
        return False, f"Experiential Labs API error ({e.status_code}): {e.message}", []
    except APIConnectionError:
        return False, f"Cannot connect to Experiential Labs at {Config.EXPLABS_API_BASE_URL}.", []
    except Exception as e:
        return False, f"Experiential Labs connection check failed: {str(e)}", []

def encode_image(image_path):
    """Encode local image file to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_food_image(image_path):
    """
    Analyze food image using Experiential Labs Vision API.
    Returns structured nutrition information dictionary.
    """
    api_key = Config.EXPLABS_API_KEY or os.environ.get('EXPLABS_API_KEY', '')
    
    if not api_key:
        logger.warning("Experiential Labs API key is missing. Returning helpful notice.")
        return {
            "success": False,
            "error": "Experiential Labs API key is not configured. Please add EXPLABS_API_KEY to your .env file.",
            "is_key_missing": True,
            "status_code": 401
        }

    client = get_explabs_client()
    if not client:
        return {
            "success": False,
            "error": "Experiential Labs client could not be initialized.",
            "status_code": 500
        }

    try:
        base64_image = encode_image(image_path)
        
        # Determine image mime type
        ext = os.path.splitext(image_path)[1].lower().replace('.', '')
        mime = 'image/jpeg' if ext in ['jpg', 'jpeg'] else f'image/{ext}'

        system_prompt = (
            "You are an expert nutritionist and computer vision food analyzer powered by Experiential Labs. "
            "Analyze the image and identify the primary food item(s). "
            "Estimate its portion size, total calories, and macronutrients (protein, carbs, fat, fiber). "
            "You MUST respond ONLY with valid, raw JSON (no markdown formatting, no backticks, no code blocks) matching this exact schema:\n"
            "{\n"
            '  "food_name": "Grilled Chicken Salad with Avocado",\n'
            '  "quantity": "1 medium bowl (approx 350g)",\n'
            '  "estimated_calories": 420.0,\n'
            '  "protein": 38.0,\n'
            '  "carbohydrates": 14.0,\n'
            '  "fat": 22.0,\n'
            '  "fiber": 7.0,\n'
            '  "health_rating": "Healthy",\n'
            '  "description": "Rich in lean protein and healthy monounsaturated fats.",\n'
            '  "ingredients": ["Grilled chicken breast", "Lettuce", "Cherry tomatoes", "Avocado", "Olive oil dressing"]\n'
            "}"
        )

        response = client.chat.completions.create(
            model=Config.EXPLABS_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this food image and provide the estimated nutritional breakdown in the requested JSON structure."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{base64_image}",
                                "detail": "low"
                            }
                        }
                    ]
                }
            ],
            max_tokens=600,
            temperature=0.2
        )

        raw_content = response.choices[0].message.content.strip()
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:]
        if raw_content.startswith("```"):
            raw_content = raw_content[3:]
        if raw_content.endswith("```"):
            raw_content = raw_content[:-3]
        raw_content = raw_content.strip()

        data = json.loads(raw_content)
        
        result = {
            "success": True,
            "food_name": str(data.get("food_name", "Identified Food Item")),
            "quantity": str(data.get("quantity", "1 serving")),
            "estimated_calories": float(data.get("estimated_calories", 0.0)),
            "protein": float(data.get("protein", 0.0)),
            "carbohydrates": float(data.get("carbohydrates", 0.0)),
            "fat": float(data.get("fat", 0.0)),
            "fiber": float(data.get("fiber", 0.0)),
            "health_rating": str(data.get("health_rating", "Balanced")),
            "description": str(data.get("description", "Nutritional estimation completed via Experiential Labs.")),
            "ingredients": data.get("ingredients", [])
        }
        return result

    except AuthenticationError:
        logger.error("Experiential Labs 401: Invalid API key")
        return {
            "success": False,
            "error": "Experiential Labs authentication failed (401). Please check EXPLABS_API_KEY in your .env file.",
            "status_code": 401
        }
    except PermissionDeniedError:
        logger.error("Experiential Labs 403: Permission denied")
        return {
            "success": False,
            "error": "Experiential Labs permission denied (403). Your account does not have access to this resource.",
            "status_code": 403
        }
    except NotFoundError:
        logger.error(f"Experiential Labs 404: Model {Config.EXPLABS_MODEL} not found")
        return {
            "success": False,
            "error": f"Experiential Labs model '{Config.EXPLABS_MODEL}' was not found (404). Please verify EXPLABS_MODEL in .env.",
            "status_code": 404
        }
    except RateLimitError:
        logger.error("Experiential Labs 429: Rate limit exceeded")
        return {
            "success": False,
            "error": "Experiential Labs rate limit exceeded (429). Please wait a moment before trying again.",
            "status_code": 429
        }
    except InternalServerError:
        logger.error("Experiential Labs 500: Server error")
        return {
            "success": False,
            "error": "Experiential Labs service encountered an internal server error (500). Please retry shortly.",
            "status_code": 500
        }
    except APIStatusError as e:
        logger.error(f"Experiential Labs APIStatusError {e.status_code}: {e.message}")
        if e.status_code == 402:
            return {
                "success": False,
                "error": "Experiential Labs account credits required (402): Add credits or verify your account at https://platform.experientiallabs.ai/credits.",
                "status_code": 402
            }
        return {
            "success": False,
            "error": f"Experiential Labs API returned error ({e.status_code}): {e.message}",
            "status_code": e.status_code
        }
    except APIConnectionError as e:
        logger.error(f"Experiential Labs connection error: {e}")
        return {
            "success": False,
            "error": f"Cannot connect to Experiential Labs at {Config.EXPLABS_API_BASE_URL}. Please check your internet connection.",
            "status_code": 0
        }
    except Exception as e:
        logger.error(f"Experiential Labs unexpected error: {e}")
        return {
            "success": False,
            "error": f"Experiential Labs AI analysis failed: {str(e)}",
            "status_code": 500
        }

def generate_fitness_recommendations(profile_data, workout_stats=None, food_stats=None):
    """
    Generate tailored AI fitness and nutrition recommendations using Experiential Labs.
    """
    client = get_explabs_client()
    if not client:
        return {
            "success": False,
            "error": "Experiential Labs API key is not configured.",
            "status_code": 401
        }

    try:
        user_context = (
            f"User Profile: Name: {profile_data.get('name', 'Athlete')}, "
            f"Age: {profile_data.get('age', 'N/A')}, Gender: {profile_data.get('gender', 'N/A')}, "
            f"Height: {profile_data.get('height', 'N/A')}cm, Weight: {profile_data.get('weight', 'N/A')}kg. "
            f"Recent Activity: {workout_stats.get('total_workouts', 0) if workout_stats else 0} workouts logged, "
            f"{workout_stats.get('total_burned', 0) if workout_stats else 0} kcal burned. "
            f"Dietary Intake: {food_stats.get('total_consumed', 0) if food_stats else 0} kcal consumed."
        )

        prompt = (
            "Based on the following user biometrics and activity history, provide 3 actionable, professional fitness recommendations "
            "and 3 nutritional recommendations to optimize energy balance and athletic performance. "
            "Format the response in concise, structured bullet points without unnecessary disclaimers.\n\n"
            f"{user_context}"
        )

        response = client.chat.completions.create(
            model=Config.EXPLABS_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional sports nutritionist and exercise physiologist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        return {
            "success": True,
            "recommendations": response.choices[0].message.content.strip()
        }
    except APIStatusError as e:
        return {
            "success": False,
            "error": f"Experiential Labs API error ({e.status_code}): {e.message}",
            "status_code": e.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 500
        }
