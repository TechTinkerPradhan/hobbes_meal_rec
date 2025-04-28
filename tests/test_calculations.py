# tests/test_calculations.py

import os
import sys
import pandas as pd

# Make sure the root project directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.nutrition_calculation.calculations import process_user_row

def test_nutrition_calculation_for_one_user():
    # Paths
    users_path = "data/users.csv"
    preferences_path = "data/user_preferences.csv"

    # Load data
    users_df = pd.read_csv(users_path, dtype={'id': str})
    prefs_df = pd.read_csv(preferences_path, dtype={'user_id': str})

    # Pick one user (user_id = '1' for example)
    test_user_id = '1'
    
    user_row = users_df[users_df['id'] == test_user_id]
    pref_row = prefs_df[prefs_df['user_id'] == test_user_id]

    if user_row.empty or pref_row.empty:
        print(f"❌ Test user {test_user_id} not found in data.")
        return

    user_row = user_row.iloc[0]
    pref_row = pref_row.iloc[0]

    # Display raw user data
    print("\n👤 User Raw Data:")
    print(user_row.to_dict())
    print("\n❤️ Preferences:")
    print(pref_row.to_dict())

    # Process and calculate
    result = process_user_row(user_row, pref_row)

    if result:
        print("\n✅ Calculated Nutrition Targets:")
        for k, v in result.items():
            print(f"{k}: {v}")
    else:
        print("\n⚠️ Failed to calculate nutrition targets for user.")

if __name__ == "__main__":
    test_nutrition_calculation_for_one_user()
