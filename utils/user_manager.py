import datetime as dt
import json
import os
from typing import Tuple

from flask import request

import config as settings

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "user_data.json")


def _ensure_db_dir():
    os.makedirs(DB_DIR, exist_ok=True)


def _load_data() -> dict:
    _ensure_db_dir()
    if not os.path.exists(DB_PATH):
        return {}
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_data(data: dict) -> None:
    _ensure_db_dir()
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _today_str() -> str:
    # Keep it naive; daily reset by server local time
    return dt.date.today().isoformat()


def _get_client_id() -> str:
    # For simple demo: use IP address
    ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not ip:
        ip = request.remote_addr or "unknown"
    return ip


def increment_and_check(max_tries: int = None) -> Tuple[bool, int, int]:
    """
    Increment today's usage for this user and check if allowed.
    Returns: (allowed, used, remaining)
    """
    if max_tries is None:
        max_tries = settings.MAX_DAILY_TRIES

    user_id = _get_client_id()
    today = _today_str()
    data = _load_data()

    user = data.get(user_id, {"date": today, "used": 0})
    if user.get("date") != today:
        # New day, reset count
        user = {"date": today, "used": 0}

    if user["used"] >= max_tries:
        data[user_id] = user
        _save_data(data)
        return False, user["used"], 0

    user["used"] += 1
    data[user_id] = user
    _save_data(data)

    remaining = max_tries - user["used"]
    return True, user["used"], remaining
