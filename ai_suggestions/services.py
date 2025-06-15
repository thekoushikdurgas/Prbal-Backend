"""
OpenRouter AI integration service for Prbal AI suggestions.
Handles communication with OpenRouter API for generating AI-powered service suggestions.
"""
import os
import json
import requests
import logging
from django.conf import settings
from typing import Dict, List, Any, Optional

logger = logging.getLogger('ai_suggestions')

class OpenRouterAIService:
    """
    Service for interacting with OpenRouter AI API.
    """
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = "openai/gpt-3.5-turbo"  # Default model
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers required for OpenRouter API requests.
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": settings.SITE_URL,  # Your site URL for attribution
            "X-Title": "Prbal Service Marketplace",  # Your app name for attribution
        }
    
    def generate_service_suggestions(self, 
                                    user_preferences: Dict[str, Any], 
                                    user_history: List[Dict[str, Any]],
                                    category_id: Optional[int] = None,
                                    max_suggestions: int = 5) -> List[Dict[str, Any]]:
        """
        Generate service suggestions based on user preferences and history.
        
        Args:
            user_preferences: User preferences data
            user_history: User's previous interactions
            category_id: Optional category to filter suggestions
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of service suggestions
        """
        try:
            # Construct the prompt for the AI
            prompt = self._construct_suggestion_prompt(
                user_preferences, 
                user_history,
                category_id,
                max_suggestions
            )
            
            # Call OpenRouter API
            response = self._call_openrouter_api(prompt)
            
            # Parse the response
            suggestions = self._parse_suggestions_response(response)
            
            # Limit to requested number
            return suggestions[:max_suggestions]
            
        except Exception as e:
            logger.error(f"Error generating service suggestions: {str(e)}")
            return []
    
    def _construct_suggestion_prompt(self, 
                                   user_preferences: Dict[str, Any], 
                                   user_history: List[Dict[str, Any]],
                                   category_id: Optional[int],
                                   max_suggestions: int) -> str:
        """
        Construct a prompt for the AI based on user data.
        """
        # Extract relevant information
        interests = user_preferences.get('interests', [])
        location = user_preferences.get('location', 'Unknown')
        budget = user_preferences.get('budget', 'Not specified')
        
        # Format history
        history_text = ""
        if user_history:
            history_text = "User's recent activity:\n"
            for item in user_history[:5]:  # Use only the 5 most recent activities
                if item.get('type') == 'view':
                    history_text += f"- Viewed service: {item.get('service_name')}\n"
                elif item.get('type') == 'booking':
                    history_text += f"- Booked service: {item.get('service_name')}\n"
                elif item.get('type') == 'search':
                    history_text += f"- Searched for: {item.get('query')}\n"
        
        # Construct the full prompt
        prompt = f"""You are an AI assistant for Prbal, a service marketplace. 
Your task is to suggest {max_suggestions} services that would interest this user.

User Information:
- Interests: {', '.join(interests)}
- Location: {location}
- Budget preference: {budget}

{history_text}

Please provide exactly {max_suggestions} service suggestions in JSON format.
Each suggestion should include:
1. A catchy title for the service
2. A brief description (max 100 words)
3. An estimated price range
4. Key benefits (list of 3 items)
5. Relevant tags (list of 3-5 keywords)

Response should be a valid JSON array of objects with the structure:
[
  {{
    "title": "Service Title",
    "description": "Brief description...",
    "price_range": "₹X - ₹Y",
    "benefits": ["Benefit 1", "Benefit 2", "Benefit 3"],
    "tags": ["tag1", "tag2", "tag3"]
  }}
]

Only respond with the JSON, no introduction or explanation text."""
        
        if category_id:
            prompt += f"\n\nPlease ensure all suggestions are within category ID: {category_id}."
            
        return prompt
    
    def _call_openrouter_api(self, prompt: str) -> Dict[str, Any]:
        """
        Call the OpenRouter API with the provided prompt.
        """
        endpoint = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": self.default_model,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant for a service marketplace."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        
        response = requests.post(
            endpoint,
            headers=self._get_headers(),
            json=payload,
            timeout=30  # 30 second timeout
        )
        
        if response.status_code != 200:
            logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
            raise Exception(f"API request failed with status code {response.status_code}")
            
        return response.json()
    
    def _parse_suggestions_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse the API response to extract service suggestions.
        """
        try:
            # Get the message content from the first choice
            content = response.get('choices', [{}])[0].get('message', {}).get('content', '{}')
            
            # Parse the JSON content
            suggestions = json.loads(content)
            
            # Validate the response format
            if not isinstance(suggestions, list):
                logger.warning("API response is not a list, returning empty suggestions")
                return []
                
            # Ensure all required fields are present
            validated_suggestions = []
            for suggestion in suggestions:
                if all(k in suggestion for k in ['title', 'description', 'price_range', 'benefits', 'tags']):
                    validated_suggestions.append(suggestion)
                else:
                    logger.warning(f"Skipping suggestion with missing fields: {suggestion}")
            
            return validated_suggestions
            
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON response from OpenRouter API")
            return []
        except Exception as e:
            logger.error(f"Error parsing suggestions response: {str(e)}")
            return []
