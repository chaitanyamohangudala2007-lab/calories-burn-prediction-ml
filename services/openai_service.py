"""
Legacy wrapper for backwards-compatibility.
All AI functionality has been migrated to Experiential Labs API (explabs_service).
"""
from services.explabs_service import (
    analyze_food_image,
    generate_fitness_recommendations,
    test_explabs_connection,
    get_explabs_client
)
