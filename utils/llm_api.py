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
You are a Malayalam 'Chai Kada Chattan' – a funny tea shop uncle who speaks in Manglish.
Your style is sarcastic, spicy, funny but still helpful. You roast resumes like a local tea shop legend,
but you also give real advice for improvement.

🔥 ROAST & FEEDBACK FORMAT (VERY IMPORTANT):
1. 7–12 sentences of spicy, sarcastic Manglish roast.
2. Then give **detailed resume improvement advice** (4–6 sentences).
3. BE CREATIVE – use local chai kada style sarcasm.
4. END the reply with EXACTLY one line:
   RATING=<number>     ← example: RATING=7

⚠ DO NOT reveal personal data like email, phone, address.

📌 WRITE MORE TOKENS (TARGET: 300–350 words).
📌 Do NOT write “ROAST:” / “ADVICE:” / “RATING:” headings — just speak normally.
📌 Output must feel like a real chai kada chettan talking directly to the person.

🧠 Example slang words you can use (OPTIONAL):
"entha ithu", "mone", "ayiio", "okke nalla try",
"azhaku illa", "porotta polum stiff", "poda makale", "pani undu".

📝 Resume Summary to roast:
{summary}

--------
ONLY output what the chettan says.
NO extra text before or after.
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
    """
    Extract rating from model output.
    Supports patterns like:
    - RATING: 7
    - RATING = 7
    - Rating: 7
    - rating=7
    """
    match = re.search(r"rating\s*[:=]\s*(\d+)", text, re.IGNORECASE)
    if not match:
        # fallback: last number between 1 and 10 in the text
        nums = re.findall(r"\b([1-9]|10)\b", text)
        if nums:
            rating = int(nums[-1])
        else:
            return 5  # neutral fallback
    else:
        rating = int(match.group(1))

    return max(1, min(10, rating))


def get_roast_and_rating(summary: str) -> Tuple[str, int]:
    client = get_client()
    model = settings.GEMINI_MODEL

    prompt = build_roast_prompt(summary)
    safe_prompt, _ = ensure_prompt_within_limit(client, model, prompt)

    response = client.models.generate_content(
        model=model,
        contents=safe_prompt,
        generation_config={
            "max_output_tokens": 800,  # default is usually lower
            "temperature": 0.9,        # more creativity
            "top_p": 0.9,              # wider sampling
        }
    )

    raw_text = _extract_text_from_response(
        response).strip() or "No roast generated."

    # 1️⃣ Parse rating BEFORE trimming
    rating = parse_rating(raw_text)

    # 2️⃣ Drop the last non-empty line (where rating lives)
    lines = raw_text.splitlines()
    # remove trailing empty lines first
    while lines and not lines[-1].strip():
        lines.pop()

    if lines:
        lines = lines[:-1]  # drop last line

    cleaned_roast = "\n".join(lines).strip()

    return cleaned_roast, rating
