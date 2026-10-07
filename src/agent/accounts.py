import os
import json
import base64
import shutil
import logging
import platform
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

GEMINI_DIR = Path.home() / ".gemini"
VAULT_DIR = GEMINI_DIR / "accounts_vault"
CREDS_FILE = GEMINI_DIR / "oauth_creds.json"
ACCOUNTS_FILE = GEMINI_DIR / "google_accounts.json"

def _sync_to_windows_keyring(creds_path: Path):
    """Synchronizes active credentials to Windows Credential Manager (gemini:antigravity)."""
    if platform.system().lower() != "windows":
        return
    try:
        import ctypes
        from ctypes import wintypes
        class CREDENTIAL(ctypes.Structure):
            _fields_ = [
                ('Flags', wintypes.DWORD),
                ('Type', wintypes.DWORD),
                ('TargetName', wintypes.LPWSTR),
                ('Comment', wintypes.LPWSTR),
                ('LastWritten', wintypes.FILETIME),
                ('CredentialBlobSize', wintypes.DWORD),
                ('CredentialBlob', ctypes.c_char_p),
                ('Persist', wintypes.DWORD),
                ('AttributeCount', wintypes.DWORD),
                ('Attributes', ctypes.c_void_p),
                ('TargetAlias', wintypes.LPWSTR),
                ('UserName', wintypes.LPWSTR),
            ]
        with open(creds_path, "r", encoding="utf-8") as f:
            cdata = json.load(f)
        keyring_data = {
            "token": {
                "access_token": cdata.get("access_token"),
                "token_type": cdata.get("token_type", "Bearer"),
                "refresh_token": cdata.get("refresh_token"),
                "expiry": "2030-01-01T00:00:00Z"
            },
            "auth_method": "oauth",
            "id_token": cdata.get("id_token")
        }
        blob = json.dumps(keyring_data).encode("utf-8")
        cred = CREDENTIAL()
        cred.Type = 1  # CRED_TYPE_GENERIC
        cred.TargetName = "gemini:antigravity"
        cred.UserName = "antigravity"
        cred.CredentialBlobSize = len(blob)
        cred.CredentialBlob = blob
        cred.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE
        cred.AttributeCount = 0
        cred.Attributes = None
        ctypes.windll.advapi32.CredWriteW(ctypes.byref(cred), 0)
        logger.info("Synchronized active account to Windows Credential Manager (gemini:antigravity)")
    except Exception as e:
        logger.debug(f"Failed to sync Windows keyring: {e}")

def _import_windows_keyring_to_vault():
    """Reads credentials from Windows Credential Manager and caches into vault."""
    if platform.system().lower() != "windows":
        return
    try:
        import ctypes
        from ctypes import wintypes
        class CREDENTIAL(ctypes.Structure):
            _fields_ = [
                ('Flags', wintypes.DWORD),
                ('Type', wintypes.DWORD),
                ('TargetName', wintypes.LPWSTR),
                ('Comment', wintypes.LPWSTR),
                ('LastWritten', wintypes.FILETIME),
                ('CredentialBlobSize', wintypes.DWORD),
                ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
                ('Persist', wintypes.DWORD),
                ('AttributeCount', wintypes.DWORD),
                ('Attributes', ctypes.c_void_p),
                ('TargetAlias', wintypes.LPWSTR),
                ('UserName', wintypes.LPWSTR),
            ]
        advapi32 = ctypes.windll.advapi32
        CredReadW = advapi32.CredReadW
        CredReadW.argtypes = [wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
        CredReadW.restype = wintypes.BOOL

        pcred = ctypes.POINTER(CREDENTIAL)()
        if CredReadW('gemini:antigravity', 1, 0, ctypes.byref(pcred)):
            blob = bytes(pcred.contents.CredentialBlob[:pcred.contents.CredentialBlobSize])
            data = json.loads(blob.decode('utf-8'))
            t = data.get('token', {})
            id_t = data.get('id_token')
            if id_t and isinstance(t, dict):
                import tempfile
                tmp_p = Path(tempfile.gettempdir()) / "tmp_id.json"
                tmp_p.write_text(json.dumps({"id_token": id_t}))
                email = extract_email_from_creds(tmp_p)
                tmp_p.unlink(missing_ok=True)
                if email:
                    target_file = VAULT_DIR / f"{email}.json"
                    if not target_file.exists():
                        creds = {
                            'access_token': t.get('access_token'),
                            'refresh_token': t.get('refresh_token'),
                            'id_token': id_t,
                            'token_type': t.get('token_type', 'Bearer'),
                            'scope': 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email openid https://www.googleapis.com/auth/cloud-platform',
                        }
                        with open(target_file, 'w', encoding='utf-8') as f:
                            json.dump(creds, f, indent=2)
                        logger.info(f"Imported account {email} from Windows Credential Manager to vault")
    except Exception as e:
        logger.debug(f"Could not import Windows keyring to vault: {e}")

from ..config import settings

def get_google_client_id() -> str:
    return os.getenv("GOOGLE_CLIENT_ID") or getattr(settings, "google_client_id", "")

def get_google_client_secret() -> str:
    return os.getenv("GOOGLE_CLIENT_SECRET") or getattr(settings, "google_client_secret", "")

# Module-level aliases
GOOGLE_CLIENT_ID = get_google_client_id()
GOOGLE_CLIENT_SECRET = get_google_client_secret()
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
    "https://www.googleapis.com/auth/cloud-platform"
]
DEFAULT_REDIRECT_URI = "http://localhost:8085/auth/callback"

def generate_google_auth_url(redirect_uri: str = DEFAULT_REDIRECT_URI) -> str:
    """Generates a direct Google OAuth 2.0 authorization URL."""
    import urllib.parse
    client_id = get_google_client_id() or GOOGLE_CLIENT_ID
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "select_account consent",
    }
    return "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(params)

async def exchange_code_for_tokens(code_or_url: str, redirect_uri: str = DEFAULT_REDIRECT_URI) -> Optional[Dict[str, Any]]:
    """Exchanges an authorization code or redirect URL with Google for tokens."""
    import urllib.parse
    import httpx
    
    code = code_or_url.strip()
    # Extract code if full URL was pasted
    if "code=" in code:
        parsed = urllib.parse.urlparse(code)
        qs = urllib.parse.parse_qs(parsed.query)
        if "code" in qs:
            code = qs["code"][0]
        elif "#" in code:
            frag_qs = urllib.parse.parse_qs(parsed.fragment)
            if "code" in frag_qs:
                code = frag_qs["code"][0]

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": get_google_client_id() or GOOGLE_CLIENT_ID,
                    "client_secret": get_google_client_secret() or GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                }
            )
            if resp.status_code != 200:
                logger.error(f"Google token exchange failed ({resp.status_code}): {resp.text}")
                return None
            return resp.json()
    except Exception as e:
        logger.error(f"Exception during Google token exchange: {e}")
        return None

def save_new_account_credentials(token_data: Dict[str, Any]) -> Optional[str]:
    """Saves new credentials returned by Google into vault and sets as active."""
    _ensure_vault_dir()
    import time
    creds = {
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "id_token": token_data.get("id_token"),
        "token_type": token_data.get("token_type", "Bearer"),
        "scope": token_data.get("scope", " ".join(GOOGLE_SCOPES)),
    }
    if "expires_in" in token_data:
        creds["expiry_date"] = int(time.time() * 1000) + int(token_data["expires_in"]) * 1000

    tmp_path = VAULT_DIR / "temp_extracted.json"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(creds, f, indent=2)
        email = extract_email_from_creds(tmp_path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

    if not email:
        logger.error("Could not extract email from id_token")
        return None

    # Save to vault
    target_vault = VAULT_DIR / f"{email}.json"
    with open(target_vault, "w", encoding="utf-8") as f:
        json.dump(creds, f, indent=2)

    # Set as active oauth_creds.json
    with open(CREDS_FILE, "w", encoding="utf-8") as f:
        json.dump(creds, f, indent=2)

    _sync_to_windows_keyring(target_vault)
    _update_google_accounts_json(active_email=email)
    logger.info(f"Successfully saved and activated new account: {email}")
    return email

def _ensure_vault_dir():
    try:
        VAULT_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create accounts_vault directory: {e}")

def extract_email_from_creds(file_path: Path) -> Optional[str]:
    """Extracts email address from id_token in an oauth_creds.json file."""
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        id_token = data.get("id_token")
        if not id_token or "." not in id_token:
            return None
        parts = id_token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64).decode("utf-8", errors="replace")
        payload = json.loads(payload_json)
        return payload.get("email")
    except Exception as e:
        logger.debug(f"Failed to extract email from {file_path}: {e}")
        return None

def sync_current_account_to_vault() -> Optional[str]:
    """Saves active oauth_creds.json into accounts_vault/<email>.json."""
    _ensure_vault_dir()
    if not CREDS_FILE.exists():
        return None
    
    email = extract_email_from_creds(CREDS_FILE)
    if not email:
        # Fallback to google_accounts.json active field
        if ACCOUNTS_FILE.exists():
            try:
                with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                    email = json.load(f).get("active")
            except Exception:
                pass
                
    if email:
        target_path = VAULT_DIR / f"{email}.json"
        try:
            shutil.copy2(CREDS_FILE, target_path)
            # Update google_accounts.json if needed
            _update_google_accounts_json(active_email=email)
            return email
        except Exception as e:
            logger.error(f"Failed to copy credentials to vault: {e}")
    return None

def _update_google_accounts_json(active_email: str):
    """Keeps ~/.gemini/google_accounts.json in sync."""
    old_accounts = []
    if ACCOUNTS_FILE.exists():
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                old_accounts = data.get("old", [])
        except Exception:
            pass

    if active_email in old_accounts:
        old_accounts.remove(active_email)
    
    # Collect all vault accounts
    if VAULT_DIR.exists():
        for f in VAULT_DIR.glob("*.json"):
            acc_name = f.stem
            if acc_name != active_email and acc_name not in old_accounts:
                old_accounts.append(acc_name)

    try:
        with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"active": active_email, "old": old_accounts}, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not update google_accounts.json: {e}")

def list_accounts() -> Dict[str, Any]:
    """Returns the currently active account and all saved accounts in the vault."""
    _ensure_vault_dir()
    _import_windows_keyring_to_vault()
    active_email = sync_current_account_to_vault()
    
    accounts = []
    if VAULT_DIR.exists():
        for f in VAULT_DIR.glob("*.json"):
            accounts.append(f.stem)

    # Also check if google_accounts.json mentions any other accounts
    if ACCOUNTS_FILE.exists():
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                act = data.get("active")
                if act and act not in accounts and (VAULT_DIR / f"{act}.json").exists():
                    accounts.append(act)
                for o in data.get("old", []):
                    if o not in accounts and (VAULT_DIR / f"{o}.json").exists():
                        accounts.append(o)
        except Exception:
            pass

    # Ensure unique list
    unique_accounts = list(dict.fromkeys(accounts))
    
    return {
        "active": active_email,
        "accounts": unique_accounts
    }

def switch_account(target_email: str) -> bool:
    """Switches active oauth_creds.json to the selected account from the vault."""
    _ensure_vault_dir()
    sync_current_account_to_vault()
    
    target_creds = VAULT_DIR / f"{target_email}.json"
    if not target_creds.exists():
        logger.warning(f"Vault credentials not found for {target_email}")
        return False

    try:
        shutil.copy2(target_creds, CREDS_FILE)
        _sync_to_windows_keyring(target_creds)
        _update_google_accounts_json(active_email=target_email)
        logger.info(f"Successfully switched active Google account to {target_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to switch account to {target_email}: {e}")
        return False

def remove_account(target_email: str) -> bool:
    """Removes an account from the vault."""
    _ensure_vault_dir()
    target_creds = VAULT_DIR / f"{target_email}.json"
    removed = False
    if target_creds.exists():
        try:
            target_creds.unlink()
            removed = True
        except Exception as e:
            logger.error(f"Failed to delete {target_creds}: {e}")

    if ACCOUNTS_FILE.exists():
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            old_list = data.get("old", [])
            if target_email in old_list:
                old_list.remove(target_email)
            if data.get("active") == target_email:
                data["active"] = None
            data["old"] = old_list
            with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            removed = True
        except Exception:
            pass

    return removed
