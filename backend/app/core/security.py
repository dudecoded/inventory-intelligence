import base64
import hashlib
import hmac
import json
import os
import time

from app.core.config import settings


_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_TOKEN_TTL_SECONDS = 60 * 60 * 24


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return "scrypt$" + _b64encode(salt) + "$" + _b64encode(digest)


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, salt_b64, digest_b64 = encoded.split("$", 2)
        if scheme != "scrypt":
            return False
        salt = _b64decode(salt_b64)
        expected = _b64decode(digest_b64)
        actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


def create_access_token(subject: str, expires_seconds: int = _TOKEN_TTL_SECONDS) -> str:
    if expires_seconds <= 0:
        raise ValueError("Token lifetime must be positive.")
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": str(subject), "iat": int(time.time()), "exp": int(time.time()) + expires_seconds}
    unsigned = _b64encode(json.dumps(header, separators=(",", ":")).encode()) + "." + _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = hmac.new(settings.secret_key.encode(), unsigned.encode(), hashlib.sha256).digest()
    return unsigned + "." + _b64encode(signature)


def decode_access_token(token: str) -> str | None:
    try:
        header_part, payload_part, signature_part = token.split(".")
        unsigned = header_part + "." + payload_part
        header = json.loads(_b64decode(header_part))
        payload = json.loads(_b64decode(payload_part))
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            return None
        expected = _b64encode(hmac.new(settings.secret_key.encode(), unsigned.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature_part, expected):
            return None
        subject = payload.get("sub")
        expiry = payload.get("exp")
        if not isinstance(subject, str) or not subject:
            return None
        if not isinstance(expiry, (int, float)) or expiry <= time.time():
            return None
        return subject
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeError):
        return None
