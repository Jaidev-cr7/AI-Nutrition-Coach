import google.generativeai as genai
import os
import json
import re
import hashlib
import logging
from datetime import datetime, timedelta
from django.core.cache import cache
from django.conf import settings
from ..models import AIAnalysisCache

logger = logging.getLogger(__name__)


class AINutritionService:
    def __init__(self):
        self.api_key = os.getenv("AI_API_KEY")
        self.model = None
        self.cache_timeout = 24 * 60 * 60  # 24 hours
        
        if self.api_key and self.api_key != "YOUR_GEMINI_API_KEY":
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-2.0-flash")
                logger.info("AI service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AI service: {e}")
                self.model = None
        else:
            logger.warning("AI_API_KEY not configured - using mock responses")

    def _generate_cache_key(self, meal_description: str) -> str:
        """Generate a consistent cache key for meal descriptions"""
        # Normalize the meal description (lowercase, remove extra spaces)
        normalized = re.sub(r'\s+', ' ', meal_description.strip().lower())
        return f"nutrition_analysis_{hashlib.md5(normalized.encode()).hexdigest()}"

    def _validate_and_clean_ai_response(self, response_text: str) -> dict:
        """
        Validate and clean the AI response to ensure it matches expected format
        """
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                logger.warning(f"No JSON found in AI response: {response_text[:200]}...")
                return self._get_fallback_response()
            
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Validate and clean each field
            cleaned_data = {
                'calories': self._clean_number_field(data.get('calories', 0), 0, 10000),
                'protein': self._clean_nutrient_field(data.get('protein', '0g')),
                'carbs': self._clean_nutrient_field(data.get('carbs', '0g')),
                'fat': self._clean_nutrient_field(data.get('fat', '0g')),
                'health_score': self._clean_number_field(data.get('health_score', 5), 1, 10),
                'advice': self._clean_advice_field(data.get('advice', 'No advice available'))
            }
            
            return cleaned_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from AI response: {e}")
            return self._get_fallback_response()
        except Exception as e:
            logger.error(f"Error processing AI response: {e}")
            return self._get_fallback_response()

    def _clean_number_field(self, value, min_val, max_val):
        """Clean and validate numeric fields"""
        try:
            if isinstance(value, str):
                # Extract numbers from strings like "300 calories"
                numbers = re.findall(r'\d+\.?\d*', str(value))
                if numbers:
                    num = float(numbers[0])
                else:
                    num = min_val
            else:
                num = float(value) if value is not None else min_val
            
            # Clamp to valid range
            return max(min_val, min(max_val, int(num)))
        except (ValueError, TypeError):
            return min_val

    def _clean_nutrient_field(self, value):
        """Clean nutrient fields to ensure proper format (number + unit)"""
        if not value:
            return "0g"
        
        # Extract numbers from the string
        numbers = re.findall(r'\d+\.?\d*', str(value))
        if numbers:
            num = float(numbers[0])
            return f"{num:.1f}g"
        return "0g"

    def _clean_advice_field(self, value):
        """Clean advice field to ensure it's a proper string"""
        if not value:
            return "No advice available"
        
        # Clean up the advice text
        advice = str(value).strip()
        # Remove excessive whitespace
        advice = re.sub(r'\s+', ' ', advice)
        # Limit length
        if len(advice) > 500:
            advice = advice[:497] + "..."
        
        return advice

    def _get_fallback_response(self):
        """Return a safe fallback response when AI fails"""
        return {
            'calories': 0,
            'protein': '0g',
            'carbs': '0g',
            'fat': '0g',
            'health_score': 5,
            'advice': 'Unable to analyze meal. Please try again later.'
        }

    def _get_mock_response(self, meal_description: str) -> dict:
        """Return a mock response for development when AI is not available"""
        # Simple mock logic based on keywords
        meal_lower = meal_description.lower()
        
        # Default values
        calories = 250
        protein = 15.0
        carbs = 30.0
        fat = 10.0
        health_score = 6
        
        # Adjust based on meal content
        if 'chicken' in meal_lower or 'meat' in meal_lower:
            calories += 100
            protein += 20
            health_score = 7
        elif 'salad' in meal_lower or 'vegetable' in meal_lower:
            calories -= 50
            carbs += 10
            health_score = 8
        elif 'rice' in meal_lower or 'pasta' in meal_lower:
            calories += 80
            carbs += 25
            health_score = 6
        elif 'egg' in meal_lower:
            calories += 70
            protein += 6
            health_score = 7
        elif 'banana' in meal_lower or 'fruit' in meal_lower:
            calories += 30
            carbs += 15
            health_score = 9
        elif 'oat' in meal_lower or 'oats' in meal_lower:
            calories += 60
            carbs += 20
            health_score = 8
        
        # Generate advice based on health score
        if health_score >= 8:
            advice = "Excellent choice! This meal is well-balanced and nutritious."
        elif health_score >= 6:
            advice = "Good meal option. Consider adding more vegetables for better nutrition."
        else:
            advice = "This meal could be improved. Try adding lean protein and reducing processed ingredients."
        
        return {
            'calories': calories,
            'protein': f"{protein:.1f}g",
            'carbs': f"{carbs:.1f}g",
            'fat': f"{fat:.1f}g",
            'health_score': health_score,
            'advice': advice
        }

    def _check_cache(self, meal_description: str) -> dict:
        """Check if we have a cached response for this meal"""
        cache_key = self._generate_cache_key(meal_description)
        
        # Check Django cache first (faster)
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit (Django cache) for: {meal_description[:50]}...")
            return cached_data
        
        # Check database cache (persistent)
        try:
            cache_entry = AIAnalysisCache.objects.get(
                meal_description__iexact=meal_description.strip(),
                expires_at__gt=datetime.now()
            )
            logger.info(f"Cache hit (DB) for: {meal_description[:50]}...")
            
            # Store in Django cache for faster future access
            cache.set(cache_key, cache_entry.analysis_data, self.cache_timeout)
            return cache_entry.analysis_data
            
        except AIAnalysisCache.DoesNotExist:
            return None

    def _store_in_cache(self, meal_description: str, analysis_data: dict):
        """Store the analysis result in both cache layers"""
        cache_key = self._generate_cache_key(meal_description)
        expires_at = datetime.now() + timedelta(seconds=self.cache_timeout)
        
        # Store in Django cache
        cache.set(cache_key, analysis_data, self.cache_timeout)
        
        # Store in database cache
        try:
            AIAnalysisCache.objects.update_or_create(
                meal_description=meal_description.strip(),
                defaults={
                    'analysis_data': analysis_data,
                    'expires_at': expires_at
                }
            )
        except Exception as e:
            logger.error(f"Failed to store in database cache: {e}")

    def get_nutrition_advice(self, meal_description: str) -> dict:
        """
        Get nutrition advice for a meal description with caching and validation
        """
        if not meal_description or not meal_description.strip():
            return self._get_fallback_response()
        
        # Check cache first
        cached_result = self._check_cache(meal_description)
        if cached_result:
            return cached_result
        
        # If AI model is not available, return mock response
        if not self.model:
            mock_response = self._get_mock_response(meal_description)
            self._store_in_cache(meal_description, mock_response)
            return mock_response
        
        try:
            # Generate prompt for AI
            prompt = f"""
            You are a professional AI nutritionist.
            Analyze this meal: {meal_description}

            Return:
            - Calories (estimate)
            - Protein / Carbs / Fat macros
            - Health score (1–10)
            - Improvements
            - Short diet advice

            Format as clean JSON:
            {{
              "calories": number,
              "protein": "value + unit",
              "carbs": "value + unit", 
              "fat": "value + unit",
              "health_score": number,
              "advice": "string"
            }}
            """

            # Call AI API
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Validate and clean the response
            cleaned_data = self._validate_and_clean_ai_response(response_text)
            
            # Store in cache
            self._store_in_cache(meal_description, cleaned_data)
            
            logger.info(f"Generated new analysis for: {meal_description[:50]}...")
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error calling AI API: {e}")
            return self._get_fallback_response()

    def clear_expired_cache(self):
        """Clean up expired cache entries"""
        try:
            deleted_count = AIAnalysisCache.objects.filter(
                expires_at__lt=datetime.now()
            ).delete()[0]
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired cache entries")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired cache: {e}")


# Singleton instance
ai_service = AINutritionService()
