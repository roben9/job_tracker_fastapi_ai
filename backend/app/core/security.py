from datetime import timedelta, datetime, timezone
from pwdlib import PasswordHash
import jwt
from app.core.config import settings

password_hash = PasswordHash.recommended()  # this recommend will give the argon2

ALGORITHM = "HS256"


# this for hashing the password
def hash_password(password: str) -> str:
    return password_hash.hash(password)


# this for verify the password
def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


# subject says which user this token belongs to , so this will be the user ID
def create_token(subject: str, token_type: str, lifetime: timedelta):
    expire = datetime.now(timezone.utc) + lifetime
    payload = {"sub": subject, "type": token_type, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_access_token(subject: str) -> str:
    return create_token(
        subject, "access", timedelta(minutes=settings.access_token_expire_minutes)
    )


def create_refresh_token(subject: str) -> str:
    return create_token(
        subject, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )


def decode_token(token: str, expected_type: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=ALGORITHM)
    except jwt.InvalidTokenError:
        return None

    if payload.get("type") != expected_type:
        return None

    return payload.get("sub")
