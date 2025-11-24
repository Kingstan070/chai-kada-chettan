import os
import logging

from flask import Flask, render_template, request

import config as settings
from utils.file_parser import extract_text, UnsupportedFileTypeError
from utils.summarize import summarize_resume
from utils.llm_api import get_roast_and_rating, LLMConfigError
from utils.snack_rating import get_snack
from utils.user_manager import increment_and_check


app = Flask(__name__)
app.config["SECRET_KEY"] = settings.FLASK_SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = settings.MAX_CONTENT_LENGTH_MB * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("chai_kada_chattan")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_resume():
    # Daily free trial check
    allowed, used, remaining = increment_and_check()
    if not allowed:
        return render_template(
            "limit.html",
            used=used,
            remaining=0,
            max_tries=settings.MAX_DAILY_TRIES,
            contact_email=settings.CONTACT_EMAIL,
        )

    file = request.files.get("resume")
    if file is None or file.filename == "":
        return render_template(
            "error.html",
            error_message="Oru file um select cheythilla. Please upload a resume.",
        ), 400

    try:
        # Parse text from resume
        text = extract_text(file)
        if not text.strip():
            return render_template(
                "error.html",
                error_message="Ithil oru readable text um kittiyilla. "
                "PDF locked aano / scanned image aano ennu nokko.",
            ), 400

        # Light heuristic summarization BEFORE sending to LLM
        summary = summarize_resume(text)

        # Get roast + numeric rating from LLM
        roast_text, rating = get_roast_and_rating(summary)

        # Map rating to Kerala snack!
        snack_emoji, snack_name, snack_description = get_snack(rating)

        # Trials left for info banner
        trials_left = remaining

        # NOTE: Jinja auto-escapes variables by default,
        # so roast_text is rendered safely (no |safe used).
        return render_template(
            "result.html",
            roast_text=roast_text,
            rating=rating,
            snack_emoji=snack_emoji,
            snack_name=snack_name,
            snack_description=snack_description,
            trials_left=trials_left,
        )

    except UnsupportedFileTypeError as e:
        logger.warning("Unsupported file type: %s", e)
        return render_template("error.html", error_message=str(e)), 400

    except LLMConfigError as e:
        logger.error("LLM configuration error: %s", e)
        return render_template(
            "error.html",
            error_message="Server configuration issue with AI model. "
            "Admin-ne vilicholyo?",
        ), 500

    except Exception as e:
        # Try to detect overload / quota style errors for nicer UX
        msg = str(e)
        logger.exception("Unhandled error while processing upload: %s", msg)
        overload_signals = [
            "429", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "quota"]
        api_overload = any(s.lower() in msg.lower() for s in overload_signals)
        return (
            render_template(
                "error.html",
                error_message=msg if not api_overload else None,
                api_overload=api_overload,
            ),
            500,
        )


# ---------- Health Check (for monitoring / uptime checks) ---------- #
@app.route("/health", methods=["GET"])
def health():
    """
    Lightweight health endpoint:
    - Returns 200 if Flask is up and API key is configured.
    - Does NOT call the model (fast & cheap).
    """
    status = "ok"
    message = "Service is running"

    if not settings.GEMINI_API_KEY:
        status = "degraded"
        message = "GEMINI_API_KEY missing"

    return {"status": status, "message": message}, 200 if status == "ok" else 500


# ---------- Global Error Handlers ---------- #
@app.errorhandler(413)
def request_entity_too_large(error):
    return (
        render_template(
            "error.html",
            error_message=f"File valiyaayipoyi! Max {settings.MAX_CONTENT_LENGTH_MB} MB mathram.",
        ),
        413,
    )


@app.errorhandler(404)
def page_not_found(error):
    return (
        render_template(
            "error.html",
            error_message="Page kandupidikkan pattiyilla. URL sheriyakko.",
        ),
        404,
    )


if __name__ == "__main__":
    # For local dev. In production, use gunicorn/uvicorn etc.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
