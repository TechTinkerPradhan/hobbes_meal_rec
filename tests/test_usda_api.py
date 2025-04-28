import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.usda_api import USDAApiClient

class TestUSDAApiClient(unittest.TestCase):
    """Test case for the USDAApiClient module."""
    
    def setUp(self):
        """Set up test environment."""
        # Initialize the API client
        self.api_client = USDAApiClient()
        
        # Define sample response data for mocking
        self.sample_search_response = {
            'foods': [
                {
                    'fdcId': 123456,
                    'description': 'Chicken, breast, meat only, cooked, roasted',
                    'dataType': 'SR Legacy',
                    'foodNutrients': [
                        {
                            'nutrientId': 1003,
                            'nutrientName': 'Protein',
                            'value': 31.02,
                            'unitName': 'g'
                        },
                        {
                            'nutrientId': 1004,
                            'nutrientName': 'Total lipid (fat)',
                            'value': 3.57,
                            'unitName': 'g'
                        }
                    ]
                }
            ]
        }
        
        self.sample_food_details = {
            'fdcId': 123456,
            'description': 'Chicken, breast, meat only, cooked, roasted',
            'foodNutrients': [
                {
                    'nutrient': {
                        'id': 1003,
                        'name': 'Protein',
                        'unitName': 'g'
                    },
                    'amount': 31.02
                },
                {
                    'nutrient': {
                        'id': 1004,
                        'name': 'Total lipid (fat)',
                        'unitName': 'g'
                    },
                    'amount': 3.57
                },
                {
                    'nutrient': {
                        'id': 1005,
                        'name': 'Carbohydrate, by difference',
                        'unitName': 'g'
                    },
                    'amount': 0.0
                }
            ]
        }
    
    @patch('requests.get')
    def test_search_food(self, mock_get):
        """Test food search functionality."""
        # Set up the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_search_response
        mock_get.return_value = mock_response
        
        # Call the search function
        results = self.api_client.search_food('chicken breast')
        
        # Check that the results are correct
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['fdcId'], 123456)
        
        # Check that the API was called correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn('api.nal.usda.gov', args[0])
        self.assertIn('api_key', kwargs['params'])
        self.assertIn('query', kwargs['params'])
        self.assertEqual(kwargs['params']['query'], 'chicken breast')
    
    @patch('requests.get')
    def test_search_food_error(self, mock_get):
        """Test handling of search errors."""
        # Set up the mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
        mock_get.return_value = mock_response
        
        # Call the search function
        results = self.api_client.search_food('invalid query')
        
        # Check that an empty list is returned on error
        self.assertEqual(results, [])
    
    @patch('requests.get')
    def test_get_food_details(self, mock_get):
        """Test food details retrieval."""
        # Set up the mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_food_details
        mock_get.return_value = mock_response
        
        # Call the get_food_details function
        details = self.api_client.get_food_details('123456')
        
        # Check that the details are correct
        self.assertEqual(details['fdcId'], 123456)
        self.assertEqual(len(details['foodNutrients']), 3)
        
        # Check that the API was called correctly
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertIn('123456', args[0])
        self.assertIn('api_key', kwargs['params'])
    
    @patch('requests.get')
    def test_get_food_details_error(self, mock_get):
        """Test handling of food details errors."""
        # Set up the mock response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Not Found'
        mock_get.return_value = mock_response
        
        # Call the get_food_details function
        details = self.api_client.get_food_details('999999')
        
        # Check that None is returned on error
        self.assertIsNone(details)
    
    def test_extract_nutrients(self):
        """Test nutrient extraction from food details."""
        # Call the extract_nutrients function
        nutrients = self.api_client.extract_nutrients(self.sample_food_details)
        
        # Check that nutrients are extracted correctly
        self.assertIn('Protein', nutrients)
        self.assertIn('Total Fat', nutrients)
        self.assertIn('Carbohydrates', nutrients)
        
        self.assertEqual(nutrients['Protein']['value'], 31.02)
        self.assertEqual(nutrients['Protein']['unit'], 'g')
        
        self.assertEqual(nutrients['Total Fat']['value'], 3.57)
        self.assertEqual(nutrients['Total Fat']['unit'], 'g')
        
        self.assertEqual(nutrients['Carbohydrates']['value'], 0.0)
        self.assertEqual(nutrients['Carbohydrates']['unit'], 'g')
    
    def test_extract_nutrients_empty(self):
        """Test nutrient extraction with empty data."""
        # Call with empty data
        nutrients = self.api_client.extract_nutrients({})
        
        # Check that an empty dict is returned
        self.assertEqual(nutrients, {})
    
    @patch.object(USDAApiClient, 'search_food')
    @patch.object(USDAApiClient, 'get_food_details')
    def test_get_nutrition_info(self, mock_get_details, mock_search):
        """Test the get_nutrition_info function."""
        # Set up the mocks
        mock_search.return_value = [{'fdcId': 123456}]
        mock_get_details.return_value = self.sample_food_details
        
        # Call the get_nutrition_info function
        nutrition_info = self.api_client.get_nutrition_info('chicken breast')
        
        # Check that the info is formatted correctly
        self.assertEqual(len(nutrition_info), 3)  # We have 3 nutrients in the sample data
        
        # Check the first nutrient
        first_nutrient = nutrition_info[0]
        self.assertIn('Nutrient', first_nutrient)
        self.assertIn('Value', first_nutrient)
        self.assertIn('Unit', first_nutrient)
        
        # Verify the search and details calls
        mock_search.assert_called_once_with('chicken breast')
        mock_get_details.assert_called_once_with(123456)
    
    @patch.object(USDAApiClient, 'search_food')
    def test_get_nutrition_info_no_results(self, mock_search):
        """Test get_nutrition_info with no search results."""
        # Set up the mock to return empty results
        mock_search.return_value = []
        
        # Call the get_nutrition_info function
        nutrition_info = self.api_client.get_nutrition_info('nonexistent food')
        
        # Check that an empty list is returned
        self.assertEqual(nutrition_info, [])

if __name__ == '__main__':
    unittest.main()
