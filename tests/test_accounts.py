import json
import base64
import pytest
from pathlib import Path
import src.agent.accounts as accounts_mod

def create_mock_jwt(email: str) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').decode("utf-8").rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"email": email}).encode("utf-8")).decode("utf-8").rstrip("=")
    sig = "mock_signature"
    return f"{header}.{payload}.{sig}"

@pytest.fixture
def mock_gemini_vault(tmp_path, monkeypatch):
    vault = tmp_path / "accounts_vault"
    vault.mkdir(parents=True, exist_ok=True)
    creds = tmp_path / "oauth_creds.json"
    acc_json = tmp_path / "google_accounts.json"

    monkeypatch.setattr(accounts_mod, "VAULT_DIR", vault)
    monkeypatch.setattr(accounts_mod, "CREDS_FILE", creds)
    monkeypatch.setattr(accounts_mod, "ACCOUNTS_FILE", acc_json)
    monkeypatch.setattr(accounts_mod, "_sync_to_windows_keyring", lambda p: None)
    monkeypatch.setattr(accounts_mod, "_import_windows_keyring_to_vault", lambda: None)

    return {"vault": vault, "creds": creds, "accounts": acc_json}


def test_generate_google_auth_url():
    url = accounts_mod.generate_google_auth_url()
    assert "accounts.google.com" in url
    assert "client_id=" in url
    assert "response_type=code" in url


def test_extract_email_from_creds(tmp_path):
    id_token = create_mock_jwt("test_user@gmail.com")
    creds_file = tmp_path / "sample_creds.json"
    creds_file.write_text(json.dumps({
        "access_token": "ya29.xyz",
        "id_token": id_token,
    }), encoding="utf-8")

    extracted = accounts_mod.extract_email_from_creds(creds_file)
    assert extracted == "test_user@gmail.com"


def test_save_and_switch_accounts(mock_gemini_vault):
    id_tok_1 = create_mock_jwt("user1@gmail.com")
    id_tok_2 = create_mock_jwt("user2@gmail.com")

    # 1. Save user 1
    email_1 = accounts_mod.save_new_account_credentials({
        "access_token": "tok_1",
        "id_token": id_tok_1,
        "token_type": "Bearer"
    })
    assert email_1 == "user1@gmail.com"

    # 2. Save user 2
    email_2 = accounts_mod.save_new_account_credentials({
        "access_token": "tok_2",
        "id_token": id_tok_2,
        "token_type": "Bearer"
    })
    assert email_2 == "user2@gmail.com"

    # List accounts
    acc_data = accounts_mod.list_accounts()
    assert "user1@gmail.com" in acc_data["accounts"]
    assert "user2@gmail.com" in acc_data["accounts"]

    # 3. Switch account back to user 1
    switched = accounts_mod.switch_account("user1@gmail.com")
    assert switched is True
    active_now = accounts_mod.list_accounts()["active"]
    assert active_now == "user1@gmail.com"

    # 4. Remove user 2
    removed = accounts_mod.remove_account("user2@gmail.com")
    assert removed is True
    acc_after = accounts_mod.list_accounts()
    assert "user2@gmail.com" not in acc_after["accounts"]
