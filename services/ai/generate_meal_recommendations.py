# services/ai/generate_meal_recommendations.py

import csv
import os
from dotenv import load_dotenv
from openai import OpenAI
from services.ai.guardrails_manager import GuardrailsManager

# Load environment
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(env_path, override=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
guardrails = GuardrailsManager()

# Paths
users_path = "data/users.csv"
preferences_path = "data/user_preferences.csv"
prompt_template_path = "services/prompts/meal_recommendation_prompt.txt"
output_meals_path = "data/full_day_meal_recommendations.csv"
output_totals_path = "data/daily_nutrition_totals.csv"

# Load prompt template
with open(prompt_template_path, 'r') as f:
    prompt_template = f.read()

# Read users
users = {}
with open(users_path, mode='r') as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        users[row["id"]] = row

# Read preferences
preferences = {}
with open(preferences_path, mode='r') as infile:
    reader = csv.DictReader(infile)
    for row in reader:
        preferences[row["user_id"]] = row

# Ensure output directory
os.makedirs('data', exist_ok=True)

# Output files
meal_writer = csv.writer(open(output_meals_path, 'w', newline=''))
meal_writer.writerow([
    "user_id", "meal_type", "meal_name", "ingredients", "calories", "protein_g", "carbs_g", "fats_g", "rationale"
])

totals_writer = csv.writer(open(output_totals_path, 'w', newline=''))
totals_writer.writerow([
    "user_id", "total_calories", "total_protein_g", "total_carbs_g", "total_fats_g"
])

# Meal type mapping
meal_order = ["breakfast", "morning_snack", "lunch", "evening_snack", "dinner"]

# For each user
for user_id in users.keys():
    user = users[user_id]
    preference = preferences.get(user_id)
    
    if not preference:
        continue
    
    # Fill the full-day prompt
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
        # LLM call
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        raw_response = response.choices[0].message.content

        # Split the response based on headings
        meals = raw_response.split('\n\n')
        
        daily_totals = {
            "calories": 0.0,
            "protein_g": 0.0,
            "carbs_g": 0.0,
            "fats_g": 0.0
        }

        for meal_text, meal_type in zip(meals, meal_order):
            parsed_meal = guardrails.sanitize_and_validate_output(meal_text)
            
            if not parsed_meal:
                print(f"⚠️ Skipping invalid meal for user {user_id} ({meal_type})")
                continue

            meal_writer.writerow([
                user_id,
                meal_type,
                parsed_meal["meal_name"],
                parsed_meal["ingredients"],
                parsed_meal["calories"],
                parsed_meal["protein_g"],
                parsed_meal["carbs_g"],
                parsed_meal["fats_g"],
                parsed_meal["rationale"]
            ])

            # Sum daily totals
            daily_totals["calories"] += parsed_meal["calories"]
            daily_totals["protein_g"] += parsed_meal["protein_g"]
            daily_totals["carbs_g"] += parsed_meal["carbs_g"]
            daily_totals["fats_g"] += parsed_meal["fats_g"]

        totals_writer.writerow([
            user_id,
            daily_totals["calories"],
            daily_totals["protein_g"],
            daily_totals["carbs_g"],
            daily_totals["fats_g"]
        ])

        print(f"✅ Generated full day meals for user {user_id}")

    except Exception as e:
        print(f"⚠️ Failed for user {user_id}: {e}")

print("🎯 All users processed successfully!")
