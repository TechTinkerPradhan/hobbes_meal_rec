# tests/test_meals_reasoning.py
import os 
import sys
import pytest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.meal_reasoning import reason_meal_components_and_servings

def test_reasoning_response_format():
    user_profile = {
        "age": 28,
        "sex": "male",
        "weight_kg": 72,
        "height_cm": 178,
        "activity_level": "Moderately Active"
    }

    meal_name = "Grilled chicken with rice and salad"
    meal_type = "Lunch"

    result = reason_meal_components_and_servings(meal_name, meal_type, user_profile)

    assert isinstance(result, list)
    assert len(result) > 0

    for entry in result:
        assert "component" in entry
        assert "estimated_serving_qty" in entry
        assert "serving_unit" in entry
        assert isinstance(entry["component"], str)
        assert isinstance(entry["estimated_serving_qty"], (int, float))
        assert isinstance(entry["serving_unit"], str)
