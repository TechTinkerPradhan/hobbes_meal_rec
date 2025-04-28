# utils/generate_user_preferences.py

import csv
import random
import os

# Input users CSV
input_users_path = "data/users.csv"
# Output preferences CSV
output_preferences_path = "data/user_preferences.csv"

# Possible health conditions
health_conditions_list = [
    "none", "pre-diabetes", "diabetes", "hypertension", "heart disease", "high cholesterol"
]

# Goal types
goal_types = [
    "weight_loss", "muscle_gain", "reverse_metabolic_markers", "longevity", "optimize_fitness"
]

# Motivations
motivations = [
    "appearance", "health", "energy", "sports_performance", "doctor_recommendation"
]

# Dietary restrictions
dietary_restrictions_list = [
    "none", "vegetarian", "vegan", "keto", "paleo", "gluten_free", "low_fodmap"
]

# Preferred cuisines
preferred_cuisines_list = [
    "Italian", "Indian", "Mexican", "Chinese", "Japanese", "Mediterranean", "Thai", "American", "Middle Eastern"
]

# Ensure data/ exists
os.makedirs('data', exist_ok=True)

# Read users and generate preferences
with open(input_users_path, mode='r') as infile, open(output_preferences_path, mode='w', newline='') as outfile:
    reader = csv.DictReader(infile)
    writer = csv.writer(outfile)

    # Write header
    writer.writerow([
        "user_id", "health_conditions", "goal_type", "motivation", "dietary_restrictions", "preferred_cuisines"
    ])

    for row in reader:
        user_id = row["id"]

        health_conditions = random.choices(health_conditions_list, weights=[0.6, 0.1, 0.1, 0.1, 0.05, 0.05], k=1)[0]
        goal_type = random.choice(goal_types)
        motivation = random.choice(motivations)
        
        # Allow for multiple dietary restrictions or none
        if random.random() < 0.7:
            dietary_restrictions = random.choice(dietary_restrictions_list)
        else:
            dietary_restrictions = "none"
        
        # Pick 1–3 preferred cuisines
        preferred_cuisines = random.sample(preferred_cuisines_list, random.randint(1, 3))
        preferred_cuisines_str = "; ".join(preferred_cuisines)

        writer.writerow([
            user_id, health_conditions, goal_type, motivation, dietary_restrictions, preferred_cuisines_str
        ])

print(f"✅ Generated user preferences and saved to {output_preferences_path}")
