import hmac
import hashlib
import json
import urllib.parse
import time
import logging
from typing import Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# Maximum age of initData in seconds (24 hours)
INIT_DATA_MAX_AGE_SECONDS = 86400

# Trusted reverse proxy IPs (socket-level only — cannot be spoofed from the internet).
# Only the actual TCP client IP (request.client.host) is checked, never X-Forwarded-For.
def get_trusted_proxy_ips() -> frozenset:
    trusted = {"127.0.0.1", "::1"}
    if settings.trusted_proxies:
        for ip in settings.trusted_proxies.split(","):
            cleaned = ip.strip()
            if cleaned:
                trusted.add(cleaned)
    return frozenset(trusted)


def validate_telegram_init_data(init_data: str, bot_token: str, admin_id: int) -> bool:
    """
    Validates Telegram WebApp initData string using HMAC-SHA256 signature,
    checks user ID matches admin, and verifies auth_date freshness (anti-replay).
    """
    if not init_data or not bot_token:
        return False

    # Fail-closed: if admin_id is not configured, deny all access
    if admin_id <= 0:
        logger.error("SECURITY: telegram_admin_id is not configured (<=0). Denying all TMA access (fail-closed).")
        return False

    try:
        init_data_clean = urllib.parse.unquote(init_data) if "%" in init_data else init_data
        parsed_data = dict(urllib.parse.parse_qsl(init_data_clean, keep_blank_values=True))

        if "hash" not in parsed_data:
            parsed_data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))

        if "hash" not in parsed_data:
            return False

        received_hash = parsed_data.pop("hash")

        # Construct data-check-string (sorted key=value joined by \n)
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = "\n".join(data_check_arr)

        # Secret key = HMAC-SHA256(key="WebAppData", data=bot_token)
        secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()

        # Calculated hash = HMAC-SHA256(key=secret_key, data=data_check_string)
        calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            return False

        # Validate auth_date freshness (anti-replay protection)
        auth_date_str = parsed_data.get("auth_date")
        if auth_date_str:
            try:
                auth_date = int(auth_date_str)
                age = int(time.time()) - auth_date
                if age > INIT_DATA_MAX_AGE_SECONDS:
                    logger.warning(
                        f"SECURITY: initData expired — auth_date is {age}s old "
                        f"(limit: {INIT_DATA_MAX_AGE_SECONDS}s). Possible replay attack."
                    )
                    return False
            except (ValueError, TypeError):
                logger.warning("SECURITY: auth_date is not a valid integer in initData.")
                return False
        else:
            logger.warning("SECURITY: auth_date missing from initData. Denying.")
            return False

        # Validate user ID
        user_raw = parsed_data.get("user")
        if not user_raw:
            return False

        user_data = json.loads(user_raw)
        user_id = int(user_data.get("id", 0))

        if user_id != admin_id:
            logger.warning(f"Unauthorized TMA access attempt from Telegram user_id={user_id}, expected={admin_id}")
            return False

        logger.info(f"Authorized TMA access confirmed for user_id={user_id}")
        return True
    except Exception as e:
        logger.error(f"Error validating Telegram initData: {e}")
        return False


async def verify_admin_access(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Ensures the request is authorized. Security layers (in order):
    1. Trusted reverse proxy (socket-level IP only — NOT spoofable headers).
    2. Valid Telegram Mini App initData (cryptographic HMAC-SHA256 + auth_date freshness).
    3. Bearer token matching the bot token (constant-time comparison).

    SECURITY NOTE: X-Forwarded-For and X-Real-IP headers are deliberately NEVER read.
    Only request.client.host (TCP socket-level IP) is used for proxy trust,
    which cannot be spoofed without physical access to the local network.
    """
    admin_id = settings.telegram_admin_id

    # Fail-closed: if admin is not configured, block everything
    if admin_id <= 0:
        logger.error("SECURITY: telegram_admin_id not configured. Blocking all API access (fail-closed).")
        raise HTTPException(
            status_code=503,
            detail="⛔ Сервер не настроен: TELEGRAM_ADMIN_ID не задан. Доступ заблокирован."
        )

    client_ip = request.client.host if request.client else "unknown"

    # 1. Trust requests from known reverse proxy (socket-level IP, not spoofable)
    if client_ip in get_trusted_proxy_ips():
        return True

    # 2. Check X-Telegram-Init-Data header or query param
    init_data = (
        request.headers.get("X-Telegram-Init-Data")
        or request.headers.get("x-telegram-init-data")
        or request.query_params.get("tg_init_data")
        or request.query_params.get("tgWebAppData")
    )

    if init_data:
        token = settings.telegram_bot_token
        if validate_telegram_init_data(init_data, token, admin_id):
            return True

    # 3. Check Bearer token (only bot_token accepted, constant-time comparison)
    if auth and auth.credentials:
        if hmac.compare_digest(auth.credentials, settings.telegram_bot_token):
            return True

    logger.warning(
        f"Unauthorized access to {request.url.path} from client_ip={client_ip}"
    )

    raise HTTPException(
        status_code=403,
        detail="⛔ Доступ запрещён. Требуется авторизация администратора через Telegram Mini App."
    )
