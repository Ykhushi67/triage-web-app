"""
PatientTriage.ai - Token Authentication & Role-Based Access Control.
Zero external crypto dependencies (uses Python standard library hmac, hashlib, base64, json).
Fully compatible with standard Bearer JWT tokens.
"""

import hmac
import hashlib
import base64
import json
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db

bearer_scheme = HTTPBearer(auto_error=False)


# ─────────────────────────────────────────────
# Password Hashing (PBKDF2-HMAC-SHA256)
# ─────────────────────────────────────────────
SALT = b"patient_triage_ai_clinical_salt_2026"

def hash_password(password: str) -> str:
    """Hashes password using PBKDF2-HMAC-SHA256."""
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), SALT, 100000)
    return key.hex()

def verify_password(plain: str, hashed: str) -> bool:
    """Verifies a plain password against the stored PBKDF2 hash."""
    return hmac.compare_digest(hash_password(plain), hashed)


# ─────────────────────────────────────────────
# JWT Token Generator (HMAC-SHA256 base64url)
# ─────────────────────────────────────────────
def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

def _b64url_decode(s: str) -> bytes:
    pad = 4 - (len(s) % 4)
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    expire_ts = time.time() + (expires_delta.total_seconds() if expires_delta else (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60))
    payload["exp"] = expire_ts

    header_b64 = _b64url_encode(json.dumps(header).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(payload).encode("utf-8"))
    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

    sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)

    return f"{header_b64}.{payload_b64}.{sig_b64}"

def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Malformed token")
        header_b64, payload_b64, sig_b64 = parts

        # Verify signature
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected_sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        provided_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, provided_sig):
            raise ValueError("Signature mismatch")

        payload = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        if "exp" in payload and payload["exp"] < time.time():
            raise ValueError("Token expired")
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    from backend.app.models import Staff

    # For seamless prototype testing and swagger exploration: if no bearer token provided, fallback to default doctor
    if credentials is None:
        default_user = db.query(Staff).filter(Staff.role == "DOCTOR").first()
        if default_user:
            return default_user
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    payload = decode_access_token(credentials.credentials)
    staff_id: str = payload.get("sub")
    if not staff_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.query(Staff).filter(Staff.staff_id == staff_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_roles(*allowed_roles: str):
    """Dependency factory: restrict endpoint to specific clinical roles."""
    def _check(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to roles: {list(allowed_roles)}"
            )
        return current_user
    return _check
