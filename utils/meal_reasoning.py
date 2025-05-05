from openai import OpenAI
import os
from dotenv import load_dotenv

# Load API key
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(env_path, override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def reason_meal_components_and_servings(meal_name: str, meal_type: str, user_profile: dict) -> list:
    """
    Use LLM to reason about meal components and their likely serving sizes.

    Args:
        meal_name (str): Name of the meal (e.g., "Kebab and 3 rotis")
        meal_type (str): Type of meal (e.g., "Lunch", "Dinner")
        user_profile (dict): Info like weight, height, sex, age, activity level, etc.

    Returns:
        List[dict]: Each dict contains `component`, `estimated_serving_qty`, and `serving_unit`
    """
    system_msg = "You are a meal reasoning assistant. You break down meals into components and estimate how much of each was likely consumed based on user profile and meal type."
    
    user_msg = f"""
User Profile:
- Age: {user_profile['age']}
- Sex: {user_profile['sex']}
- Weight: {user_profile['weight_kg']} kg
- Height: {user_profile['height_cm']} cm
- Activity Level: {user_profile['activity_level']}

Meal Log:
- Meal Name: {meal_name}
- Meal Type: {meal_type}

Respond with a JSON array where each entry contains:
- component (string)
- estimated_serving_qty (float)
- serving_unit (string, e.g., 'cup', 'piece', 'g')
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            temperature=0.3
        )
        import json
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ LLM reasoning failed: {e}")
        return []
