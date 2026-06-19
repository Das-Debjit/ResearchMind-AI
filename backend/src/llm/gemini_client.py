# src/llm/gemini_client.py
# Gemini API client using the new google-genai package

from google import genai
from google.genai import types
from loguru import logger
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from backend folder explicitly
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Global client instance
_client = None


def get_gemini_client() -> genai.Client:

    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file!")

        _client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialized successfully!")

    return _client


def generate_response(
    prompt: str,
    model_name: str = "gemini-3.1-flash-lite",
    temperature: float = 0.3,
    max_tokens: int = 2048
) -> str:
 
    try:
        client = get_gemini_client()

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )

        result = response.text
        logger.info(f"Response generated: {len(result)} characters")
        return result

    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        raise


def get_gemini_model(model_name: str = "gemini-1.5-flash"):
 
    return get_gemini_client()