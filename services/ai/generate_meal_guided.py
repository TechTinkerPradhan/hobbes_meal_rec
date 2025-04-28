# services/ai/generate_meal_guided.py

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
output_csv_path = "llm_test_data/outputs_guided.csv"
prompt_template_path = "services/prompts/guided_prompt.txt"

# Load datasets
targets_df = pd.read_csv(nutrition_targets_path, dtype={'user_id': str})
users_df = pd.read_csv(users_path, dtype={'id': str})
prefs_df = pd.read_csv(preferences_path, dtype={'user_id': str})

# After merge
merged_df = pd.merge(targets_df, users_df, left_on='user_id', right_on='id', how='inner')
merged_df = pd.merge(merged_df, prefs_df, left_on='user_id', right_on='user_id', how='inner')

# 🛠 Fix column conflicts manually

# Prefer values from preferences file
merged_df['health_conditions'] = merged_df['health_conditions_y']
merged_df['motivation'] = merged_df['motivation_y']

# Fix goal_type (already in preferences properly)
merged_df['goal_type'] = merged_df['goal_type']

# Drop redundant columns
merged_df = merged_df.drop(columns=[
    'health_conditions_x', 'health_conditions_y', 
    'motivation_x', 'motivation_y'
])


# Sample 10 users
fixed_user_ids = ['1861', '354', '1334', '906', '1290', '1274', '939', '1732', '66', '1324']  # (Example IDs, replace with yours)
sampled_users = merged_df[merged_df['user_id'].isin(fixed_user_ids)]

print(sampled_users.columns)


# Load prompt template
with open(prompt_template_path, 'r') as f:
    prompt_template = f.read()

# Output CSV setup
os.makedirs('data', exist_ok=True)
output_fields = [
    "user_id", "mode", "meal_type", "meal_name", 
    "calories", "protein_g", "carbs_g", "fats_g", "rationale"
]
output_file = open(output_csv_path, 'w', newline='')
csv_writer = csv.DictWriter(output_file, fieldnames=output_fields)
csv_writer.writeheader()

# Main generation loop
for idx, user in sampled_users.iterrows():
    try:
        # Fill in the prompt dynamically
        prompt = prompt_template.format(
            age=user["age"],
            sex=user["sex"],
            weight_kg=user["weight_kg"],
            height_cm=user["height_cm"],
            activity_level=user["activity_level"],
            exercise_frequency_per_week=user["exercise_frequency_per_week"],
            health_conditions=user["health_conditions"],
            goal_type=user["goals"],
            motivation=user["motivation"],
            dietary_restrictions=user.get("dietary_restrictions", "None"),
            preferred_cuisines=user.get("preferred_cuisines", "Any"),
            optimal_calories=user["optimal_calories"],
            protein_g=user["protein_g"],
            carbs_g=user["carbs_g"],
            fat_g=user["fat_g"]
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1200
        )

        raw_response = response.choices[0].message.content
        meals = raw_response.split('\n\n')

        for meal_text in meals:
            parsed_meal = guardrails.sanitize_and_validate_output(meal_text)
            if not parsed_meal:
                print(f"⚠️ Skipping invalid meal for user {user['user_id']}")
                continue

            csv_writer.writerow({
                "user_id": user["user_id"],
                "mode": "guided",
                "meal_type": parsed_meal.get('meal_type', 'unknown'),
                "meal_name": parsed_meal["meal_name"],
                "calories": parsed_meal["calories"],
                "protein_g": parsed_meal["protein_g"],
                "carbs_g": parsed_meal["carbs_g"],
                "fats_g": parsed_meal["fats_g"],
                "rationale": parsed_meal["rationale"]
            })

        print(f"✅ Meals generated for user {user['user_id']} (guided)")

    except Exception as e:
        print(f"❌ Failed for user {user['user_id']}: {e}")

output_file.close()
print(f"🎯 Completed guided generation! Results saved to {output_csv_path}")
