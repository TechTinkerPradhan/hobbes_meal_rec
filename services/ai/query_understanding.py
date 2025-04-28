# services/ai/query_understanding.py

def classify_user_query(query: str) -> str:
    """
    Classify user queries into allowed categories.

    Returns:
        - "meal_recommendation"
        - "meal_logging"
        - "nutrition_info"
        - "plan_adjustment"
        - "unknown"
    """
    if not isinstance(query, str) or len(query.strip()) == 0:
        return "unknown"

    query_lower = query.lower()

    if any(keyword in query_lower for keyword in ["recommend", "suggest", "what should i eat", "meal idea", "suggest meal"]):
        return "meal_recommendation"
    elif any(keyword in query_lower for keyword in ["i ate", "log my meal", "record what i ate"]):
        return "meal_logging"
    elif any(keyword in query_lower for keyword in ["nutrient", "calorie", "protein", "macro", "nutrition info"]):
        return "nutrition_info"
    elif any(keyword in query_lower for keyword in ["change my plan", "adjust my diet", "modify my meal plan"]):
        return "plan_adjustment"
    else:
        return "unknown"
