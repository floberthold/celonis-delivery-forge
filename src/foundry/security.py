from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from foundry.settings import get_settings

BCRYPT_PASSWORD_MAX_BYTES = 72


def validate_password_length(password: str) -> None:
    password_bytes = len(password.encode("utf-8"))
    if password_bytes > BCRYPT_PASSWORD_MAX_BYTES:
        raise ValueError(
            f"Password must be {BCRYPT_PASSWORD_MAX_BYTES} bytes or fewer (UTF-8)."
        )


def hash_password(password: str) -> str:
    validate_password_length(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(subject: str, organization_id: str | None = None) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expires_at}
    if organization_id:
        payload["org_id"] = organization_id
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_action_token(
    *,
    subject: str,
    purpose: str,
    expires_minutes: int,
    extra_claims: dict[str, str] | None = None,
) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload: dict[str, str | datetime] = {
        "sub": subject,
        "purpose": purpose,
        "exp": expires_at,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_action_token(*, token: str, expected_purpose: str) -> dict[str, str]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

    purpose = payload.get("purpose")
    if purpose != expected_purpose:
        raise ValueError("Invalid token purpose")
    return {str(key): str(value) for key, value in payload.items()}
