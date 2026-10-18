from typing import Optional, Dict
from app.config import settings


class GeminiAdvisor:
    """
    Optional Gemini integration for advisory second-opinions.
    Strictly constrained: never issues final business decisions and defaults to rule-based analysis.
    """

    @classmethod
    def analyze_second_opinion(cls, title: str, description: str, area: str) -> Optional[Dict]:
        if not settings.gemini_api_key:
            return None

        try:
            from google import genai

            client = genai.Client(api_key=settings.gemini_api_key)
            prompt = f"""
            You are an AI advisor supporting a Swisscom Human Risk Officer.
            Assess this potential risk context and suggest considerations.
            Title: {title}
            Description: {description}
            Area: {area}

            Rules:
            1. You are providing a non-binding opinion only.
            2. The human reviewer makes the binding decision.
            Keep response concise under 80 words.
            """
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return {
                "advisor_comment": response.text,
                "disclaimer": "Advisory recommendation generated via Gemini. Human officer maintains sole sign-off authority."
            }
        except Exception:
            return None
