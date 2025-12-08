import google.generativeai as genai
import os
from dotenv import load_dotenv
from django.core.cache import cache

load_dotenv() # Load environment variables from .env

def get_gemini_response(prompt, bot_config=None):
    try:
        # Use a cache key unique to the prompt & bot config
        cache_key = f"gemini_response::{prompt}::{getattr(bot_config, 'id', None) if bot_config else 'default'}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response

        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel('gemini-pro-latest')
        if bot_config and getattr(bot_config, 'prompt_template', None):
            full_prompt = f"{bot_config.prompt_template}\n\nUser: {prompt}"
        else:
            full_prompt = prompt
        response = model.generate_content(full_prompt)
        answer = response.text
        cache.set(cache_key, answer, timeout=60*5)  # Cache for 5 minutes
        return answer
    except Exception as e:
        print(f"Error getting Gemini response: {e}")
        return "I'm sorry, I'm having trouble connecting to Gemini right now."
