import time
import json
import urllib.parse
import hmac
import hashlib
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from src.server.auth import validate_telegram_init_data, verify_admin_access
from src.config import settings

def make_init_data(token: str, user_id: int, auth_date: int = None, tamper_hash: bool = False) -> str:
    if auth_date is None:
        auth_date = int(time.time())
    user_json = json.dumps({"id": user_id, "first_name": "Test", "username": "testuser"})
    params = {
        "auth_date": str(auth_date),
        "query_id": "AAHdF6IQAAAAAN0XohD9w7uK",
        "user": user_json,
    }
    data_check_arr = [f"{k}={v}" for k, v in sorted(params.items())]
    data_check_string = "\n".join(data_check_arr)

    secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
    hash_val = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if tamper_hash:
        hash_val = "bad" + hash_val[3:]

    params["hash"] = hash_val
    return urllib.parse.urlencode(params)


def test_valid_auth():
    token = settings.telegram_bot_token or "dummy:bot_token"
    admin_id = settings.telegram_admin_id or 123456789
    valid_data = make_init_data(token, admin_id)
    assert validate_telegram_init_data(valid_data, token, admin_id) is True

def test_invalid_user_rejected():
    token = settings.telegram_bot_token or "dummy:bot_token"
    admin_id = settings.telegram_admin_id or 123456789
    attacker_data = make_init_data(token, 999999999)
    assert validate_telegram_init_data(attacker_data, token, admin_id) is False

def test_tampered_signature_rejected():
    token = settings.telegram_bot_token or "dummy:bot_token"
    admin_id = settings.telegram_admin_id or 123456789
    tampered_data = make_init_data(token, admin_id, tamper_hash=True)
    assert validate_telegram_init_data(tampered_data, token, admin_id) is False

def test_expired_auth_date_rejected():
    token = settings.telegram_bot_token or "dummy:bot_token"
    admin_id = settings.telegram_admin_id or 123456789
    # Expired 2 days ago
    expired_date = int(time.time()) - 172800
    expired_data = make_init_data(token, admin_id, auth_date=expired_date)
    assert validate_telegram_init_data(expired_data, token, admin_id) is False

def test_missing_hash_rejected():
    token = settings.telegram_bot_token or "dummy:bot_token"
    admin_id = settings.telegram_admin_id or 123456789
    assert validate_telegram_init_data("auth_date=123&user={}", token, admin_id) is False
    assert validate_telegram_init_data("", token, admin_id) is False

def test_fail_closed_when_admin_id_unset():
    token = settings.telegram_bot_token or "dummy:bot_token"
    valid_data = make_init_data(token, 12345)
    # If admin_id is 0 or negative, must return False
    assert validate_telegram_init_data(valid_data, token, 0) is False
    assert validate_telegram_init_data(valid_data, token, -1) is False

def test_verify_admin_access_dependency():
    test_app = FastAPI()

    @test_app.get("/protected", dependencies=[Depends(verify_admin_access)])
    def protected_route():
        return {"status": "ok"}

    token = settings.telegram_bot_token
    admin_id = settings.telegram_admin_id

    client = TestClient(test_app)

    # 1. No auth -> 403 Forbidden
    resp = client.get("/protected")
    assert resp.status_code == 403

    # 2. Valid TMA initData in header -> 200 OK
    valid_data = make_init_data(token, admin_id)
    resp = client.get("/protected", headers={"X-Telegram-Init-Data": valid_data})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    # 3. Bearer token matching bot token -> 200 OK
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    # 4. Invalid Bearer token -> 403 Forbidden
    resp = client.get("/protected", headers={"Authorization": "Bearer wrong_token"})
    assert resp.status_code == 403
