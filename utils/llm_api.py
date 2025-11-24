import re
from typing import Tuple

from google import genai

import config as settings
from .token_manager import ensure_prompt_within_limit


_client = None


class LLMConfigError(Exception):
    pass


def get_client():
    global _client
    if _client is None:
        if not settings.GEMINI_API_KEY:
            raise LLMConfigError(
                "GEMINI_API_KEY is not set. Check your .env file.")
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def build_roast_prompt(summary: str) -> str:
    return f"""
You are a Malayalam 'Chai Kada Chattan' (local tea shop uncle).
Speak in Manglish (Malayalam + English).
Your job: roast the resume lightly, but also give helpful feedback.

RULES:
- Tone: funny, sarcastic, but not rude.
- Use local slang and chai kada style comments.
- Point out strengths and weaknesses.
- Mention what to improve: structure, skills, projects, clarity, etc.
- DO NOT reveal any personal info (phone, email, address) even if present.

Output format (STRICT):
ROAST: <your roast text in Manglish, 5–10 sentences>

RATING: <number from 1 to 10 only, no extra text>

Here is the resume summary:

{summary}
""".strip()


def _extract_text_from_response(response) -> str:
    # google-genai response usually has .text
    if hasattr(response, "text") and response.text:
        return response.text

    # Fallback if using candidates
    try:
        if response.candidates:
            parts = response.candidates[0].content.parts
            texts = [getattr(p, "text", "")
                     for p in parts if getattr(p, "text", "")]
            return "\n".join(texts)
    except Exception:
        pass

    return ""


def parse_rating(text: str) -> int:
    match = re.search(r"RATING:\s*(\d+)", text, re.IGNORECASE)
    if not match:
        return 5  # neutral fallback
    rating = int(match.group(1))
    rating = max(1, min(10, rating))
    return rating


def get_roast_and_rating(summary: str) -> Tuple[str, int]:
    client = get_client()
    model = settings.GEMINI_MODEL

    prompt = build_roast_prompt(summary)
    safe_prompt, _ = ensure_prompt_within_limit(client, model, prompt)

    response = client.models.generate_content(
        model=model,
        contents=safe_prompt,
    )
    text = _extract_text_from_response(
        response).strip() or "No roast generated."

    rating = parse_rating(text)
    return text, rating
