import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Safety & limits
MAX_DAILY_TRIES = int(os.getenv("MAX_DAILY_TRIES", "5"))
MAX_CONTENT_LENGTH_MB = int(os.getenv("MAX_CONTENT_LENGTH_MB", "5"))

# UI / Contact
CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "tallwinkingstan@gmail.com")

# Flask secret key
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", os.urandom(24))
