import pandas as pd
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

Path("data").mkdir(exist_ok=True)

def generate_users():
    names = ["John Doe", "Jane Smith", "Alice Johnson", "Bob Lee", "Charlie Kim", "Dana Scully", "Elliot Alderson"]
    activity_levels = ["low", "moderate", "high"]
    sex_options = ["male", "female", "non-binary"]
    health_conditions = [["none"], ["diabetes"], ["high_cholesterol"], ["hypertension"], ["asthma"], ["diabetes", "hypertension"]]
    goal_types = [["weight_loss"], ["muscle_gain"], ["maintenance"], ["weight_loss", "muscle_gain"]]
    motivations = ["Get fit for summer", "Doctor recommended", "Preparing for marathon", "General wellness", "Improve mental health"]
    
    users = []

    for _ in range(1000):
        user_id = str(uuid.uuid4())
        name = random.choice(names)
        email = f"{name.lower().replace(' ', '')}{random.randint(1,9999)}@example.com"
        date_of_birth = datetime.now() - timedelta(days=random.randint(20*365, 50*365))
        sex = random.choice(sex_options)
        weight_value = round(random.uniform(50, 120), 1)
        height_value = round(random.uniform(150, 200), 1)
        activity_level = random.choice(activity_levels)
        exercise_frequency = random.randint(0, 7)
        health_cond = random.choice(health_conditions)
        goal = random.choice(goal_types)
        motivation = random.choice(motivations)
        
        users.append({
            "id": user_id,
            "name": name,
            "email": email,
            "date_of_birth": date_of_birth.date().isoformat(),
            "sex": sex,
            "weight_value": weight_value,
            "height_value": height_value,
            "activity_level": activity_level,
            "exercise_frequency": exercise_frequency,
            "health_conditions": health_cond,
            "goal_type": goal,
            "motivation": motivation
        })

    df = pd.DataFrame(users)
    df.to_csv("data/users.csv", index=False)
    print("✅ Users dataset saved to data/users.csv")

if __name__ == "__main__":
    generate_users()
