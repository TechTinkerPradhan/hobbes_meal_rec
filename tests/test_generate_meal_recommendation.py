# tests/test_generate_meal_recommendation.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from openai import OpenAI
from services.ai.guardrails_manager import GuardrailsManager

# Load environment
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(env_path, override=True)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
guardrails = GuardrailsManager()

users_path = "data/users.csv"
preferences_path = "data/user_preferences.csv"
prompt_template_path = "services/prompts/meal_recommendation_prompt.txt"

def load_test_user(user_id="1"):
    import csv
    users = {}
    with open(users_path, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            users[row["id"]] = row

    preferences = {}
    with open(preferences_path, mode='r') as infile:
        reader = csv.DictReader(infile)
        for row in reader:
            preferences[row["user_id"]] = row

    return users.get(user_id), preferences.get(user_id)

def test_generate_full_day_meal():
    user_id = "1"
    user, preference = load_test_user(user_id)

    if not user or not preference:
        print(f"❌ Test user {user_id} or preferences not found.")
        return

    with open(prompt_template_path, 'r') as f:
        prompt_template = f.read()

    prompt = prompt_template.format(
        age=user["age"],
        sex=user["sex"],
        weight_kg=user["weight_kg"],
        height_cm=user["height_cm"],
        activity_level=user["activity_level"],
        exercise_frequency_per_week=user["exercise_frequency_per_week"],
        health_conditions=preference["health_conditions"],
        goal_type=preference["goal_type"],
        motivation=preference["motivation"],
        dietary_restrictions=preference["dietary_restrictions"],
        preferred_cuisines=preference["preferred_cuisines"]
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        raw_response = response.choices[0].message.content
        meals = raw_response.split('\n\n')
        
        daily_totals = {
            "calories": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fats_g": 0.0
        }

        print("\n🍽️ Generated Meals:")
        for meal_text in meals:
            if not meal_text.strip():
                continue  # Skip empty chunks
            parsed_meal = guardrails.sanitize_and_validate_output(meal_text)
            if not parsed_meal:
                print(f"⚠️ Skipping invalid meal")
                continue

            print(f"🍴 {parsed_meal['meal_name']}")
            print(f"   Calories: {parsed_meal['calories']} kcal")
            print(f"   Protein: {parsed_meal['protein_g']} g")
            print(f"   Carbs: {parsed_meal['carbs_g']} g")
            print(f"   Fats: {parsed_meal['fats_g']} g")
            print()

            daily_totals["calories"] += parsed_meal["calories"]
            daily_totals["protein_g"] += parsed_meal["protein_g"]
            daily_totals["carbs_g"] += parsed_meal["carbs_g"]
            daily_totals["fats_g"] += parsed_meal["fats_g"]

        print("\n🧮 Daily Totals:")
        print(f"Calories: {daily_totals['calories']} kcal")
        print(f"Protein: {daily_totals['protein_g']} g")
        print(f"Carbs: {daily_totals['carbs_g']} g")
        print(f"Fats: {daily_totals['fats_g']} g")

    except Exception as e:
        print(f"⚠️ Error during meal generation test: {e}")


if __name__ == "__main__":
    test_generate_full_day_meal()
