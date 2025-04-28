# services/ai/guardrails_manager.py

import re
import logging
from typing import Dict, Any

class GuardrailsManager:
    """
    GuardrailsManager for validating and sanitizing
    user inputs, LLM prompts, and LLM outputs in Hobbes Meal Recommendation System.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Patterns to sanitize sensitive information
        self.sensitive_patterns = [
            r'(?:credit\s*card|card\s*number)\s*\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}',
            r'(?:ssn|social\s*security)\s*\d{3}[\s-]?\d{2}[\s-]?\d{4}',
            r'(?:password|passwd|pwd)[\s:]*\S{8,}',
            r'(?:api[\s\-_]*key|secret[\s\-_]*key|access[\s\-_]*token)[\s:]*[\w\-]{10,}'
        ]


        # Expected meal structure keywords
        self.expected_output_fields = ["Meal Name:", "Ingredients:", "Macros", "Short Rationale:"]

    def sanitize_text(self, text: str) -> str:
        """Redact sensitive information from text."""
        if not isinstance(text, str):
            return ""
        sanitized = text
        for pattern in self.sensitive_patterns:
            sanitized = re.sub(pattern, '[REDACTED]', sanitized, flags=re.IGNORECASE)
        return sanitized

    def validate_user_query(self, query: str) -> str:
        """Sanitize and validate user query before passing to LLM."""
        sanitized_query = self.sanitize_text(query)
        if len(sanitized_query.strip()) < 5:
            return "Invalid or empty query."
        return sanitized_query

    def validate_llm_response_structure(self, response: str) -> bool:
        """Check if LLM output contains necessary fields."""
        if not isinstance(response, str):
            return False
        for keyword in self.expected_output_fields:
            if keyword not in response:
                return False
        return True

    def strict_parse_macros(self, macros_text: str) -> Dict[str, float]:
        """
        Strictly parse the 'Macros' line.
        Expected format: Calories, Protein g, Carbs g, Fats g
        """
        try:
            nums = re.findall(r"[-+]?\d*\.\d+|\d+", macros_text)
            if len(nums) >= 4:
                return {
                    "calories": float(nums[0]),
                    "protein_g": float(nums[1]),
                    "carbs_g": float(nums[2]),
                    "fats_g": float(nums[3])
                }
            else:
                # fallback
                return {
                    "calories": 500.0,
                    "protein_g": 30.0,
                    "carbs_g": 40.0,
                    "fats_g": 20.0
                }
        except Exception as e:
            self.logger.error(f"Error parsing macros: {e}")
            return {
                "calories": 500.0,
                "protein_g": 30.0,
                "carbs_g": 40.0,
                "fats_g": 20.0
            }

    def sanitize_and_validate_output(self, raw_response: str) -> Dict[str, Any]:
        """
        Full guardrailed validation of LLM output.
        Parses and returns clean fields.
        """
        clean_response = self.sanitize_text(raw_response)

        if not self.validate_llm_response_structure(clean_response):
            self.logger.warning("Invalid meal response structure. Skipping.")
            return {}

        try:
            lines = clean_response.splitlines()
            parsed = {
                "meal_name": "",
                "ingredients": "",
                "calories": 0.0,
                "protein_g": 0.0,
                "carbs_g": 0.0,
                "fats_g": 0.0,
                "rationale": ""
            }
            for line in lines:
                line_lower = line.lower()
                if "meal name" in line_lower:
                    parsed["meal_name"] = line.split(":", 1)[1].strip()
                elif "ingredients" in line_lower:
                    parsed["ingredients"] = line.split(":", 1)[1].strip()
                elif "macros" in line_lower:
                    macros = self.strict_parse_macros(line)
                    parsed.update(macros)
                elif "short rationale" in line_lower:
                    parsed["rationale"] = line.split(":", 1)[1].strip()

            return parsed

        except Exception as e:
            self.logger.error(f"Error parsing LLM output: {e}")
            return {}

