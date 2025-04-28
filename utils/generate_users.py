# utils/generate_users.py

import csv
import random
import os
from faker import Faker

# Initialize Faker
fake = Faker()

# Activity levels
activity_levels = [
    "Sedentary",          # Little to no exercise
    "Lightly Active",     # Light exercise 1–3 days/week
    "Moderately Active",  # Moderate exercise 3–5 days/week
    "Very Active",        # Hard exercise 6–7 days/week
    "Super Active"        # Very intense daily exercise
]

# Number of users to generate
NUM_USERS = 2000

# Ensure data/ exists
os.makedirs('data', exist_ok=True)

# Output CSV path
output_path = "data/users.csv"

# Create users
with open(output_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    # Write header
    writer.writerow([
        "id", "name", "email", "age", "sex",
        "weight_kg", "height_cm",
        "activity_level", "exercise_frequency_per_week"
    ])
    
    for user_id in range(1, NUM_USERS + 1):
        name = fake.name()
        email = fake.email()
        age = random.randint(18, 70)
        sex = random.choice(["male", "female"])
        weight_kg = round(random.uniform(50, 120), 1)  # Random weight
        height_cm = round(random.uniform(150, 200), 1)  # Random height
        activity_level = random.choice(activity_levels)
        exercise_frequency = random.randint(0, 7)

        writer.writerow([
            user_id, name, email, age, sex,
            weight_kg, height_cm,
            activity_level, exercise_frequency
        ])

print(f"✅ Generated {NUM_USERS} users and saved to {output_path}")
