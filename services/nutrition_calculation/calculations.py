# services/nutrition_calculation/calculations.py

import os
import csv
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import ast

# ------------------ Logger Setup ------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------ Constants ------------------

# Default body fat percentage assumptions if missing
DEFAULT_BODY_FAT_MALE = 20
DEFAULT_BODY_FAT_FEMALE = 28

# Activity level multipliers for TDEE calculation
ACTIVITY_MULTIPLIERS = {
    'Sedentary': 1.2,
    'Lightly Active': 1.375,
    'Moderately Active': 1.55,
    'Very Active': 1.725,
    'Extra Active': 1.9
}

# Macronutrient strategy mappings based on health conditions or goals
MACRO_STRATEGIES = {
    'diabetes': {'protein': 0.30, 'carbs': 0.35, 'fat': 0.35},
    'pre-diabetes': {'protein': 0.30, 'carbs': 0.35, 'fat': 0.35},
    'insulin_resistance': {'protein': 0.30, 'carbs': 0.35, 'fat': 0.35},
    'muscle_gain': {'protein': 0.35, 'carbs': 0.40, 'fat': 0.25},
    'gain_weight': {'protein': 0.35, 'carbs': 0.40, 'fat': 0.25},
    'lose_weight': {'protein': 0.35, 'carbs': 0.40, 'fat': 0.25},
    'heart_disease': {'protein': 0.30, 'carbs': 0.40, 'fat': 0.30}
}

# Default fallback macros if no specific condition or goal applies
DEFAULT_MACROS = {'protein': 0.30, 'carbs': 0.45, 'fat': 0.25}

# ------------------ Core Calculation Functions ------------------

def mifflin_st_jeor(sex, weight_kg, height_cm, age):
    """Mifflin-St Jeor BMR formula"""
    if sex.lower() == 'male':
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

def katch_mcardle(weight_kg, body_fat_percent):
    """Katch-McArdle BMR formula (if body fat % is known)"""
    lean_mass = weight_kg * (1 - body_fat_percent / 100)
    return 370 + 21.6 * lean_mass

def weighted_bmr(sex, weight_kg, height_cm, age, body_fat_percent=None):
    """
    Weighted combination of Mifflin-St Jeor and Katch-McArdle formulas.
    Fallback to MSJ alone if body fat % is not available.
    """
    bmr_msj = mifflin_st_jeor(sex, weight_kg, height_cm, age)
    if body_fat_percent is not None:
        bmr_kma = katch_mcardle(weight_kg, body_fat_percent)
        return 0.8 * bmr_msj + 0.2 * bmr_kma
    else:
        return bmr_msj

def calculate_ibw(sex, height_cm):
    """
    Calculate Ideal Body Weight (IBW) using Hamwi formula.
    """
    height_in = height_cm / 2.54
    if sex.lower() == 'male':
        ibw_lbs = 106 + 6 * (height_in - 60)
    else:
        ibw_lbs = 100 + 5 * (height_in - 60)
    ibw_kg = ibw_lbs / 2.20462
    return round(ibw_kg, 2)

def get_activity_multiplier(activity_level):
    """Fetch activity multiplier or default to 'Moderately Active'"""
    return ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)

def adjust_calories_for_goal(tdee, goals):
    """Apply adjustment based on goals"""
    goals = [g.lower() for g in goals]
    if 'lose_weight' in goals:
        return tdee * 0.85  # 15% deficit
    elif 'gain_weight' in goals or 'muscle_gain' in goals:
        return tdee * 1.15  # 15% surplus
    else:
        return tdee  # Maintain calories

def select_macro_split(health_conditions, goals):
    """
    Select macronutrient distribution based on user's health conditions and goals.
    Priority: Health condition first, then goals, else default.
    """
    for cond in health_conditions:
        cond_key = cond.lower()
        if cond_key in MACRO_STRATEGIES:
            return MACRO_STRATEGIES[cond_key]
    for goal in goals:
        goal_key = goal.lower()
        if goal_key in MACRO_STRATEGIES:
            return MACRO_STRATEGIES[goal_key]
    return DEFAULT_MACROS

def calculate_macronutrients(calories, macro_split):
    """Calculate macronutrients in grams from calories"""
    protein_cal = calories * macro_split['protein']
    carbs_cal = calories * macro_split['carbs']
    fat_cal = calories * macro_split['fat']

    return {
        'protein_g': round(protein_cal / 4, 2),
        'carbs_g': round(carbs_cal / 4, 2),
        'fat_g': round(fat_cal / 9, 2)
    }

def get_age_from_dob(dob_str):
    """Calculate age from date of birth string"""
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d")
        return (datetime.today() - dob).days // 365
    except Exception:
        return None

def estimate_body_fat(sex):
    """Default body fat estimate if not provided"""
    return DEFAULT_BODY_FAT_MALE if sex.lower() == 'male' else DEFAULT_BODY_FAT_FEMALE

# ------------------ Main Processing Functions ------------------

def process_user_row(user_row, pref_row):
    """
    Process individual user row and preference row to calculate nutrition targets.
    Applies fallbacks where necessary.
    """
    try:
        # Extract basic user info
        user_id = user_row['id']
        sex = user_row['sex']
        weight = float(user_row['weight_kg'])
        height = float(user_row['height_cm'])
        activity_level = user_row['activity_level']
        exercise_freq = int(user_row['exercise_frequency_per_week'])

        # Get age from DOB or fallback
        dob = user_row.get('date_of_birth')
        if dob:
            age = get_age_from_dob(dob)
        else:
            age = int(user_row['age']) if 'age' in user_row else None

        if not (sex and weight and height and age):
            logger.warning(f"Skipping user {user_id}: Missing required fields.")
            return None

        # Health & goals
        health_conditions_raw = pref_row.get('health_conditions', '[]')
        goal_type_raw = pref_row.get('goal_type', '[]')

        try:
            health_conditions = ast.literal_eval(health_conditions_raw)
            if not isinstance(health_conditions, list):
                health_conditions = [str(health_conditions)]
        except Exception:
            health_conditions = [str(health_conditions_raw)]

        try:
            goals = ast.literal_eval(goal_type_raw)
            if not isinstance(goals, list):
                goals = [str(goals)]
        except Exception:
            goals = [str(goal_type_raw)]

        # Body fat estimate if missing
        body_fat_percent = user_row.get('body_fat_percent')
        if not body_fat_percent:
            body_fat_percent = estimate_body_fat(sex)  # Assumed default

        # Core calculations
        bmr = weighted_bmr(sex, weight, height, age, body_fat_percent)
        tdee = bmr * get_activity_multiplier(activity_level)
        optimal_calories = adjust_calories_for_goal(tdee, goals)
        macro_split = select_macro_split(health_conditions, goals)
        macros = calculate_macronutrients(optimal_calories, macro_split)
        ibw_kg = calculate_ibw(sex, height)

        return {
            'user_id': user_id,
            'optimal_calories': round(optimal_calories, 2),
            'protein_g': macros['protein_g'],
            'carbs_g': macros['carbs_g'],
            'fat_g': macros['fat_g'],
            'ibw_kg': ibw_kg,
            'health_conditions': health_conditions,
            'goals': goals,
            'motivation': pref_row.get('motivation', 'Unknown')
        }

    except Exception as e:
        logger.error(f"Error processing user {user_row.get('id', 'unknown')}: {e}")
        return None

def generate_nutrition_targets():
    """
    Main driver function to load user data, compute nutrition targets, and save output.
    """
    users_path = "data/users.csv"
    preferences_path = "data/user_preferences.csv"
    output_path = "data/user_nutrition_targets.csv"

    users_df = pd.read_csv(users_path)
    prefs_df = pd.read_csv(preferences_path)

    merged_df = pd.merge(users_df, prefs_df, left_on='id', right_on='user_id', how='inner')

    results = []
    for idx, row in merged_df.iterrows():
        result = process_user_row(row, row)
        if result:
            results.append(result)

    # output_df = pd.DataFrame(results)
    # output_df.to_csv(output_path, index=False)

    logger.info(f"✅ Saved nutrition targets for {len(results)} users to {output_path}")

# ------------------ Entrypoint ------------------

if __name__ == "__main__":
    generate_nutrition_targets()
