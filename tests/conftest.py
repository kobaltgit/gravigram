import os
import sys
import time
import json
import hmac
import hashlib
import urllib.parse
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from src.config import settings
import src.database as db_module
from src.server.app import app
from src.server.auth import verify_admin_access

def make_valid_init_data(bot_token: str, admin_id: int, auth_date: int = None) -> str:
    """Helper to generate cryptographically signed Telegram initData."""
    if auth_date is None:
        auth_date = int(time.time())
    user_json = json.dumps({"id": admin_id, "first_name": "Admin", "username": "adminuser"})
    params = {
        "auth_date": str(auth_date),
        "query_id": "AAHdF6IQAAAAAN0XohD9w7uK",
        "user": user_json,
    }
    data_check_arr = [f"{k}={v}" for k, v in sorted(params.items())]
    data_check_string = "\n".join(data_check_arr)

    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    hash_val = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    params["hash"] = hash_val
    return urllib.parse.urlencode(params)


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path, monkeypatch):
    """
    Ensures every test runs against a clean, isolated SQLite database
    in a temporary directory, avoiding interference with production data.
    """
    test_db_path = tmp_path / "test_gravigram.db"
    monkeypatch.setattr(db_module, "DB_FILE", test_db_path)
    await db_module.init_db()
    yield test_db_path
    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except Exception:
            pass


@pytest.fixture
def valid_auth_headers():
    init_data = make_valid_init_data(settings.telegram_bot_token, settings.telegram_admin_id)
    return {"X-Telegram-Init-Data": init_data}


@pytest.fixture
def bearer_auth_headers():
    return {"Authorization": f"Bearer {settings.telegram_bot_token}"}


@pytest.fixture
def client(valid_auth_headers):
    """FastAPI TestClient pre-configured with valid Telegram Mini App auth headers."""
    return TestClient(app, headers=valid_auth_headers)


@pytest.fixture
def unauth_client():
    """FastAPI TestClient with NO auth headers to test 403 Forbidden enforcement."""
    return TestClient(app)
