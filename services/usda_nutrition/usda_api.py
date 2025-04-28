import requests
import json
import pandas as pd
import os
import logging
from time import sleep
from typing import Dict, List, Any, Optional

class USDAApiClient:
    """
    Client for interacting with the USDA FoodData Central API to retrieve
    nutritional information for food items.
    """
    
    def __init__(self):
        """Initialize the USDA API client with API key and base URL."""
        self.api_key = os.getenv("USDA_API_KEY", "DEMO_KEY")
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        self.logger = logging.getLogger(__name__)
        
        # Cache to avoid repeated API calls
        self.cache = {}
    
    def search_food(self, query: str, page_size: int = 5) -> List[Dict[str, Any]]:
        """
        Search for food items in the USDA database.
        
        Args:
            query (str): Food item to search for
            page_size (int): Number of results to return
            
        Returns:
            List[Dict]: List of food items matching the query
        """
        try:
            # Check cache first
            cache_key = f"search_{query}_{page_size}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Construct the API endpoint
            endpoint = f"{self.base_url}/foods/search"
            
            # Set up parameters
            params = {
                "api_key": self.api_key,
                "query": query,
                "pageSize": page_size,
                "dataType": ["Foundation", "SR Legacy", "Survey (FNDDS)"]
            }
            
            # Make the request
            response = requests.get(endpoint, params=params)
            
            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                foods = data.get('foods', [])
                
                # Cache the result
                self.cache[cache_key] = foods
                
                return foods
            else:
                self.logger.error(f"Error searching for food: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error in search_food: {str(e)}")
            return []
    
    def get_food_details(self, fdc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed nutritional information for a specific food item.
        
        Args:
            fdc_id (str): FDC ID of the food item
            
        Returns:
            Dict: Detailed nutritional information
        """
        try:
            # Check cache first
            cache_key = f"details_{fdc_id}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Construct the API endpoint
            endpoint = f"{self.base_url}/food/{fdc_id}"
            
            # Set up parameters
            params = {
                "api_key": self.api_key
            }
            
            # Make the request
            response = requests.get(endpoint, params=params)
            
            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()
                
                # Cache the result
                self.cache[cache_key] = data
                
                return data
            else:
                self.logger.error(f"Error getting food details: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error in get_food_details: {str(e)}")
            return None
    
    def extract_nutrients(self, food_details: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract key nutrients from food details.
        
        Args:
            food_details (Dict): Detailed food information
            
        Returns:
            Dict: Extracted nutrients
        """
        nutrients = {}
        
        try:
            if not food_details or 'foodNutrients' not in food_details:
                return nutrients
            
            # Map of nutrient IDs to names (common nutrients)
            nutrient_map = {
                1003: 'Protein',
                1004: 'Total Fat',
                1005: 'Carbohydrates',
                1008: 'Energy (kcal)',
                1018: 'Alcohol',
                1051: 'Water',
                1079: 'Fiber',
                1087: 'Calcium',
                1089: 'Iron',
                1090: 'Magnesium',
                1092: 'Potassium',
                1093: 'Sodium',
                1095: 'Zinc',
                1106: 'Vitamin A',
                1114: 'Vitamin D',
                1162: 'Vitamin C',
                1165: 'Vitamin E',
                1166: 'Vitamin K',
                1175: 'Vitamin B6',
                1177: 'Vitamin B12',
                1178: 'Vitamin B1 (Thiamin)',
                1180: 'Vitamin B2 (Riboflavin)',
                1185: 'Vitamin B3 (Niacin)',
                1186: 'Vitamin B9 (Folate)',
                1258: 'Saturated Fat',
                1292: 'Monounsaturated Fat',
                1293: 'Polyunsaturated Fat',
                2000: 'Sugars'
            }
            
            # Extract nutrients
            for nutrient in food_details['foodNutrients']:
                if 'nutrient' in nutrient and 'id' in nutrient['nutrient']:
                    nutrient_id = nutrient['nutrient']['id']
                    
                    if nutrient_id in nutrient_map:
                        nutrient_name = nutrient_map[nutrient_id]
                        nutrient_value = nutrient.get('amount', 0)
                        nutrient_unit = nutrient.get('nutrient', {}).get('unitName', '')
                        
                        nutrients[nutrient_name] = {
                            'value': nutrient_value,
                            'unit': nutrient_unit
                        }
            
            return nutrients
            
        except Exception as e:
            self.logger.error(f"Error extracting nutrients: {str(e)}")
            return nutrients
    
    def get_nutrition_info(self, food_name: str) -> List[Dict[str, Any]]:
        """
        Get nutritional information for a food item by name.
        
        Args:
            food_name (str): Name of the food item
            
        Returns:
            List[Dict]: Nutritional information
        """
        try:
            # Check cache first
            cache_key = f"nutrition_{food_name}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # Search for the food
            search_results = self.search_food(food_name)
            
            if not search_results:
                return []
            
            # Get the first result (most relevant)
            food_id = search_results[0]['fdcId']
            
            # Get detailed information
            food_details = self.get_food_details(food_id)
            
            if not food_details:
                return []
            
            # Extract nutrients
            nutrients = self.extract_nutrients(food_details)
            
            # Format for display
            nutrition_info = []
            for nutrient_name, nutrient_data in nutrients.items():
                nutrition_info.append({
                    'Nutrient': nutrient_name,
                    'Value': nutrient_data['value'],
                    'Unit': nutrient_data['unit']
                })
            
            # Cache the result
            self.cache[cache_key] = nutrition_info
            
            return nutrition_info
            
        except Exception as e:
            self.logger.error(f"Error getting nutrition info: {str(e)}")
            return []
