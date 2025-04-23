import pandas as pd
import uuid
import random
from datetime import datetime, timedelta
from pathlib import Path

Path("data").mkdir(exist_ok=True)

def generate_meals():
    users_df = pd.read_csv("data/users.csv")
    meal_types = ["breakfast", "lunch", "dinner", "snack"]
    meals = []

    for user_id in users_df["id"]:
        for _ in range(random.randint(3, 6)):  # random number of meals per user
            meal_id = str(uuid.uuid4())
            meal_type = random.choice(meal_types)
            total_calories = random.randint(200, 900)
            protein = round(random.uniform(5, 40), 1)
            carbs = round(random.uniform(20, 100), 1)
            fat = round(random.uniform(5, 30), 1)
            satisfaction = random.choice(["low", "medium", "high"])
            created_at = datetime.now() - timedelta(days=random.randint(0, 30))
            meals.append({
                "id": meal_id,
                "user_id": user_id,
                "meal_type": meal_type,
                "total_calories": total_calories,
                "total_protein": protein,
                "total_carbs": carbs,
                "total_fat": fat,
                "satisfaction": satisfaction,
                "created_at": created_at.isoformat()
            })

    df = pd.DataFrame(meals)
    df.to_csv("data/meals.csv", index=False)
    print("✅ Meals dataset saved to data/meals.csv")

if __name__ == "__main__":
    generate_meals()
