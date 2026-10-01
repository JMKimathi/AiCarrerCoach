"""Password hashing and signed bearer tokens using Python's standard library."""

import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import User, get_db

_bearer = HTTPBearer(auto_error=False)
_PASSWORD_ROUNDS = 310_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PASSWORD_ROUNDS)
    return f"pbkdf2_sha256${_PASSWORD_ROUNDS}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    # Upgrade prototype plaintext credentials on the next successful sign-in.
    if not encoded.startswith("pbkdf2_sha256$"):
        return hmac.compare_digest(password.encode(), encoded.encode())
    try:
        algorithm, rounds, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), _unb64(salt), int(rounds))
        return hmac.compare_digest(actual, _unb64(expected))
    except (ValueError, TypeError):
        return False


def is_password_hashed(encoded: str) -> bool:
    return encoded.startswith("pbkdf2_sha256$")


def create_access_token(user: User) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user.user_id,
        "role": user.role,
        "iat": now,
        "exp": now + int(timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES).total_seconds()),
    }
    unsigned = f"{_json_b64(header)}.{_json_b64(payload)}"
    signature = hmac.new(settings.SECRET_KEY.encode(), unsigned.encode(), hashlib.sha256).digest()
    return f"{unsigned}.{_b64(signature)}"


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _json_b64(value: dict) -> str:
    return _b64(json.dumps(value, separators=(",", ":")).encode())


def _decode_token(token: str) -> dict:
    try:
        header_part, payload_part, signature_part = token.split(".")
        unsigned = f"{header_part}.{payload_part}"
        expected = hmac.new(settings.SECRET_KEY.encode(), unsigned.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _unb64(signature_part)):
            raise ValueError("Invalid signature")
        header = json.loads(_unb64(header_part))
        payload = json.loads(_unb64(payload_part))
        if header.get("alg") != "HS256" or int(payload.get("exp", 0)) <= int(time.time()):
            raise ValueError("Expired or invalid token")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token", headers={"WWW-Authenticate": "Bearer"}) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    payload = _decode_token(credentials.credentials)
    user = db.query(User).filter(User.user_id == payload.get("sub"), User.is_active.is_(True)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Account is unavailable", headers={"WWW-Authenticate": "Bearer"})
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user
