# services/ai/generate_meal_partial_guided.py

import os
import sys
import random
import csv
import pandas as pd

from dotenv import load_dotenv
from openai import OpenAI

# Add root project directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from services.ai.guardrails_manager import GuardrailsManager

# Load environment
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(env_path, override=True)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
guardrails = GuardrailsManager()

# Paths
nutrition_targets_path = "data/user_nutrition_targets.csv"
users_path = "data/users.csv"
preferences_path = "data/user_preferences.csv"
output_csv_path = "llm_test_data/outputs_partial_guided.csv"
prompt_template_path = "services/prompts/partial_guided_prompt.txt"

# Load datasets
targets_df = pd.read_csv(nutrition_targets_path, dtype={'user_id': str})
users_df = pd.read_csv(users_path, dtype={'id': str})
prefs_df = pd.read_csv(preferences_path, dtype={'user_id': str})

# Merge all data
merged_df = pd.merge(targets_df, users_df, left_on='user_id', right_on='id', how='inner')
merged_df = pd.merge(merged_df, prefs_df, left_on='user_id', right_on='user_id', how='inner')

# Fix conflicts and pick correct columns
merged_df['health_conditions'] = merged_df['health_conditions_y']
merged_df['motivation'] = merged_df['motivation_y']
merged_df['goal_type'] = merged_df['goal_type']

# Drop redundant columns
merged_df = merged_df.drop(columns=[
    'health_conditions_x', 'health_conditions_y',
    'motivation_x', 'motivation_y'
])

# Fixed user list
fixed_user_ids = ['1861', '354', '1334', '906', '1290', '1274', '939', '1732', '66', '1324']
sampled_users = merged_df[merged_df['user_id'].isin(fixed_user_ids)]

# Load prompt template
with open(prompt_template_path, 'r') as f:
    prompt_template = f.read()

# Output CSV setup
os.makedirs('llm_test_data', exist_ok=True)
output_fields = [
    "user_id", "mode", "meal_type", "meal_name", 
    "calories", "protein_g", "carbs_g", "fats_g", "rationale"
]
output_file = open(output_csv_path, 'w', newline='')
csv_writer = csv.DictWriter(output_file, fieldnames=output_fields)
csv_writer.writeheader()

# Main generation loop
for idx, user in sampled_users.iterrows():
    success = False
    attempts = 0
    max_attempts = 3

    while not success and attempts < max_attempts:
        try:
            prompt = prompt_template.format(
                age=user.get("age", "Unknown"),
                sex=user.get("sex", "Unknown"),
                weight_kg=user.get("weight_kg", "Unknown"),
                height_cm=user.get("height_cm", "Unknown"),
                activity_level=user.get("activity_level", "Unknown"),
                exercise_frequency_per_week=user.get("exercise_frequency_per_week", "Unknown"),
                health_conditions=user.get("health_conditions", "None"),
                goal_type=user.get("goal_type", "Unknown"),
                motivation=user.get("motivation", "Unknown"),
                dietary_restrictions=user.get("dietary_restrictions", "None"),
                preferred_cuisines=user.get("preferred_cuisines", "Any"),
                optimal_calories=user.get("optimal_calories", 2000),
                ibw_kg=user.get("ibw_kg", 65)
            )

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1200
            )

            raw_response = response.choices[0].message.content
            meals = raw_response.split('\n\n')

            valid_meals = []
            for meal_text in meals:
                parsed_meal = guardrails.sanitize_and_validate_output(meal_text)
                if parsed_meal:
                    valid_meals.append(parsed_meal)
            
            if len(valid_meals) >= 5:
                for meal in valid_meals:
                    csv_writer.writerow({
                        "user_id": user["user_id"],
                        "mode": "partial_guided",
                        "meal_type": meal.get('meal_type', 'unknown'),
                        "meal_name": meal["meal_name"],
                        "calories": meal["calories"],
                        "protein_g": meal["protein_g"],
                        "carbs_g": meal["carbs_g"],
                        "fats_g": meal["fats_g"],
                        "rationale": meal["rationale"]
                    })
                print(f"✅ Meals generated for user {user['user_id']} (partial guided)")
                success = True
            else:
                print(f"⚠️ Parsing failed for user {user['user_id']}, retrying (attempt {attempts + 1})...")
                attempts += 1

        except Exception as e:
            print(f"❌ Error during generation for user {user['user_id']} (attempt {attempts + 1}): {e}")
            attempts += 1

    if not success:
        print(f"❌ Could not generate valid meals for user {user['user_id']} after {max_attempts} attempts")

output_file.close()
print(f"🎯 Completed partial-guided generation! Results saved to {output_csv_path}")
